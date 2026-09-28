#!/usr/bin/env python3
"""Prepare the placeholder world still for the 90-second sample draft.

Until the Blender world exists, the draft uses one AI-generated still of the table scene.
This script makes every image the draft needs from that single still, so the machine
view and the wide shot always match:

- frames/world_wide.png       the generated 16:9 still (5504x3072)
- frames/world_wide_half.png  the same still at half size, for the world shots
- frames/machine_view.png     the square machine view, cropped 1:1 from the still (1792x1792,
                              so one patch is 128 px and one model pixel is 8 px)
- frames/model_input_224.png  the 224x224 model input, resized from the machine view with
                              PIL bilinear, the resample that ViTImageProcessor uses
- frames/still.json           prompt, model, seed, crop, rim patch, and file hashes

Config example (the constants below):
  MODEL = "fal-ai/nano-banana-pro", SEED = 11, CROP = (1650, 864, 1792), RIM = (6, 8)

Usage:
  export FAL_KEY=...   # only needed when frames/world_wide.png does not exist yet
  python3 episodes/01-how-machines-see/sample/prep_still.py

The same seed is not guaranteed to reproduce the same image, so keep world_wide.png once
it is picked. Requires Pillow.
"""

import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
FRAMES = HERE / "frames"

MODEL = "fal-ai/nano-banana-pro"
SEED = 11
PROMPT = (
    "A calm photograph of a small tabletop scene. A pale, matte, warm off-white table in front of a "
    "soft warm-grey wall. On the table, right of center: a cobalt-blue glazed ceramic cup with a white "
    "glazed interior and a small handle; a matte red rubber ball about the size of a tennis ball, a "
    "little to the left of the cup; and a thin upright birch-plywood board standing on its edge behind "
    "the ball, like a small low wall. At the far left edge of the table, a small black camera on a short "
    "tabletop tripod, aimed at the cup and the ball. Seen from slightly above in a three-quarter view, so "
    "the cup's rim and its white inside are clearly visible. Warm, soft window light from the left, gentle "
    "soft shadows. Minimal, clean, uncluttered, everything in focus. No text, no logos, no other objects."
)
CROP = (1650, 864, 1792)  # x, y, size of the machine view inside world_wide.png
RIM = (6, 8)  # row, column of the rim patch in the 14x14 grid (0-based)


def generate(dest):
    key = os.environ.get("FAL_KEY", "")
    if not key:
        sys.exit("prep_still: FAL_KEY is not set, and frames/world_wide.png does not exist yet")
    payload = {"prompt": PROMPT, "aspect_ratio": "16:9", "resolution": "4K", "output_format": "png",
               "seed": SEED, "num_images": 1}
    req = urllib.request.Request(f"https://fal.run/{MODEL}", data=json.dumps(payload).encode(),
                                 headers={"Authorization": f"Key {key}", "Content-Type": "application/json"})
    out = json.loads(urllib.request.urlopen(req, timeout=600).read())
    urllib.request.urlretrieve(out["images"][0]["url"], dest)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    FRAMES.mkdir(exist_ok=True)
    wide_path = FRAMES / "world_wide.png"
    if not wide_path.exists():
        print(f"prep_still: generating {wide_path.name} with {MODEL}, seed {SEED}")
        generate(wide_path)
    wide = Image.open(wide_path).convert("RGB")
    x, y, size = CROP
    if x + size > wide.width or y + size > wide.height:
        sys.exit(f"prep_still: crop {CROP} falls outside the {wide.size} still")

    wide.resize((wide.width // 2, wide.height // 2), Image.LANCZOS).save(FRAMES / "world_wide_half.png")
    view = wide.crop((x, y, x + size, y + size))
    view.save(FRAMES / "machine_view.png")
    view.resize((224, 224), Image.BILINEAR).save(FRAMES / "model_input_224.png")

    files = ["world_wide.png", "world_wide_half.png", "machine_view.png", "model_input_224.png"]
    meta = {
        "note": "Placeholder still for the draft. The final world is a Blender render.",
        "model": MODEL, "seed": SEED, "prompt": PROMPT,
        "world_size": list(wide.size), "crop": {"x": x, "y": y, "size": size},
        "rim_patch": {"row": RIM[0], "col": RIM[1], "reading_order_slot": RIM[0] * 14 + RIM[1] + 1},
        "model_input": {"size": 224, "resample": "PIL bilinear (ViTImageProcessor default)"},
        "sha256": {name: sha256(FRAMES / name) for name in files},
    }
    (FRAMES / "still.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"prep_still: wrote {', '.join(files)} and still.json to {FRAMES}")


if __name__ == "__main__":
    main()
