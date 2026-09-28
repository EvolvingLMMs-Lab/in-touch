# Episode 1 · 90-second style sample: production plan

| | |
|---|---|
| Status | Plan · 2026-09-28 |
| Length | 1:30 |
| Source | A cut of [the Episode 1 script](script.md): beats 0.1–0.3, 1.1, 2.1, 2.2, 2.4, 4.1, 4.4 |
| Arc | A patch you can't read → the full cup → the machine's camera image → patches → vectors → one round of gathering information |

## Why this sample comes first

The sample is the first finished piece of the series. It sets the look, the sound, and the pipeline that every later episode reuses. It has to answer four questions:

1. **Does the world look good?** The table scene holds up full screen, with real volume, shadow, and material.
2. **Does the move into the computation layer feel natural?** The viewer always knows which part of the world the numbers came from.
3. **Do narration and picture support each other?** Each sentence has a visual change that shows the same idea, at the same moment.
4. **Does the music leave room to understand?** The narration stays clear, and the silent beat reads as a moment, not a gap.

**Out of scope for the sample:** position embeddings, the query/key/value math, heads and layers, training, and every `MEASURED` shot. The sample uses only `NARRATIVE` and `ILLUSTRATION` shots.

## The cut

Eight shots. The durations add up to 90 seconds.

| Shot | Time | Length | Tag | Script beat | Tool |
|---|---|---|---|---|---|
| S1 | 0:00–0:11 | 11 s | `NARRATIVE` | 0.1 | Manim, using a Blender still |
| S2 | 0:11–0:25 | 14 s | `NARRATIVE` | 0.2 | Manim, using a Blender still |
| S3 | 0:25–0:34 | 9 s | `NARRATIVE` | 0.3 | Blender, plus a compositing layer |
| S4 | 0:34–0:48 | 14 s | `ILLUSTRATION` | 1.1 | Blender, then compositing, then Manim |
| S5 | 0:48–0:58 | 10 s | `ILLUSTRATION` | 2.1 | Manim |
| S6 | 0:58–1:07 | 9 s | `ILLUSTRATION` | 2.2, 2.4 | Manim |
| S7 | 1:07–1:26 | 19 s | `ILLUSTRATION` | 4.1, 4.4 | Manim |
| S8 | 1:26–1:30 | 4 s | `NARRATIVE` | End card | Manim |

## Narration

163 words. At about 155 words per minute that is 63 seconds of speech, which leaves 27 seconds of picture and music. Every line comes from the script. Some lines drop a phrase, and no line is new.

Times in parentheses are silences. A marker at the start of a shot is the wait before the voice comes in; a marker inside a line is a pause. [`tools/narrate.py`](../../tools/narrate.py) reads this block and the cut table to build the voice track.

> **S1.** *(1 s)* Look at this small square. Can you tell what it is? *(pause, 1.5 s)* A curve. A bit of blue, a bit of white. Maybe a shadow.
>
> **S2.** *(0.5 s)* Now let the rest of the picture back in. *(the rings return, 3 s)* It's the rim of a cup. Nothing inside that square changed. What changed is everything around it.
>
> **S3.** *(2.5 s, the machine comes into view)* This is our machine. For now, it has one sense: a camera.
>
> **S4.** *(0.5 s)* The machine doesn't receive a cup. It receives this: a grid of pixels, and for each pixel, three numbers. How much red, how much green, how much blue.
>
> **S5.** *(0.5 s)* Cut the picture into squares. Then line them up, left to right, top to bottom, the way you'd read words on a page.
>
> **S6.** *(0.5 s)* Every patch goes through the same matrix. So far, each vector knows only its own small square.
>
> **S7.** *(0.5 s)* How does it get the context you used? It asks. *(6 s, no narration)* This position still stands for a small piece of the cup's rim. But what it carries now includes the rest of the picture.

If the recorded read runs long, cut words. Keep the silent beat in S7.

## Shots

Each shot lists the brief's five fields: the viewer's question, narration, visual, sound, and technical basis.

### S1 · 0:00–0:11 · The piece you can't read

- **Viewer's question.** What is this?
- **Narration.** "Look at this small square. Can you tell what it is? … A curve. A bit of blue, a bit of white. Maybe a shadow."
- **Visual.** Black. The rim patch fades in at the center, about 512×512 on screen, in full render detail (not pixelated). A slow push-in, about 5%.
- **Sound.** Silence for one second, then a faint room tone.
- **Technical basis.** None; this is story. The square is exactly one patch of the model's 14×14 grid over the machine's view, the same patch that S6 and S7 follow.

### S2 · 0:11–0:25 · The rest comes back

- **Viewer's question.** Oh, what is it part of?
- **Narration.** "Now let the rest of the picture back in. … It's the rim of a cup. Nothing inside that square changed. What changed is everything around it."
- **Visual.** The neighboring patches return one ring at a time, spiraling outward from the rim patch, until the whole square view is back at 896×896. The rim patch keeps a thin ink outline.
- **Sound.** One soft, grainy tick per ring. The pitch rises with each ring and settles on the last.
- **Technical basis.** None; this is story. The rings are real patch boundaries: ring *n* holds the patches at Chebyshev distance *n* from the rim patch.

### S3 · 0:25–0:34 · Meet the machine

- **Viewer's question.** Whose view is this?
- **Narration.** "This is our machine. For now, it has one sense: a camera."
- **Visual.** The rings keep going past the square's edge and fill the full 16:9 frame (handoff A, below). The picture turns out to be a view through a lens. The camera pulls back through it and reveals the machine: a small camera on a stand at the table's edge, looking at the cup, the ball, and the board. The title "IN TOUCH" appears for two seconds, lower third.
- **Sound.** The series motif, first statement: four warm notes. A faint air sound on the pull-back.
- **Technical basis.** None; this is story.

### S4 · 0:34–0:48 · From a view to numbers (the signature transition)

- **Viewer's question.** What does the machine actually get?
- **Narration.** "The machine doesn't receive a cup. It receives this: a grid of pixels, and for each pixel, three numbers. How much red, how much green, how much blue."
- **Visual.** The machine's image slides forward out of the camera's field of view, turns to face us, and settles flat at 896×896 in the center of the frame (handoff B, below). The room fades to paper behind it. The image then snaps to 224×224 pixels. Zoom into the rim until single pixels fill the frame, each showing three numbers in the mono font. Tag, bottom left: "Real pixel values from this frame."
- **Sound.** A soft lift of air as the image leaves the room. A dry snap when it turns into pixels.
- **Technical basis.** The numbers are the real 0–255 RGB values of the 224×224 model input, made from the locked frame by resizing it to 224×224 with the checkpoint's preprocessing [2]. The model then scales these values to the range −1 to 1; that step is not shown.

### S5 · 0:48–0:58 · Patches

- **Viewer's question.** How do you give this to a model built for sentences?
- **Narration.** "Cut the picture into squares. Then line them up, left to right, top to bottom, the way you'd read words on a page."
- **Visual.** Zoom back out to the full 224×224 image. Grid lines slice it into 14×14 patches. The patches lift and line up in reading order into one long row that runs off screen, with the rim patch outlined. Then the row folds back onto the grid.
- **Sound.** One soft paper-cut sound for the slicing. A light run of ticks as the row forms.
- **Technical basis.** 224 / 16 = 14, so 196 patches in raster order [1, §3.1].

### S6 · 0:58–1:07 · One recipe, applied 196 times

- **Viewer's question.** What does the model do with each square?
- **Narration.** "Every patch goes through the same matrix. So far, each vector knows only its own small square."
- **Visual.** The rim patch unrolls into a long column of numbers, meets a matrix labeled **E**, and comes out as a stack of 8 shaded cells. Caption: "Drawn with 8 numbers. ViT-Base uses 768." A quick ripple as every other patch does the same. Each vector ends up standing beside its patch on a thin tether.
- **Sound.** One soft stamp when the rim vector forms, then a quiet swell for the ripple, not one click per patch.
- **Technical basis.** One shared linear projection **E** [1, Eq. 1]. The input column has 768 numbers (16 × 16 × 3). Do not animate **E** as a pass-through.

### S7 · 1:07–1:26 · One round of gathering (the key shot)

- **Viewer's question.** How does the rim patch get the context we used?
- **Narration.** "How does it get the context you used? It asks." Then six seconds without narration. Then: "This position still stands for a small piece of the cup's rim. But what it carries now includes the rest of the picture."
- **Visual.** The rim vector sends out a single query, drawn as a soft ring that sweeps the grid. Every patch glows by its weight. Values stream toward the rim vector, each as thick as its weight: thick from the rest of the rim and the cup's body, thin from the far table. They merge and are added to the rim vector, and its cells shift shade. The tether never moves. Tag, bottom left: "Illustration · weights drawn for explanation."
- **Sound.** A soft ping for the query. Near-silence while the weights glow. The motif's chord resolves as the streams merge.
- **Technical basis.** Softmax weights over all patches, a weighted sum of values, and a residual add [1, App. A; §3.1, Eq. 2]. The weights are hand-drawn.

### S8 · 1:26–1:30 · End card

- **Visual.** "In Touch · Episode 1: How Machines See" on paper.
- **Sound.** The motif's last note rings out.

## Look

Starting values. Lookdev validates them (phase P2), and after sign-off they become the series style guide.

### Frame format

- 1920×1080, 30 fps, progressive, sRGB / Rec. 709, SDR. Every source uses this format: set Blender's scene to 30 fps and render Manim with `--frame_rate 30`. Mixed frame rates are the most common way these pipelines break.

### Colors

The table and the paper are close in value, so the room fading to paper reads as the same space turning abstract.

| Token | Value | Use | Contrast on paper |
|---|---|---|---|
| `paper` | `#EEEAE3` | Computation-layer background | — |
| `ink` | `#22201C` | Text, strokes, outlines | 13.6 : 1 |
| `ink-2` | `#625D55` | Captions and tags | 5.5 : 1 |
| `grid` | `#CBC4B8` | Patch grid lines (decorative) | 1.4 : 1 |
| `vision` | `#12806A` | Vision tokens, attention glow | 4.1 : 1 (graphics only) |
| `vision-dark` | `#0B4A3E` | Vision text, high-value cells | 8.5 : 1 |
| `vision-light` | `#D3ECE6` | Low-value cells (always with an `ink-2` hairline) | 1.0 : 1 |
| `language` | `#6C4AB6` | Reserved for Episode 2 | 5.3 : 1 |
| `audio` | `#B07A08` | Reserved for Episode 3 | 3.1 : 1 |
| `error` | `#B5306B` | Error and gradient pulses (Episode 1, beat 5.2) | 4.9 : 1 |

World materials: a matte warm off-white table (about `#E6E0D6`), a cobalt glaze cup (about `#2E4E9B`) with a white interior (`#F3EFE7`), a matte red rubber ball (about `#CF3F2E`), and a birch board (about `#CDAE84`). The object hues stay clear of the token hues. Blue stays with the cup, green-teal with vision, and red with the ball.

Vector cells use a sequential ramp inside the modality's hue, from `vision-light` for low values to `vision-dark` for high ones. Color never works alone: vision cells are square, and later modalities get their own cell shapes and labels.

### Type

- Labels and titles: Inter.
- Numbers in pixels, vectors, and matrices: JetBrains Mono.
- Formulas, when needed: Manim's `MathTex`. The sample has none.

### On-screen tags

A small `ink-2` label at the bottom left: "Illustration · …", "Measured · checkpoint · layer/head · method", or "Real pixel values from this frame". In the sample, S4 and S7 carry tags.

## Sound

- **Motif.** A short series motif of about four notes. It changes timbre with each sense in later episodes. The sample uses it twice: its first statement in S3, and a variation with a grainy texture that resolves in S7 and rings out in S8.
- **Effects only on state changes.** Ring returns, the image lifting out, the snap to pixels, slicing, the vector forming, the query, and the merge. Never one sound per token.
- **Mix.** The narration must be clear on laptop speakers. Music ducks about 8–10 dB under the voice. Master to −14 LUFS integrated, true peak at or below −1 dBTP.
- **Voice.** A synthetic voice (decided 2026-09-28). [`tools/narrate.py`](../../tools/narrate.py) builds the voice track from the Narration block: one clip per segment, trimmed, placed on the cut, loudness-matched, and checked word for word with speech-to-text. To change a line, edit the Narration block and rebuild; unchanged clips come from the cache.

### Voice takes (2026-09-28)

Six takes of the same narration, each a full 90-second track. Every clip is leveled to the same loudness, and each track sits at about −16 LUFS. Every clip passed the word check (ElevenLabs Scribe v2 transcript against the text). "Tight shots" are shots where the voice ends less than 0.25 s before the cut.

| Take | Engine | Voice | Pace | Tight shots |
|---|---|---|---|---|
| `elevenlabs-george` | ElevenLabs Multilingual v2, speed 1.0 | George | 193 wpm | none |
| `elevenlabs-george-0.9` | ElevenLabs Multilingual v2, speed 0.9 | George | 166 wpm | S1 (0.1 s) |
| `elevenlabs-matilda` | ElevenLabs Multilingual v2, speed 1.0 | Matilda | 186 wpm | none |
| `elevenlabs-matilda-0.9` | ElevenLabs Multilingual v2, speed 0.9 | Matilda | 174 wpm | none |
| `gemini-charon` | Gemini 3.8 Flash TTS, style instructions | Charon | 156 wpm | S1 (−0.1 s), S7 (0.0 s) |
| `minimax-graceful-lady` | MiniMax Speech 2.8 HD, speed 1.0 | English_Graceful_Lady | 141 wpm | S1, S2, S4, S5, S7 (−0.9 to 0.1 s) |

- All three engines run through fal. fal's model catalog lists each of them with a commercial license, and fal's terms say the model providers' own terms may also apply.
- S6 dropped "One recipe, applied 196 times." Every take overran S6 with it: the number alone is five spoken words ("a hundred and ninety-six").
- Once a take is picked, record its engine, voice, and settings here. The files live under `sample/audio/narration/`, outside git.

## Build

### Tools

- **Manim Community v0.21.0** (needs Python ≥ 3.11) for S1, S2, the end of S4, and S5–S8. Use a project virtual environment with Manim pinned. The sample uses `Text`, not `MathTex`, so it needs no LaTeX install.
- **Blender 5.2.2 LTS** for the world: the machine-view still, S3, and the start of S4. Start with EEVEE. Switch the world shots to Cycles only if the lookdev stills need it. The sample has about 17 seconds of world footage, around 510 frames.
- **An editor with compositing** (DaVinci Resolve with Fusion, for example) for the corner pin in S4, assembly, the mix, and a light grade.

### Sources of truth

1. **The machine-view still.** Rendered once from the machine camera: square, 3584×3584 pixels (224 × 16), so one model pixel is exactly 16×16 render pixels and one patch is 256×256. Saved as an 8-bit sRGB PNG with its hash. S1 and S2 are cut from this file.
2. **The model input.** The same still, resized to 224×224 with the checkpoint's preprocessing [2]. This file supplies the pixel values in S4. Save it with its hash.
3. **The rim patch.** Its row and column in the 14×14 grid, chosen during layout. Test it: shown the square alone, at least two of three people should fail to name "cup."

### Handoff A: the flat still becomes the room (S2 → S3)

The first frame of S3 is rendered from the machine camera's exact pose, with sensor fit set to vertical and the same focal length. Its center 1080×1080 region is then the machine view. In the edit, the ring reveal continues past the square's edge into the 16:9 frame, and the square scales from 896 to 1080 pixels as it does. Check it with a difference blend of the two frames.

### Handoff B: the room becomes paper (S4)

This is the hardest shot. The floating image is a 2D layer, not a Blender object:

1. Blender renders the room and exports the four screen-space corners of the camera frustum's far plane for each frame (a short Python script in Blender).
2. In compositing, the machine-view PNG is corner-pinned from those four corners to the target rectangle: 896×896, centered.
3. The room cross-fades to `paper` under the image.

The image never passes through Blender's color management, so its last frame matches Manim's first frame pixel for pixel. Manim then starts from the same PNG at the same rectangle and does the snap to 224×224. Check it with a difference blend. Fallback: cut on a fast move with a cross-dissolve of 4–6 frames.

### Files in this repository (created when production starts)

```
episodes/01-how-machines-see/sample/
  manim/     one module per shot group, e.g. s01_s02_cold_open.py
  blender/   world scene and the frustum-corner export script
  frames/    the locked machine-view still, the 224×224 model input, and their hashes
  audio/     voice, music, and effect stems
  edit/      editor project and an EDL or OTIO export
```

Renders stay out of git. Before the first render, decide where `.blend` files and audio live (see open decisions).

## Schedule

Estimates are for one generalist animator plus a part-time composer.

| Phase | Work | Exit criteria | Estimate |
|---|---|---|---|
| P0 · Lock | Lock the narration above. Sketch the machine-view composition. | Narration locked. | 0.5 day |
| P1 · Animatic | The picked synthetic take as the voice track. Manim blockout at low quality with placeholder colors. Blender grey-box of the table and the machine camera. Cut to the voice track. | Runs 90 s ± 2 s. Every line has its visual. The silent beat is intact. Review with Brian: story and timing. | 1–2 days |
| P2 · Lookdev | Materials and light. Render the final machine-view still, and pick and test the rim patch. Three hero stills: the machine view, the wide world, and a close-up of the cup. Palette check on three Manim frames. | Brian approves the stills and palette. The still and the 224×224 input are locked, with hashes. | 2–3 days |
| P3 · Build | Final Manim shots S1, S2, S4 (second half), and S5–S8. Blender shots S3 and S4 (first half). Handoffs A and B. | Both difference-blend checks pass. | 4–6 days |
| P4 · Sound | Motif sketch, effects pass, and the final voice. Starts once P1 locks the timing and runs alongside P3. | Mixed to target loudness. | 2–3 days |
| P5 · Assemble and review | Edit, light grade (match the world's whites to `paper`), and mix. Run the review below. | Sign-off, or a fix list. | 1–2 days |

Total: about two to three weeks for one person, plus the composer.

## Review

The sample passes when all of these hold:

1. **World.** The three hero stills hold up full screen on a large display. The cup reads as ceramic, the ball as rubber, and the board as wood.
2. **Transitions.** At both handoffs, the difference blend shows only the intended motion. Asked "where did the numbers come from?", viewers point to the camera.
3. **Narration and picture.** Each sentence has a visual change showing the same idea on the same beat, and nothing moves without a reason. With the sound off, the order of steps is still clear. With the picture off, the narration still makes sense.
4. **Music.** The narration is clear on laptop speakers, and the silent beat in S7 reads as a moment.
5. **Labels.** S7 carries its illustration tag, and the numbers in S4 match the locked 224×224 input.
6. **Viewer test.** Three to five people who don't know ViT watch it once, then answer three questions:
   - What does the machine actually receive?
   - What happens to the picture before the model uses it?
   - What changed about the rim square at the end?

   The sample passes if most viewers answer all three in their own words: "numbers," "it's cut into squares and lined up," and "it took in information from the rest of the picture."

## Open decisions

1. **Narrator.** A synthetic voice (decided 2026-09-28). Pick one of the voice takes above; the picked take sets the final timing.
2. **Music.** Commission the series motif now, or use a temporary track for the sample?
3. **Large files.** Git LFS in this public repository, or external storage for `.blend` files, audio, and renders?
4. **License.** The repository has none yet, so all rights are reserved by default. Choose one before accepting outside contributions.

## References

1. A. Dosovitskiy et al. "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale." ICLR 2021. [arXiv:2010.11929](https://arxiv.org/abs/2010.11929)
2. `google/vit-base-patch16-224`, model card and preprocessing config. [Hugging Face](https://huggingface.co/google/vit-base-patch16-224)
