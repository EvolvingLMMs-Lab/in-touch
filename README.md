# In Touch

**How machines perceive, understand, and act.**

In Touch is an animated explainer series. It follows one machine, step by step, as it learns to perceive, understand, and act in the world. Each episode starts from a concrete scene, goes inside the model, and shows how that scene turns into pixels, vectors, words, and finally actions.

The series is fully animated, with narration and music and no on-camera host. It is made for people who are curious about AI and want to understand how it works, without having read the papers. The technical depth lives in the pictures, and the narration stays plain.

## One small world

Every episode returns to the same scene: a table, a cup, a ball, and a small wooden board. The machine is a camera on a stand at the table's edge.

Each episode adds one new ability to this world. In Episode 1, the machine turns what its camera sees into vectors. In Episode 2, it answers questions about the scene. In Episode 3, the picture goes dark and it has to listen to the ball roll. Later chapters use the same table for depth, tracking, prediction, and action: the ball rolls behind the board, the machine predicts where it will come out, and in the end it moves the board to catch it.

## Chapter One: Learning to Perceive

| # | Episode | The question | Length | Status |
|---|---|---|---|---|
| 01 | **How Machines See**: Vision Transformers, Visually Explained | How does a picture become something a machine can compute with? | 10–12 min | [Script draft](episodes/01-how-machines-see/script.md) · [90-second sample plan](episodes/01-how-machines-see/sample-90s-plan.md) |
| 02 | **Giving Language Eyes**: Flamingo and LLaVA | How does a language model use what's in a picture? | 12–15 min | Planned |
| 03 | **A New Sense**: Teaching Language Models to Hear | When you add a new sense, what can be reused, and what has to be learned? | 7–10 min | Planned |

Later chapters: *Learning to Predict* and *Learning to Act*.

## How we make it

- **Start from a question.** Every segment opens with the question the viewer has at that moment, never with a definition.
- **Every animation explains something.** A motion that carries no idea gets cut.
- **Keep the thread to the world.** The signature move goes world → representation → computation → world. On screen, every vector stays tied to the part of the scene it came from.
- **Say what kind of picture it is.** Every shot has a tag:
  - `ILLUSTRATION`: a mechanism drawn to explain it.
  - `MEASURED`: data from a real model run, naming the checkpoint, the layer or head, and the method.
  - `NARRATIVE`: story, with no technical claim.

  We never label a vector dimension with a meaning we have not measured.
- **Give color a job.** Vision, language, and audio each get a color family. Training shows as a pulse, and frozen modules get a lock. Shape and labels always back up color.
- **Leave room to understand.** Sound marks state changes, not every token. Each episode has a 20–30 second stretch with no narration, where the viewer watches the rules run.
- **Trace every claim.** Each script ends with a table that maps each technical claim to the paper section, figure, or checkpoint it comes from.

## Tools

Planned: [Manim Community](https://www.manim.community/) v0.21.0 for the computation layer (patches, vectors, attention, formulas) and [Blender](https://www.blender.org/) 5.2 LTS for the world (the table scene, camera moves, materials). Versions are pinned per episode.

## Repository layout

```
README.md
episodes/
  01-how-machines-see/
    script.md              Episode 1 script: narration, visuals, sound, tags, sources
    sample-90s-plan.md     Plan for the 90-second style sample, cut from Episode 1
```

## Status

Pre-production. The Episode 1 script is a first draft. The 90-second style sample comes next, and it sets the look, sound, and pipeline for the series.
