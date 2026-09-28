#!/usr/bin/env python3
"""Build a synthetic narration track for a sample cut, straight from its plan.

The tool reads two parts of a sample plan (for example
episodes/01-how-machines-see/sample-90s-plan.md):

- "## The cut": the table that gives every shot its slot, e.g. "| S1 | 0:00–0:11 | 11 s | ...".
- "## Narration": one line per shot. Times in parentheses are silences. The marker that
  opens a shot is the wait before the voice; a marker inside a line is a pause.
  Example: "> **S1.** *(1 s)* Look at this small square. *(pause, 1.5 s)* A curve."

For each text segment it asks the chosen engine for speech, trims the silence at both
ends, levels the clip to a common loudness, and places it at its shot start plus the
lead-in, with the marked pauses in between. It then loudness-matches the whole track, writes WAV and M4A files, transcribes
every clip to check that the spoken words match the text, and writes a timing report.

Engines, all served by fal (the key comes only from the FAL_KEY environment variable):
  elevenlabs  ElevenLabs Multilingual v2   fal-ai/elevenlabs/tts/multilingual-v2
  gemini      Gemini 3.8 Flash TTS         google/gemini-3.8-flash-tts
  minimax     MiniMax Speech 2.8 HD        fal-ai/minimax/speech-2.8-hd
The word check transcribes every clip with ElevenLabs Scribe v2 (fal-ai/elevenlabs/speech-to-text/scribe-v2);
skip it with --no-word-check.

Config example (one take):
  --engine elevenlabs --voice George --speed 1.0

Usage:
  export FAL_KEY=...   # your fal key
  python3 tools/narrate.py \\
      --plan episodes/01-how-machines-see/sample-90s-plan.md \\
      --engine elevenlabs --voice George \\
      --out episodes/01-how-machines-see/sample/audio/narration/elevenlabs-george

Outputs in --out: clips/ (one WAV per segment, cached by a hash of its request),
timeline.wav and timeline.m4a (the full length of the cut), segments.json, and timing.md.
Requires ffmpeg on PATH.
"""

import argparse
import array
import base64
import datetime
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

RATE = 48000
TAIL = 0.25  # seconds the voice should end before the cut
CLIP_LEVEL = -20.0  # LUFS; every clip is leveled here first, so separate requests don't jump in level

# Spoken forms go to the TTS engine only. The plan and the script keep the written form.
SPOKEN_FORMS = {"196": "a hundred and ninety-six"}

NARRATOR_STYLE = (
    "A warm, calm narrator for an animated science explainer. Curious and kind, as if "
    "showing a friend something interesting on a table. Unhurried, with clear pauses at "
    "the ends of sentences. Plain and natural: no announcer voice, no drama, no sing-song."
)

ENGINES = {
    "elevenlabs": ("ElevenLabs Multilingual v2 via fal", "fal-ai/elevenlabs/tts/multilingual-v2"),
    "gemini": ("Gemini 3.8 Flash TTS via fal", "google/gemini-3.8-flash-tts"),
    "minimax": ("MiniMax Speech 2.8 HD via fal", "fal-ai/minimax/speech-2.8-hd"),
}
ASR = "fal-ai/elevenlabs/speech-to-text/scribe-v2"

MARKER = re.compile(r"\*\(([^)]*)\)\*")
SECONDS = re.compile(r"(\d+(?:\.\d+)?) s\b")
SLOT = re.compile(r"^\| (S\d+) \| (\d+):(\d\d)–(\d+):(\d\d) \| \d+ s \|", re.M)
LINE = re.compile(r"^> \*\*(S\d+)\.\*\* (.+)$", re.M)


def fail(msg):
    sys.exit(f"narrate: {msg}")


def section(text, title):
    m = re.search(rf"^## {re.escape(title)}\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not m:
        fail(f"the plan has no '## {title}' section")
    return m.group(1)


def parse_plan(path):
    """Return the narrated shots (slots plus ordered text and pause items) and the cut's length."""
    text = Path(path).read_text()
    slots = {m[0]: (int(m[1]) * 60 + int(m[2]), int(m[3]) * 60 + int(m[4]))
             for m in SLOT.findall(section(text, "The cut"))}
    shots = []
    for sid, body in LINE.findall(section(text, "Narration")):
        if sid not in slots:
            fail(f"{sid} has narration but no slot in the cut table")
        items = []
        for i, part in enumerate(MARKER.split(body)):
            if i % 2:
                sec = SECONDS.search(part)
                if not sec:
                    fail(f"{sid}: the marker '({part})' needs a time in seconds, e.g. '(pause, 1.5 s)'")
                items.append(("pause", float(sec.group(1))))
            elif part.strip():
                items.append(("text", part.strip()))
        if not items or items[0][0] != "pause":
            fail(f"{sid}: the line must open with a lead-in marker such as *(0.5 s)*")
        shots.append({"id": sid, "start": slots[sid][0], "end": slots[sid][1], "items": items})
    if not shots:
        fail("found no narration lines ('> **S1.** ...') in the plan")
    return shots, max(end for _, end in slots.values())


def spoken(text):
    for written, said in SPOKEN_FORMS.items():
        text = re.sub(rf"\b{re.escape(written)}\b", said, text)
    return text


def need_env(name):
    value = os.environ.get(name, "")
    if not value:
        fail(f"{name} is not set; export it before running")
    return value


def fetch(req, timeout=300, tries=3):
    for attempt in range(1, tries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            body = e.read()[:600].decode(errors="replace")
            if e.code in (429, 500, 502, 503, 504) and attempt < tries:
                time.sleep(5 * attempt)
                continue
            fail(f"HTTP {e.code} from {req.full_url}: {body}")
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < tries:
                time.sleep(5 * attempt)
                continue
            fail(f"request to {req.full_url} failed: {e}")


def post_json(url, payload, headers):
    data = json.dumps(payload).encode()
    return fetch(urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **headers}))


def fal(endpoint, payload):
    return json.loads(post_json(f"https://fal.run/{endpoint}", payload, {"Authorization": f"Key {need_env('FAL_KEY')}"}))


def fal_audio(endpoint, payload):
    out = fal(endpoint, payload)
    url = (out.get("audio") or {}).get("url")
    if not url:
        fail(f"{endpoint} returned no audio: {str(out)[:300]}")
    return fetch(urllib.request.Request(url))


def synthesize(args, text, prev_text, next_text):
    endpoint = ENGINES[args.engine][1]
    if args.engine == "elevenlabs":
        return fal_audio(endpoint, {
            "text": text, "voice": args.voice, "speed": args.speed, "stability": args.stability,
            "similarity_boost": args.similarity, "style": args.style_exaggeration,
            "previous_text": prev_text, "next_text": next_text,
        })
    if args.engine == "gemini":
        return fal_audio(endpoint, {"prompt": text, "voice": args.voice, "style_instructions": args.style,
                                    "turns": None, "speakers": None})
    return fal_audio(endpoint, {
        "prompt": text, "output_format": "url", "language_boost": "English",
        "voice_setting": {"voice_id": args.voice, "speed": args.speed, "english_normalization": True},
        "audio_setting": {"format": "mp3", "sample_rate": 44100, "bitrate": 256000, "channel": 1},
    })


def run(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode:
        fail(f"{' '.join(cmd[:3])} ... failed:\n{proc.stderr[-800:]}")
    return proc


def to_clip(raw, dest):
    """Decode engine audio to 48 kHz mono 16-bit WAV with the silence at both ends trimmed."""
    trim = "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.02"
    chain = f"{trim},afade=t=in:d=0.005,areverse,{trim},afade=t=in:d=0.01,areverse"
    with tempfile.NamedTemporaryFile(suffix=".audio") as tmp:
        tmp.write(raw)
        tmp.flush()
        run(["ffmpeg", "-v", "error", "-y", "-i", tmp.name, "-af", chain,
             "-ar", str(RATE), "-ac", "1", "-c:a", "pcm_s16le", str(dest)])


def read_samples(path):
    with wave.open(str(path)) as w:
        if w.getframerate() != RATE or w.getnchannels() != 1 or w.getsampwidth() != 2:
            fail(f"{path} is not 48 kHz mono 16-bit")
        samples = array.array("h", w.readframes(w.getnframes()))
    if sys.byteorder == "big":
        samples.byteswap()
    return samples


def write_wav(path, samples):
    out = array.array("h", samples)
    if sys.byteorder == "big":
        out.byteswap()
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(out.tobytes())


def mix_in(track, samples, t0):
    off = round(t0 * RATE)
    if off + len(samples) > len(track):
        track.extend(array.array("h", bytes(2 * (off + len(samples) - len(track)))))
    for i, s in enumerate(samples):
        v = track[off + i] + s
        track[off + i] = 32767 if v > 32767 else -32768 if v < -32768 else v


def loudness(path):
    """Integrated loudness of a file in LUFS (EBU R128)."""
    probe = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128", "-f", "null", "-"],
                           capture_output=True, text=True)
    found = re.findall(r"I:\s+(-?\d+(?:\.\d+)?) LUFS", probe.stderr)
    if not found:
        fail(f"could not measure the loudness of {path}:\n{probe.stderr[-400:]}")
    return float(found[-1])


def leveled(samples, lufs):
    gain = 10 ** ((CLIP_LEVEL - lufs) / 20)
    return array.array("h", (max(-32768, min(32767, round(v * gain))) for v in samples))


def normalize(src, dst, target):
    """Linear gain to the loudness target, then a lookahead peak limiter at -1.5 dBFS.

    loudnorm is not used: TTS peaks are high for its loudness, so loudnorm's linear mode
    falls back to dynamic mode, which rides the gain and makes the first seconds louder.
    """
    gain = target - loudness(src)
    limit = 10 ** (-1.5 / 20)
    run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af",
         f"volume={gain:.2f}dB,alimiter=limit={limit:.4f}:attack=5:release=50:level=false:latency=true",
         "-ar", str(RATE), "-ac", "1", "-c:a", "pcm_s16le", str(dst)])
    return {"gain_db": round(gain, 2), "output_lufs": loudness(dst)}


def transcribe(path):
    uri = "data:audio/wav;base64," + base64.b64encode(Path(path).read_bytes()).decode()
    out = fal(ASR, {"audio_url": uri, "language_code": "en", "diarize": False, "tag_audio_events": False})
    if "text" not in out:
        fail(f"{ASR} returned no text: {str(out)[:300]}")
    return out["text"]


def words(text):
    return re.findall(r"[a-z0-9']+", text.lower().replace("’", "'").replace("-", " "))


def word_check(expected, heard):
    """Compare the spoken form with the transcript; return (ratio, differences)."""
    a, b = words(expected), words(spoken(heard))
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    diffs = [f"{tag}: '{' '.join(a[i1:i2])}' → '{' '.join(b[j1:j2])}'"
             for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != "equal"]
    return round(sm.ratio(), 3), diffs


def clock(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


def settings(args):
    if args.engine == "elevenlabs":
        return {"speed": args.speed, "stability": args.stability, "similarity_boost": args.similarity,
                "style": args.style_exaggeration}
    if args.engine == "minimax":
        return {"speed": args.speed, "english_normalization": True}
    return {"style_instructions": args.style}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--plan", required=True, help="sample plan with '## The cut' and '## Narration'")
    ap.add_argument("--engine", required=True, choices=sorted(ENGINES))
    ap.add_argument("--voice", required=True, help="engine voice, e.g. George (elevenlabs), Charon (gemini)")
    ap.add_argument("--out", required=True, help="output directory for this take")
    ap.add_argument("--shots", help="comma-separated shot ids to build (default: all)")
    ap.add_argument("--style", default=NARRATOR_STYLE, help="delivery instructions (gemini)")
    ap.add_argument("--speed", type=float, default=1.0, help="speed (elevenlabs 0.7-1.2, minimax 0.5-2.0)")
    ap.add_argument("--stability", type=float, default=0.5, help="elevenlabs stability, 0-1")
    ap.add_argument("--similarity", type=float, default=0.75, help="elevenlabs similarity boost, 0-1")
    ap.add_argument("--style-exaggeration", type=float, default=0.0, help="elevenlabs style, 0-1")
    ap.add_argument("--loudness", type=float, default=-16.0, help="integrated loudness target, LUFS")
    ap.add_argument("--no-word-check", action="store_true", help="skip transcribing the clips")
    args = ap.parse_args()

    if not shutil.which("ffmpeg"):
        fail("ffmpeg is not on PATH")
    need_env("FAL_KEY")

    shots, length = parse_plan(args.plan)
    if args.shots:
        wanted = set(args.shots.split(","))
        shots = [s for s in shots if s["id"] in wanted]
        if not shots:
            fail(f"no shots match --shots {args.shots}")
    segments = [(shot, spoken(val)) for shot in shots for kind, val in shot["items"] if kind == "text"]
    out = Path(args.out)
    (out / "clips").mkdir(parents=True, exist_ok=True)
    name, model_id = ENGINES[args.engine]
    print(f"narrate: {name} ({model_id}) voice={args.voice} shots={len(shots)} segments={len(segments)} "
          f"word_check={'off' if args.no_word_check else ASR} out={out}")

    track = array.array("h", bytes(2 * round(length * RATE)))
    records, rows, seg_i = [], [], 0
    for shot in shots:
        t, first_in, n = float(shot["start"]), None, 0
        for kind, val in shot["items"]:
            if kind == "pause":
                t += val
                continue
            n += 1
            text = spoken(val)
            prev_text = segments[seg_i - 1][1] if seg_i > 0 else None
            next_text = segments[seg_i + 1][1] if seg_i + 1 < len(segments) else None
            seg_i += 1
            request = {"engine": args.engine, "model": model_id, "voice": args.voice, "settings": settings(args),
                       "text": text, "prev": prev_text if args.engine == "elevenlabs" else None,
                       "next": next_text if args.engine == "elevenlabs" else None}
            digest = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()[:10]
            clip = out / "clips" / f"{shot['id']}-{n}-{digest}.wav"
            if not clip.exists():
                to_clip(synthesize(args, text, prev_text, next_text), clip)
            clip_lufs = loudness(clip)
            samples = leveled(read_samples(clip), clip_lufs)
            dur = len(samples) / RATE
            mix_in(track, samples, t)
            rec = {"shot": shot["id"], "segment": n, "text": val, "spoken": text,
                   "start": round(t, 3), "end": round(t + dur, 3), "seconds": round(dur, 3), "clip": clip.name,
                   "clip_lufs": clip_lufs}
            if not args.no_word_check:
                heard_file = clip.with_suffix(".heard.txt")
                if not heard_file.exists():
                    heard_file.write_text(transcribe(clip))
                rec["heard"] = heard_file.read_text()
                rec["match"], rec["differences"] = word_check(text, rec["heard"])
            records.append(rec)
            print(f"  {shot['id']}-{n} {dur:5.2f}s at {clock(t)}  {val[:60]}")
            first_in = t if first_in is None else first_in
            t += dur
        speech = sum(r["seconds"] for r in records if r["shot"] == shot["id"])
        written = sum(len(words(v)) for k, v in shot["items"] if k == "text")
        rows.append({"shot": shot["id"], "slot": (shot["start"], shot["end"]), "voice_in": first_in,
                     "voice_out": t, "speech": speech, "words": written, "slack": shot["end"] - t})

    raw = out / "timeline.raw.wav"
    write_wav(raw, track)
    level = normalize(raw, out / "timeline.wav", args.loudness)
    raw.unlink()
    run(["ffmpeg", "-v", "error", "-y", "-i", str(out / "timeline.wav"), "-c:a", "aac", "-b:a", "160k",
         str(out / "timeline.m4a")])

    total_speech = sum(r["speech"] for r in rows)
    total_words = sum(r["words"] for r in rows)
    wpm = total_words / total_speech * 60
    over = [r for r in rows if r["slack"] < TAIL]
    mismatched = [r for r in records if r.get("differences")]
    (out / "segments.json").write_text(json.dumps({
        "engine": args.engine, "model": model_id, "voice": args.voice, "settings": settings(args),
        "clip_level": CLIP_LEVEL, "loudness_target": args.loudness, "loudness": level,
        "segments": records}, indent=2) + "\n")

    lines = [f"# Narration take: {args.engine} · {args.voice}", "",
             f"Built {datetime.date.today().isoformat()} by `tools/narrate.py` from `{args.plan}`.", "",
             "| Setting | Value |", "|---|---|",
             f"| Engine | {name} (`{model_id}`) |", f"| Voice | {args.voice} |",
             f"| Settings | {json.dumps(settings(args))} |",
             f"| Loudness | Clips leveled to {CLIP_LEVEL:g} LUFS each; track gain {level['gain_db']:+.1f} dB to "
             f"{level['output_lufs']:g} LUFS, peaks limited at −1.5 dBFS |", "",
             f"Speech: {total_speech:.1f} s for {total_words} words ({wpm:.0f} words per minute).", "",
             "| Shot | Slot | Voice in | Voice out | Speech | Words | Slack before the cut |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        flag = " (over)" if r["slack"] < TAIL else ""
        lines.append(f"| {r['shot']} | {clock(r['slot'][0])}–{clock(r['slot'][1])} | {clock(r['voice_in'])} | "
                     f"{clock(r['voice_out'])} | {r['speech']:.1f} s | {r['words']} | {r['slack']:.1f} s{flag} |")
    lines += ["", f"Shots that end less than {TAIL} s before the cut: "
              + (", ".join(r["shot"] for r in over) if over else "none") + "."]
    if not args.no_word_check:
        lines += ["", "## Word check", "",
                  f"Each clip was transcribed with ElevenLabs Scribe v2 and compared with its text. "
                  f"{len(records) - len(mismatched)} of {len(records)} clips match exactly."]
        for r in mismatched:
            lines.append(f"- {r['shot']}-{r['segment']} (match {r['match']}): " + "; ".join(r["differences"]))
    (out / "timing.md").write_text("\n".join(lines) + "\n")
    print(f"narrate: speech {total_speech:.1f}s, {wpm:.0f} wpm, over={[r['shot'] for r in over]}, "
          f"word mismatches={len(mismatched)}; wrote {out / 'timeline.m4a'}")


if __name__ == "__main__":
    main()
