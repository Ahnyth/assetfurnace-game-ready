# Game-ready (AssetFurnace add-on)

Takes what AssetFurnace makes the last step into a game: a rigged figure or a finished prop goes in, a file an engine
takes as it is comes out.

![Two figures made game-ready by this add-on, in their idle in Unity](pictures/game-ready.jpg)

## Make a figure game-ready

Give it the GLB from Rig (or Animate). It writes one GLB with:

- **one material and one atlas** (512 to 4096 px), where no texel is painted twice, the colour baked from the
  figure's own textures, the normal map's detail kept as soft light from above, so no normal map is needed; the
  **face gets as much of the atlas as its paint holds** (up to four times the body's texels across), never more,
  and only the face: hair, a ponytail or a hat keep the body's share, so a long ponytail cannot starve the body;
- **the triangle count you pick** (8,000 to 30,000 for phones, 50,000 with a 4096 atlas for a PC game: above that a
  figure's shape stops gaining, since the generator's own detail is the limit; or as rigged), with the **hidden inner
  wall dropped** first:
  Pixal3D leaves a second surface inside a figure that nobody sees, and dropping it gives the budget to what is
  seen. The drop is **checked in motion**: the figure is posed in a run, a dodge, a fall and a reach and seen from
  twelve sides, and any dropped face that would show as a hole is put back; an edge that can be seen from outside
  is never opened (since 0.1.8: where hair goes up into a hat's brim, the brim's underside stays closed);
- **real height** with the feet on the floor; a **sole the generator made up** below the pictures' feet (it finds
  the Finish run in the rig's licence record) is cut off, and thin plates of it the cut leaves in front of the toe
  (under 6.5 mm on a 1.85 m figure) are cleared and the toe closed, while the boot's own toe stays (a heel only a
  little too high is pressed flat instead);
- **engine bone names** (Unity's Humanoid or Mixamo, or the rig's own), finger bones kept or folded into the hands,
  at most four bones per vertex;
- optional **glow** on thin lines of the colours you name (`#29e6ff`), never on the face or the hands; what counts as
  a thin line is judged in centimetres, so a figure glows the same however much of the atlas its face takes; at most
  8 % of the figure glows (since 0.1.11: a knight's eye-slit red also matched his dark red cape faintly and lit a
  quarter of him; past 8 % the glow is narrowed, and dropped if it stays past it); **Glow where: eyes only** keeps the
  glow on the head alone, for eyes whose colour the body shares (since 0.1.12 only skin plainly the head's, not a neck
  it shares);
- a **look**: `clean` (the default since 0.1.7), which mirrors a fifth of a bright room's light, so a dark coat stays
  dark and colours stay full in engines and viewers that light with a bright environment, or `stylized`, the usual
  material, whose sheen lifted a figure's darkest tones from 7 to 29 of 255 and halved its colour;
- the colour **baked from the finer model** it names, never from the back of a surface (since 0.1.9: round a neck in a
  high collar the rays started behind the collar's inside and painted its dark under the chin; each texel now takes
  the longest of three ray starts that meets a surface facing it, or keeps its own paint), nor from another layer
  standing off it (since 0.1.10: a collar's flap a centimetre out lay inside the longest start and drew thin dark
  strokes along a wizard's jaw; where the longest ray's paint is far from the figure's own, a shorter start that
  agrees with it wins);
- a **colour check** at the end: the finished figure against the model its colour came from, from eight sides; a
  patch that differs is a bake fault, named in `<run>.report.json` and marked in `<run>.colour.png`.

## Make a prop game-ready

Give it a finished prop (Finish's GLB). It turns its front to +Z (glTF's and Unity's forward), scales it to its real
height, length or width, puts the pivot at the bottom centre, and writes LODs (each baked from LOD0, maps
compressed) and a box or convex-hull collider beside it (the hull built on Blender 5.2 again since 0.1.10), with `<run>.prop.json` saying what it did. The result is
LOD0.

## What it does on your machine

- Runs entirely on your machine; no network, nothing downloaded, no models used.
- Starts Blender (4.2 or newer) as AssetFurnace's add-on runner asks. From it, it starts **AssetFurnace's own Python**
  (the install's `.venv`, where numpy, Pillow and SciPy already are; set `I2L_PYTHON` to use another) to run
  `scripts/game_ready.py` or `scripts/prop_ready.py`, which start one more headless Blender for the mesh work.
- Reads only the model you give it and, for a figure, the Finish run its licence record names; writes only into the
  run folder AssetFurnace gives it.

## Use

In the studio: Add-ons, Game-ready. From the command line:

    ./lab addon add --unlisted https://github.com/Ahnyth/assetfurnace-game-ready@<commit>
    ./lab addon run game-ready figure --input model=output/animate/<run>/<name>_rigged.glb \
        --input height=1.8 --input triangles=14000 --input atlas=1024 --input bones=unity \
        --input fingers=keep --input glow=none --input look=clean
    ./lab addon run game-ready prop --input model=output/finish/<run>/<name>_5k.glb --input front=+z \
        --input axis=height --input size=0.8 --input lods=2500,1000 --input collider=box

The entry is tested without Blender: `python -m pytest tests`. The scripts in `scripts/` come from the branch
[`feat/game-ready`](https://github.com/Ahnyth/image-to-3dlab/tree/feat/game-ready) of my AssetFurnace fork, where
their own tests live; `extra/` holds the two checks the core does not ship yet (the colour comparison and the
outline check of [image-to-3dlab#292](https://github.com/Bingeljell/image-to-3dlab/pull/292)).

It has built 29 of the figures in a small mobile game made with AssetFurnace.

Licence: Apache-2.0 (see `LICENSE` and `NOTICE`: the scripts build on [image-to-3dlab](https://github.com/Bingeljell/image-to-3dlab), AssetFurnace itself).
