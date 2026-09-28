# Episode 1: How Machines See

*Vision Transformers, Visually Explained*

| | |
|---|---|
| Series | In Touch · Chapter One: Learning to Perceive |
| Status | Draft 0.1 · 2026-09-28 |
| Length | About 12:00 with the optional beat 2.3, about 11:40 without it |
| Narration | About 1,450 words, timed at 150 words per minute, plus a 25-second stretch with no narration |
| Model | The original Vision Transformer (ViT) [1] |
| The question | How does a picture become something a machine can compute with? |

## How to read this script

- Each beat has a time, a tag, and up to four parts: **Visual**, **Narration**, **Sound**, and **Note** (production and technical notes). Every technical claim is traced in [Claims and sources](#claims-and-sources).
- Tags:
  - `NARRATIVE`: story and world. No technical claim.
  - `ILLUSTRATION`: a mechanism drawn to explain it. Shapes, sizes, and weights are chosen for clarity. They are not taken from a model.
  - `MEASURED`: data from a real model run. The shot names the checkpoint, the layer or head, and the method. See [Measurements](#measurements).
- Numbers are for ViT-Base with 16×16 patches (ViT-B/16) and 224×224 input.
- Measured shots use the public checkpoint `google/vit-base-patch16-224` (pretrained on ImageNet-21k, fine-tuned on ImageNet-1k) [3]. The paper's headline results come from models pretrained on JFT-300M, which are not public.
- Times are estimates. The animatic with a scratch read sets the real timing.

## The world

- **The table scene.** A pale matte table. A cobalt-blue ceramic cup, white inside. A red rubber ball. A thin birch board standing upright. Warm, soft light.
- **The machine.** A small camera on a stand at the table's edge. Its view is square.
- **The rim patch.** One square of the machine's 14×14 patch grid holds a piece of the cup's rim: an arc where blue glaze meets white, with a sliver of shadow. It is the square in the cold open and the patch we follow for the whole episode. Frame the shot so that this square is hard to read on its own.

## At a glance

| Part | Time | The viewer's question |
|---|---|---|
| Cold open | 0:00–1:04 | What is this small piece? |
| 1. What the machine receives | 1:04–2:08 | What does the model actually get? |
| 2. Cutting the picture into words | 2:08–3:46 | How do you give a picture to a model built for sentences? |
| 3. Where each piece came from | 3:46–5:33 | Once the patches are in a line, is the layout still there? |
| 4. Attention | 5:33–8:45 | How does one patch use the others? |
| 5. Where the usefulness comes from | 8:45–11:24 | Why would any of this become useful? |
| Ending | 11:24–12:00 | What is left, and where does it go next? |

---

## Cold open

### 0.1 · The piece you can't read

`NARRATIVE` · 0:00–0:17

**Visual.** Black. One square fades in at the center, large and in full render detail: a curved band of cobalt blue meets a band of white, with a soft grey shadow in one corner. A slow push-in.

**Narration.**

> Look at this small square. Can you tell what it is?
>
> *(pause)*
>
> A curve. A bit of blue, a bit of white. Maybe a shadow. Not much to go on.

**Sound.** Silence, then a faint room tone.

### 0.2 · The rest comes back

`NARRATIVE` · 0:17–0:37

**Visual.** The neighboring squares return one ring at a time, spiraling outward, until the whole view is back: a blue ceramic cup on a pale table, seen from a little above. The first square keeps a thin outline. It sits on the cup's rim.

**Narration.**

> Now let the rest of the picture back in.
>
> *(the rings return)*
>
> It's the rim of a cup. There's the handle, and its shadow on the table.
>
> Nothing inside that square changed. What changed is everything around it.

**Sound.** Each ring lands with a soft, grainy tick. The ticks rise, then settle.

**Note.** The squares are the model's real patch grid (14×14 over the machine's view). Beat 2.1 pays this off.

### 0.3 · Meet the machine

`NARRATIVE` · 0:37–1:04

**Visual.** The rings keep going past the square's edge and fill the wide frame. The flat picture turns out to be a view through a lens. We pull back through it: a small camera on a stand at the table's edge, looking at the cup, a red ball, and a thin wooden board standing upright. A faint outline shows the camera's field of view.

**Narration.**

> You read that square by using what was around it, without even trying.
>
> This is our machine. For now, it has one sense: a camera.
>
> In this episode, we'll build a way for it to do what you just did: let every piece of a picture use every other piece.

**Title.** IN TOUCH · Episode 1: How Machines See

**Sound.** The series motif enters: four warm notes, unhurried.

---

## 1. What the machine receives

*The viewer's question: what does the model actually get?*

### 1.1 · From a view to numbers

`ILLUSTRATION` · 1:04–1:40

**Visual.** The signature transition. The camera's image slides forward out of its field of view, turns to face us, and settles flat. The room fades to warm-grey paper behind it. The image snaps to a coarse grid of 224×224 pixels. Zoom into the rim: each pixel is a small square with three numbers on it.

**Narration.**

> When the camera looks at the table, the machine doesn't receive a cup. It receives this: a grid of pixels, and for each pixel, three numbers. How much red, how much green, how much blue.
>
> The model we'll look at takes pictures 224 pixels on a side. That's about fifty thousand pixels, and a hundred and fifty thousand numbers.
>
> The cup is in there somewhere, spread across thousands of them. None of them says "cup."

**Sound.** A soft lift of air as the image leaves the room. A dry snap when it turns into pixels.

**Note.** The numbers on screen are the real RGB values (0–255) of our 224×224 model input, made from the final frame with the checkpoint's own preprocessing. Tag on screen: "Real pixel values from this frame."

### 1.2 · A model built for sentences

`ILLUSTRATION` · 1:40–2:08

**Visual.** To one side, a short sentence appears, *the ball rolls behind the board*, and breaks into pieces. Each piece becomes a vector in a row. Thin arcs link every position to every other. Then back to the square picture, which is clearly not a row.

**Narration.**

> That model is called a Vision Transformer, or ViT. Researchers at Google introduced it in 2020.
>
> Transformers were built for text. A Transformer takes a sequence, one vector for each piece of a sentence, and lets every position gather information from every other.
>
> That's the ability we want. But a picture isn't a sequence. So the first step is to make it one.

---

## 2. Cutting the picture into words

*The viewer's question: how do you give a picture to a model built for sentences?*

### 2.1 · Patches

`ILLUSTRATION` · 2:08–2:41

**Visual.** Grid lines slice the picture into 14×14 squares. The squares lift off and line up in reading order, left to right and top to bottom, into one long row that runs off screen. The rim square keeps its outline, so we can find it in the row.

**Narration.**

> The idea is almost blunt: cut the picture into squares.
>
> With squares sixteen pixels wide, our picture becomes a 14-by-14 grid: 196 patches. You've already met them. The square at the start of this video was one of these patches.
>
> Then line them up, left to right, top to bottom, the way you'd read words on a page. That's where the paper got its title: *An Image Is Worth 16x16 Words.*

**Sound.** One soft paper-cut sound for the slicing, not one per line. A light run of ticks as the row forms.

### 2.2 · One recipe, applied 196 times

`ILLUSTRATION` · 2:41–3:15

**Visual.** The rim patch unrolls into one long column of 768 numbers (16 × 16 × 3). A matrix labeled **E** appears, drawn as a stack of small patch-shaped patterns. The column meets each pattern in turn, and each meeting gives one number. The numbers collect into a short stack of shaded cells: the embedding. Caption: "Drawn with 8 numbers. ViT-Base uses 768." Then every other patch runs through the same **E** in a quick ripple.

**Narration.**

> Take one patch. Sixteen by sixteen pixels, three numbers each: 768 numbers, unrolled into one long list.
>
> Now multiply that list by a matrix. Picture the matrix as a stack of patterns, each the size of a patch. Multiplying measures how much of each pattern our patch contains, one number per pattern. Together, those numbers form a vector: the patch's embedding.
>
> Every patch goes through the same matrix. One recipe, applied 196 times.

**Note.** In ViT-B/16, the flattened patch and the embedding both have 768 numbers. That is a coincidence of the chosen sizes: ViT-L/16 maps the same 768 numbers to 1,024. Never animate **E** as a pass-through.

### 2.3 · What the patterns become (optional)

`MEASURED` · 3:15–3:34

**Visual.** The main patterns of **E** in a trained model, drawn as small colored tiles. Tag: "Measured · google/vit-base-patch16-224 · patch-embedding filters, top principal components (M1)".

**Narration.**

> Nobody draws these patterns by hand. They start out random, and training shapes them. Here are the main ones from a trained model: smooth ramps, stripes, checkerboards. Simple building blocks for describing the detail inside a patch.

**Note.** Optional; cut for time if needed. The paper reports this for ViT-L/32 (Fig. 7, left). Confirm the description against our own measurement M1 before recording, and rewrite the second half of the line to match what M1 shows.

### 2.4 · What each vector knows so far

`ILLUSTRATION` · 3:34–3:46

**Visual.** Back to the grid. Each patch now has its embedding standing beside it, tied to it by a thin line (a tether). The rim patch's embedding is highlighted.

**Narration.**

> So far, each vector knows only its own small square. Our rim patch still has no idea it belongs to a cup.

**Note.** The tether rule starts here: from now on, every vector on screen stays tied to its patch.

---

## 3. Where each piece came from

*The viewer's question: once the patches are in a line, is the layout still there?*

### 3.1 · A set, not a sentence

`ILLUSTRATION` · 3:46–4:15

**Visual.** The row of embeddings. A thought experiment: the patches shuffle into a scrambled mosaic, and the row shuffles the same way. Both versions go through a dimmed model box. The two answers that come out are identical, and an equals sign appears between them.

**Narration.**

> Now a problem. We lined the patches up in reading order, but the next part of the model, called attention, doesn't read in order. It treats its inputs as a set.
>
> So with nothing else added, shuffling the patches wouldn't change the model's final answer at all.
>
> To this machine, a scrambled cup and a whole cup would be the same picture.

### 3.2 · A return address

`ILLUSTRATION` · 4:15–4:40

**Visual.** Each slot in the row gets its own vector, drawn in a lighter outline style. It is added to the patch embedding: a plus sign, then the cells blend.

**Narration.**

> The fix: add a second vector to each patch, a position embedding. There's one for every slot in the line, like a return address.
>
> Here's the interesting part. In ViT, these position vectors start out random. Nobody tells the model that slot 15 sits right below slot 1. Whatever it knows about the grid, it has to learn.

**Note.** Slots are numbered from 1 in reading order, 14 per row, so slot 15 is directly below slot 1.

### 3.3 · The grid, rediscovered

`MEASURED` · 4:40–5:06

**Visual.** A 14×14 grid of tiles. One slot is selected, and every tile is shaded by how similar its position vector is to the selected one. A bright patch sits around the selection, with faint bands along its row and column. The selection moves, and the bright spot follows. Tag: "Measured · google/vit-base-patch16-224 · cosine similarity of learned position embeddings (M2)".

**Narration.**

> This is from a real, trained model. Pick one slot, and shade every other slot by how similar its position vector is.
>
> The neighbors light up. So do the slots in the same row and the same column.
>
> The model worked out the shape of the grid on its own.

**Note.** The paper shows this for ViT-L/32 (Fig. 7, center). Confirm on our checkpoint (M2) before recording. If the row and column bands are not visible, cut the second line.

### 3.4 · An honest footnote

`ILLUSTRATION` · 5:06–5:33

**Visual.** A small card: "No position embeddings: 61.4 · Learned 1D: 64.2 · ViT-B/16, ImageNet 5-shot linear probe (paper, Table 8)." Then back to the world: the cup and the ball, with a small question mark between them.

**Narration.**

> An honest footnote: in the paper's own tests, removing position information completely cost only about three points on one benchmark. For naming what's in a picture, a bag of patches goes a long way.
>
> But ask which side of the ball the cup is on, and a bag of patches can't tell. Keep that question in mind. It comes back.

**Note.** "Bag of patches" is the paper's own phrase (App. D.4). The question returns at the top of Episode 2.

---

## 4. Attention

*The viewer's question: how does one patch use the others?*

### 4.1 · Back to the rim

`ILLUSTRATION` · 5:33–5:51

**Visual.** The picture with its patch grid. The rim patch's vector stands beside it, enlarged, on its tether.

**Narration.**

> Now, the heart of it. Back to our rim patch, the one you couldn't read on its own. Its vector knows its own square and where that square sits. How does it get the context you used?
>
> It asks.

### 4.2 · Query, key, value

`ILLUSTRATION` · 5:51–6:13

**Visual.** From the rim vector, three smaller vectors split off through three matrices: a query, drawn with a notch; a key, drawn with a tab that fits notches; a value, drawn as a solid block. Then every patch splits the same way, all at once.

**Narration.**

> Each vector is multiplied by three more learned matrices, making three new vectors.
>
> A query: what am I looking for?
>
> A key: here's what I contain.
>
> And a value: the message I'll pass along to anyone who finds my key relevant.
>
> Every patch makes all three.

### 4.3 · Scores and weights

`ILLUSTRATION` · 6:13–6:44

**Visual.** The rim patch's query sweeps across the grid, and a score appears over each patch. The scores pass through a softmax and become weights: each patch glows with its weight, and a small counter shows that the weights add up to 1.

**On screen.** weights = softmax( q · k / √d )

**Narration.**

> Our rim patch compares its query with every key in the picture, all 196, its own included.
>
> Each comparison is a dot product: one number, large when the two vectors point the same way.
>
> A softmax turns those scores into weights. They're all positive, and they add up to one. The square root in the formula just keeps the scores from growing too large.

**Note.** The class token (beat 5.1) adds one more key, so the real sequence has 197 positions. It is not introduced yet, so the narration says 196.

### 4.4 · One vector changes (the key shot)

`ILLUSTRATION` · 6:44–7:09

**Visual.** Values stream from every patch toward the rim vector, each stream as thick as its weight: thick from the rest of the rim and the cup's body, thin from the far edge of the table. The streams merge into one vector, which is added to the rim vector. Its cells shift shade. The tether to the rim patch never moves. Tag: "Illustration · weights drawn for explanation".

**Narration.**

> Then it takes a weighted average of everyone's values, mostly from the patches it matched best, and adds that to its own vector.
>
> *(pause while the streams merge)*
>
> This position still stands for a small piece of the cup's rim. But what it carries now includes the rest of the picture.

**Sound.** A soft chord resolves as the streams merge.

**Note.** "Adds that to its own vector" is the residual connection. Keep the weight pattern plausible, but it stays an illustration. Do not reuse this frame in any measured shot.

### 4.5 · Everyone at once, in many ways at once

`ILLUSTRATION` · 7:09–7:43

**Visual.** Zoom out: all 196 patches do the same thing at the same time, each with its own pattern of weights. Several translucent copies of the grid fan out, each with a different pattern: the heads. Then a simple layer diagram: attention, then MLP, each with an arrow that adds its result back to the vector.

**Narration.**

> Every patch does this at the same time, each with its own query. That's self-attention.
>
> A layer runs several of these side by side, twelve in ViT-Base. Each one is called a head. It has its own matrices, so each head can look for something different.
>
> Then each vector goes through a small neural network of its own, an MLP, to work on what it just gathered.
>
> Attention, then MLP: that's one layer. ViT-Base stacks twelve.

**Note.** Layer normalization before each block stays off screen.

### 4.6 · The understanding moment

`ILLUSTRATION` · 7:43–8:08

**Visual.** The stack runs, layer after layer. Light moves between patches across the grid. The rim vector's cells shift a little with each layer, and its tether never breaks. Near the end, the camera drifts up until the whole grid and the cup are in view. Tag: "Illustration".

**Narration.** None, for 25 seconds.

**Sound.** Music only. The motif returns with the grainy texture from the cold open and builds a little with each layer.

### 4.7 · Where real heads look

`MEASURED` · 8:08–8:45

**Visual.** A dot chart from a real model: layers 1 to 12 across, one dot per head, with height showing the average distance in pixels over which that head gathers. In the early layers the dots spread from near zero to far. Deeper, they all rise. Tag: "Measured · google/vit-base-patch16-224 · mean attention distance per head (M3)".

**Narration.**

> So where do real heads look? We can measure how far, on average, each head reaches across the picture. Here's that measurement for a trained ViT-Base.
>
> In the first layer, some heads already take in much of the picture, while others stay close to home. Deeper in, most of them look wide.
>
> A convolutional network, the older standard for vision, is built to look locally first. ViT can look anywhere from its very first layer. Where it looks, it learns.

**Note.** The paper reports this for ViT-L, with 16 heads per layer (Fig. 7, right; App. D.7, Fig. 11). Confirm the description on M3 before recording.

---

## 5. Where the usefulness comes from

*The viewer's question: why would any of this become useful?*

### 5.1 · The class token

`ILLUSTRATION` · 8:45–9:20

**Visual.** An extra, blank vector slides in at the front of the row. It is the only vector with no tether. It joins the attention like everyone else. At the top of the stack, a small classifier reads it and lights up a score for each label.

**Narration.**

> Everything I've called "learned," the patch recipe, the position vectors, every matrix in every head of every layer, starts out random. So where does the usefulness come from?
>
> One more piece first. ViT adds an extra vector to the front of the line, one that belongs to no patch: the class token. It joins the attention like everyone else, so by the last layer it has gathered from the whole picture. A small classifier reads it and scores every label.

### 5.2 · Training

`ILLUSTRATION` · 9:20–9:57

**Visual.** A labeled photo goes in. Scores come out and are compared with the correct label. The gap appears as a magenta pulse that travels backward through the stack, and each module flickers as its numbers shift slightly. Then a fast flipbook of many different photos, the pulses blurring into a steady rhythm.

**Narration.**

> Now, training. Show the model a picture whose label we know. It produces its scores, and we measure how far they are from the right answer. That's the error.
>
> Then we trace the error backward through every step, and work out how each number in every matrix should shift to make it a little smaller. We shift them, just a little. Then again, with another picture. And again.
>
> Millions of pictures later, those numbers are no longer random.

**Sound.** A soft, low pulse for each backward pass. It speeds up into the flipbook.

### 5.3 · How much data

`ILLUSTRATION` · 9:57–10:27

**Visual.** Three stacks of photos of growing height, labeled 1.3 million, 14 million, and 303 million. Beside them, a schematic comparison: ViT a little behind the convolutional networks with the smallest stack, level with the middle one, and ahead with the largest. Caption: "Schematic. Results: paper, Figs. 3–4."

**Narration.**

> And ViT needed a lot of pictures. Trained on ImageNet's 1.3 million images alone, it came in a few points behind the convolutional networks of its day. With 14 million images, it caught up. With 300 million, it pulled ahead.
>
> The paper's own summary: large-scale training trumps inductive bias. A convolutional network comes with assumptions about images built in. ViT has to learn most of them from examples.

### 5.4 · Our table, through a real ViT

`MEASURED` · 10:27–11:03

**Visual.** Our final machine-view frame goes into the trained model. The top five labels and their scores appear. Tag: "Measured · google/vit-base-patch16-224 · top-5 on frame [frame id] (M4)".

**Narration.**

> Let's hand our table to a real, trained ViT and see what it says.
>
> *[The result goes on screen. Write this line after the run. Keep the result as it comes out, even if the top guess is wrong or odd.]*
>
> Notice how narrow the answer is. The picture holds a cup, a ball, a board, and a table. The model was trained to pick one label out of a thousand, so that's what it does. It can't tell us where the ball is, or what happens when it rolls.

**Note.** The timing reserves about five seconds for the result line.

### 5.5 · The boundary

`NARRATIVE` · 11:03–11:24

**Narration.**

> That's a line worth keeping clear. The architecture gives the model a way to move information around. Training decides what it actually learns. This model was trained to name things, so naming is what it does. On its own, it is not a model of how the world works.

---

## Ending

### 6.1 · The vectors that stay

`NARRATIVE` · 11:24–12:00

**Visual.** The labels fade. The 196 output vectors remain, each still on its tether. They lift and drift toward the other side of the frame, where a language model is writing a sentence one piece at a time. Last shot: the machine's camera on its stand, looking at the table.

**Narration.**

> But look at what's left when we take the label away. Every patch now carries a vector shaped by the whole picture.
>
> What those vectors mean depends on what they were trained for, and these were trained to pick one label from a list. Nothing has trained them to work with sentences.
>
> The picture is now a set of vectors. Next time, we'll try to make those vectors part of a sentence.

**End card.** Next · Episode 2: Giving Language Eyes

**Sound.** The motif, answered by a second voice in a new timbre: a first hint of language.

**Note.** Do not call these vectors "visual words" that a language model can already read. How vision gets tied to language (CLIP) opens Episode 2.

---

## Measurements

Every `MEASURED` shot comes from a script run on the public checkpoint. Keep the script, the checkpoint revision, the inputs, and the output file in the repository next to the episode.

| ID | Beat | What to compute | Method | Status |
|---|---|---|---|---|
| M1 | 2.3 | The main patterns of the patch-embedding matrix **E**, shown as RGB tiles | Principal components of the 768 learned filters, each reshaped to 16×16×3 (as in paper Fig. 7, left) | To do |
| M2 | 3.3 | Cosine similarity between each patch position embedding and all the others, on the 14×14 grid (class token left out) | As in paper Fig. 7, center | To do |
| M3 | 4.7 | Mean attention distance for each head in each layer | Distance in pixels from the query patch to every other patch, weighted by attention, averaged over a fixed image set. The paper used 128 images (App. D.7, Fig. 11). Record the image set with the result. | To do |
| M4 | 5.4 | Top-5 labels and probabilities on our final machine-view frame | The checkpoint's own preprocessing (resize to 224×224, normalize) | To do, after the frame is locked |

---

## Claims and sources

| Claim as narrated | Beat | Source |
|---|---|---|
| 224×224 input: 50,176 pixels, 150,528 numbers | 1.1 | Arithmetic; input size from [3] |
| ViT was introduced in 2020 by researchers at Google | 1.2 | [1] (arXiv, October 2020; Google Research, Brain Team) |
| A Transformer takes a sequence of vectors and lets every position gather from every other | 1.2 | [2] |
| 16×16 patches: a 14×14 grid, 196 patches, in reading (raster) order | 2.1 | [1] §3.1; raster order stated in App. D.4 |
| Paper title: "An Image is Worth 16x16 Words" | 2.1 | [1] |
| A flattened patch has 16 × 16 × 3 = 768 numbers; one trainable linear projection **E**, shared by all patches, maps it to an embedding | 2.2 | [1] §3.1, Eq. 1 |
| ViT-L/16 maps the 768 numbers to 1,024 | 2.2 note | [1] Table 1 (ViT-Large hidden size 1024) |
| The main components of the learned filters look like simple basis patterns for fine detail in a patch | 2.3 | [1] §4.5, Fig. 7 (left); to confirm with M1 |
| Without position information, attention treats its inputs as a set: shuffling the patches leaves the class-token output unchanged | 3.1 | Follows from the attention equations in [1] App. A (permutation equivariance), with a class-token readout |
| Learned 1D position embeddings are added to the patch embeddings; at initialization they carry no 2D information, and spatial relations must be learned | 3.2 | [1] §3.1 ("Inductive bias") |
| In a trained model, nearby positions have similar embeddings, and rows and columns show structure | 3.3 | [1] §4.5, Fig. 7 (center); to confirm with M2 |
| No position embedding: 0.61382; learned 1D: 0.64206 (ViT-B/16, ImageNet 5-shot linear) | 3.4 | [1] App. D.4, Table 8 |
| Query, key, and value come from learned projections; weights = softmax(q·kᵀ/√D_h); the output is a weighted sum of values | 4.2–4.4 | [1] App. A, Eq. 5–7; [2] §3.2 |
| The √d scaling keeps dot products from growing too large | 4.3 | [2] §3.2.1 |
| The attention result is added to the vector (residual connection) | 4.4 | [1] §3.1, Eq. 2 |
| ViT-Base: 12 layers, 12 heads, hidden size 768, MLP size 3072, 86M parameters | 4.5 | [1] Table 1 |
| Each block: attention, then a two-layer MLP with GELU; LayerNorm before each block | 4.5 | [1] §3.1 |
| Attention distance varies widely across heads in low layers and grows with depth; most heads attend widely in the second half | 4.7 | [1] §4.5, Fig. 7 (right), App. D.7; to confirm with M3 |
| CNNs build in locality; in ViT only the MLP layers are local, and self-attention is global | 4.7, 5.3 | [1] §3.1 ("Inductive bias") |
| A learnable class token is prepended; its final state is read by the classification head | 5.1 | [1] §3.1, Eq. 4 |
| On ImageNet (1.3M images) without strong regularization, ViT is a few points below comparable ResNets; with ImageNet-21k (14M) it catches up, and with JFT (303M) it pulls ahead | 5.3 | [1] §1, §4.1 (datasets), §4.3, Figs. 3–4, Table 2 caption |
| "Large scale training trumps inductive bias" | 5.3 | [1] §1 |
| The checkpoint outputs one of 1,000 ImageNet labels | 5.4 | [3] |

---

## Production notes

- **Scale.** Grids are drawn at the real 14×14. Vectors are drawn with 8 cells, and the first vector on screen carries a caption with the real size.
- **Tethers.** Every vector stays tied to its patch on screen. The class token is the only vector without a tether, and that is how the viewer recognizes it.
- **Illustration and measurement look different.** Measured charts get their own frame style and a tag that names the checkpoint, the layer or head, and the method. Illustrations never borrow that look.
- **No invented meanings.** No vector dimension is labeled with a meaning such as "cup-handle neuron," in any shot.
- **Math on screen matches the narration.** Only softmax(q · k / √d) appears. LayerNorm, the MLP's internals, and the output projection of multi-head attention stay in these notes.
- **Sequence length.** The real sequence has 197 positions: 196 patches plus the class token.

## References

1. A. Dosovitskiy et al. "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale." ICLR 2021. [arXiv:2010.11929](https://arxiv.org/abs/2010.11929)
2. A. Vaswani et al. "Attention Is All You Need." NeurIPS 2017. [arXiv:1706.03762](https://arxiv.org/abs/1706.03762)
3. `google/vit-base-patch16-224`, model card and config. [Hugging Face](https://huggingface.co/google/vit-base-patch16-224)
