# op-img

![The McLaren photo cycling through seam-carve, channel-swap, polar, pixel-sort, invert-lightness, wrong-stride and fold, each layered over the last](assets/op-img-hero.avif)

op-img is a composable image manipulation CLI:

```bash
op <patch> <input> [--args]
```

## Quick start

Clone the repository:

```bash
git clone https://github.com/service-dept/op-img.git
cd op-img
```

Install the requirements:

- [ImageMagick](https://imagemagick.org/) for the shell patches: `brew install imagemagick`
- [Python 3](https://www.python.org/) with Pillow, numpy and scipy for the Python patches: `pip3 install Pillow numpy scipy`

Add `op` to your PATH (one-time setup, from the `op-img` folder):

```bash
ln -s "$(pwd)/op" /usr/local/bin/op
```

Use it from anywhere on your machine:

```bash
op                                                       # show usage and three patches at random
op bit-crush photo.jpg                                   # default 1-bit crush
op pixel-sort photo.jpg                                  # no output given: saves photo-psort.jpg next to photo.jpg
op dot-halftone photo.jpg out.png --spacing 8            # halftone dots 8 px apart, saved as out.png
op closest-palette photo.jpg --palette "#000,#fff,#f00"  # snap every pixel to black, white or red
```

The input comes first, then an optional output. Omit the output to save the result next to the input with the patch's suffix.

## Stacking patches

Join patches with `+` to run them one after another, each one building on the previous result:

```bash
op <patch> <input> [output] [--args] + <patch> [--args] + ...
```

```bash
op pixel-sort photo.jpg + fold + polar            # writes photo-psort-fold-polar.png
op pixel-sort photo.jpg --by hue + channel-swap   # options follow the patch they belong to
op seam-carve photo.jpg out.jpg + thermal         # an output after the input names the final file
```

The input, and the output if you give one, come right after the first patch. Subsequent patches only take arguments. Omit the output path to save the result in the same directory as the input, with each patch's suffix applied in order.

### contour + swirl

Contour traces the photo's brightness bands in pink lines, and swirl twists them into a vortex.

```bash
op contour photo.jpg + swirl
```

![contour + swirl](patches/contour/stack-contour-swirl.jpg)

### fold + polar + pixel-sort + channel-swap

Fold mirrors the car, polar wraps it into an arch, pixel-sort streaks it, and channel-swap turns the orange blue.

```bash
op fold photo.jpg + polar --center 0.3,0.5 --rotate 200 --radius 0.9 + pixel-sort + channel-swap
```

![fold + polar + pixel-sort + channel-swap](patches/fold/stack-fold-polar-pixel-sort-channel-swap.jpg)

### thermal + invert-lightness

Heat colors first, then the lightness flipped, which turns the car magenta and pink.

```bash
op thermal photo.jpg + invert-lightness
```

![thermal + invert-lightness](patches/thermal/stack-thermal-invert-lightness.jpg)

### invert-lightness + thermal

The same two patches the other way round: with the lightness flipped first, the paint reads cold and the tires and grass run white-hot.

```bash
op invert-lightness photo.jpg + thermal
```

![invert-lightness + thermal](patches/invert-lightness/stack-invert-lightness-thermal.jpg)

### slit-scan + thermal

Slit-scan melts the car into curves, and thermal paints them in heat colors.

```bash
op slit-scan photo.jpg + thermal
```

![slit-scan + thermal](patches/slit-scan/stack-slit-scan-thermal.jpg)

### polar + drip + polar

Drips run straight down in polar space, so they come back as rays bursting from an off-center pole.

```bash
op polar photo.jpg --center 0.62,0.4 --rotate 150 --radius 0.85 + drip --length 500 --threshold 120 + polar --mode from-polar --center 0.62,0.4 --rotate 150 --radius 0.85
```

![polar + drip + polar](patches/polar/stack-polar-drip-polar.jpg)

### polar + tile-shuffle + polar

Tiles shuffled in polar space come back as rings of turned wedges.

```bash
op polar photo.jpg + tile-shuffle --grid 8 + polar --mode from-polar
```

![polar + tile-shuffle + polar](patches/polar/stack-polar-tile-shuffle-polar.jpg)

### dither + zoom-blur

Atkinson dithering, then a zoom blur that smears the dots into speed streaks.

```bash
op dither photo.jpg --method atkinson + zoom-blur
```

![dither + zoom-blur](patches/dither/stack-dither-zoom-blur.jpg)

### kaleidoscope + ascii

A kaleidoscope emblem, redrawn in characters.

```bash
op kaleidoscope photo.jpg + ascii
```

![kaleidoscope + ascii](patches/kaleidoscope/stack-kaleidoscope-ascii.jpg)

### scan-glitch + polar

Scan-glitch's torn rows, wrapped into arches around a shifted pole.

```bash
op scan-glitch photo.jpg + polar --center 0.72,0.3 --rotate 105 --radius 0.7
```

![scan-glitch + polar](patches/scan-glitch/stack-scan-glitch-polar.jpg)

### swirl + kaleidoscope

A swirl, mirrored into a chrome mandala.

```bash
op swirl photo.jpg + kaleidoscope
```

![swirl + kaleidoscope](patches/swirl/stack-swirl-kaleidoscope.jpg)

### res-crush + zoom-blur

Big pixels, then a zoom blur that streaks them outward.

```bash
op res-crush photo.jpg --size 32 + zoom-blur
```

![res-crush + zoom-blur](patches/res-crush/stack-res-crush-zoom-blur.jpg)

### bit-crush + flow-streak

A 1-bit crush, brushed back into painterly strokes.

```bash
op bit-crush photo.jpg --bits 1 + flow-streak
```

![bit-crush + flow-streak](patches/bit-crush/stack-bit-crush-flow-streak.jpg)

### channel-offset + swirl

Split color channels, twisted into a swirl.

```bash
op channel-offset photo.jpg --r 140,50 --g -20,40 --b -120,-40 + swirl
```

![channel-offset + swirl](patches/channel-offset/stack-channel-offset-swirl.jpg)

### pixel-sort + drip + invert-lightness

Columns sorted, bright pixels dripping upward, then the lightness flipped.

```bash
op pixel-sort photo.jpg --direction column + drip --length 500 --threshold 120 --direction up + invert-lightness
```

![pixel-sort + drip + invert-lightness](patches/pixel-sort/stack-pixel-sort-drip-invert-lightness.jpg)

## Adding a patch

A patch is a directory in `patches/`, named after the patch. It holds either a Python script with its `requirements.txt`, or a shell script. `op` finds patches by name, so there's nothing to register. A missing input prints `Error: file not found`. Its own tests go in `tests/test_<name>.py`. The name goes in `ALL_PATCHES` in `tests/test_op_cli.py`, and its default output name in `DEFAULT_NAMES` in `tests/test_conventions.py`, which checks the shared conventions for every patch.

## Patches

All examples below use this image as input:

![default input](assets/mclaren.jpg)

### bit-crush

Reduce color depth by posterizing to N bits per channel.

```bash
./patches/bit-crush/bit-crush.sh <input> [output] [--bits N]
```

Default: `--bits 1` (2 levels per channel, 8 colors)

![bit-crush example](patches/bit-crush/example.jpg)

### res-crush

Downscale to a tiny resolution and upscale back with nearest-neighbor for a chunky pixel look.

```bash
./patches/res-crush/res-crush.sh <input> [output] [--size N]
```

Default: `--size 64`

![res-crush example](patches/res-crush/example.jpg)

### channel-offset

Shift R, G, B channels by independent pixel amounts for a misregistered print / chromatic aberration look.

```bash
./patches/channel-offset/channel-offset.sh <input> [output] [--r X,Y] [--g X,Y] [--b X,Y]
```

Default: `--r 140,50 --g -20,40 --b -120,-40`

![channel-offset example](patches/channel-offset/example.jpg)

### fold

Mirror or repeat one half of the image across a fold line.

```bash
./patches/fold/fold.sh <input> [output] [--axis x|y] [--position N] [--mode mirror|repeat]
```

![fold example](patches/fold/example.jpg)

### pixel-sort

Sort contiguous runs of pixels by brightness, hue, or saturation.

```bash
python3 ./patches/pixel-sort/pixel-sort.py <input> [output] [--by brightness|hue|saturation] [--threshold N] [--direction row|column]
```

Default: `--threshold 200`

![pixel-sort example](patches/pixel-sort/example.jpg)

### scan-glitch

Randomly shift horizontal slices of the image for a broken-signal effect.

```bash
python3 ./patches/scan-glitch/scan-glitch.py <input> [output] [--severity N] [--seed N]
```

![scan-glitch example](patches/scan-glitch/example.jpg)

### echo

Composite the image on itself with offset and fade for a ghosting/echo effect.

```bash
python3 ./patches/echo/echo.py <input> [output] [--count N] [--offset-x N] [--offset-y N] [--decay N] [--blend additive|screen|multiply]
```

Default: `--count 12 --offset-x 30 --offset-y 12 --decay 0.6 --blend additive`

![echo example](patches/echo/example.jpg)

### kaleidoscope

Extract a wedge from the image and mirror/rotate it around the center for a kaleidoscope effect.

```bash
python3 ./patches/kaleidoscope/kaleidoscope.py <input> [output] [--segments N] [--angle N]
```

Default: `--segments 6 --angle 90`

![kaleidoscope example](patches/kaleidoscope/example.jpg)

### polar

Remap image between Cartesian and polar coordinates. `--center` moves the pole, `--rotate` turns where the seam falls, and `--radius` sets how far out the rings reach. Use the same values for `to-polar` and `from-polar` to map back.

```bash
python3 ./patches/polar/polar.py <input> [output] [--mode to-polar|from-polar] [--center X,Y] [--rotate DEG] [--radius N]
```

Default: `--mode to-polar --center 0.5,0.5 --rotate 0 --radius 1`

![polar example](patches/polar/example.jpg)

### raw-bend

Treat pixel data as a raw audio signal and apply echo, chorus, and bitcrush distortion.

```bash
python3 ./patches/raw-bend/raw-bend.py <input> [output] [--echo-strength N] [--echo-delay N] [--chorus N] [--bitcrush N]
```

Default: `--echo-strength 0.8 --echo-delay 2000 --chorus 0.7 --bitcrush 0`

![raw-bend example](patches/raw-bend/example.jpg)

### seam-carve

Content-aware image resizing by removing low-energy vertical seams.

```bash
python3 ./patches/seam-carve/seam-carve.py <input> [output] [--percent N] [--energy gradient|sobel]
```

Default: `--percent 35 --energy sobel`

![seam-carve example](patches/seam-carve/example.jpg)

### slit-scan

Take one column from each rotation of the image and stitch them together for a slit-scan effect.

```bash
python3 ./patches/slit-scan/slit-scan.py <input> [output] [--slits N] [--max-angle N]
```

Default: `--slits <width> --max-angle 180`

![slit-scan example](patches/slit-scan/example.jpg)

### tile-shuffle

Chop the image into an NxN grid and randomly permute the tiles.

```bash
python3 ./patches/tile-shuffle/tile-shuffle.py <input> [output] [--grid N] [--seed N]
```

Default: `--grid 8`

![tile-shuffle example](patches/tile-shuffle/example.jpg)

### wrong-stride

Flatten the pixel buffer and reshape with a wrong row width for a diagonal shear glitch.

```bash
python3 ./patches/wrong-stride/wrong-stride.py <input> [output] [--offset N]
```

Default: `--offset 1`

![wrong-stride example](patches/wrong-stride/example.jpg)

### fft-phase

Keep each channel's Fourier magnitude and blend in random phase, so the image dissolves into a texture with the same spectrum.

```bash
python3 ./patches/fft-phase/fft-phase.py <input> [output] [--amount N] [--seed N]
```

Default: `--amount 0.35`

![fft-phase example](patches/fft-phase/example.jpg)

### zoom-blur

Average copies of the image scaled up about a center point, for radial warp-speed streaks.

```bash
python3 ./patches/zoom-blur/zoom-blur.py <input> [output] [--amount N] [--center X,Y] [--samples N]
```

Default: `--amount 0.3 --center 0.5,0.5 --samples 32`

![zoom-blur example](patches/zoom-blur/example.jpg)

### swirl

Twist the image around a center, with the rotation fading out toward a radius.

```bash
python3 ./patches/swirl/swirl.py <input> [output] [--angle DEG] [--radius N] [--center X,Y]
```

Default: `--angle 360 --radius 1.0 --center 0.5,0.5`

![swirl example](patches/swirl/example.jpg)

### displace

Move each pixel along an angle by an amount taken from its own blurred brightness, so light and dark areas tear apart in opposite directions.

```bash
python3 ./patches/displace/displace.py <input> [output] [--amount PX] [--angle DEG] [--blur N]
```

Default: `--amount 150 --angle 0 --blur 3`

![displace example](patches/displace/example.jpg)

### drip

Bleed bright pixels in one direction with a fading tail, like wet paint running.

```bash
python3 ./patches/drip/drip.py <input> [output] [--length PX] [--threshold N] [--direction down|up|left|right]
```

Default: `--length 500 --threshold 120 --direction down`

![drip example](patches/drip/example.jpg)

### edge-glow

Turn edges into neon lines in each pixel's own hue, with a soft halo, over a darkened base.

```bash
python3 ./patches/edge-glow/edge-glow.py <input> [output] [--amount N] [--radius N]
```

Default: `--amount 1 --radius 6`

![edge-glow example](patches/edge-glow/example.jpg)

### contour

Draw lines where brightness crosses N levels, like a topographic map of the photo. Pink lines on black by default.

```bash
python3 ./patches/contour/contour.py <input> [output] [--levels N] [--blur N] [--width PX] [--color HEX] [--amount N]
```

Default: `--levels 16 --blur 2 --width 1 --color #ec4899 --amount 1`

![contour example](patches/contour/example.jpg)

### bloom

Pull out the highlights, blur them at three radii and screen them back for a soft glow.

```bash
python3 ./patches/bloom/bloom.py <input> [output] [--amount N] [--threshold N] [--radius N]
```

Default: `--amount 2 --threshold 110 --radius 16`

![bloom example](patches/bloom/example.jpg)

### voronoi-mosaic

Split the image into irregular Voronoi cells filled with their average color, with optional dark leading like stained glass.

```bash
python3 ./patches/voronoi-mosaic/voronoi-mosaic.py <input> [output] [--size PX] [--jitter N] [--edges PX] [--seed N]
```

Default: `--size 24 --jitter 1 --edges 0`

![voronoi-mosaic example](patches/voronoi-mosaic/example.jpg)

### oil-paint

Kuwahara filter: smooth into flat painterly patches while keeping edges crisp.

```bash
python3 ./patches/oil-paint/oil-paint.py <input> [output] [--radius N]
```

Default: `--radius 6`

![oil-paint example](patches/oil-paint/example.jpg)

### tilt-shift

Blur away from a horizontal focus band and lift the color, so the scene looks like a miniature.

```bash
python3 ./patches/tilt-shift/tilt-shift.py <input> [output] [--blur N] [--focus N] [--band N]
```

Default: `--blur 10 --focus 0.62 --band 0.25`

![tilt-shift example](patches/tilt-shift/example.jpg)

### flow-streak

Smear the image along its own contours for brushed, combed strokes.

```bash
python3 ./patches/flow-streak/flow-streak.py <input> [output] [--length N] [--sigma N]
```

Default: `--length 36 --sigma 6`

![flow-streak example](patches/flow-streak/example.jpg)

### dither

Dither to N levels per channel with a Bayer matrix, or with Floyd–Steinberg or Atkinson error diffusion. Error diffusion takes a few seconds on the README image.

```bash
python3 ./patches/dither/dither.py <input> [output] [--method bayer|floyd|atkinson] [--levels N] [--matrix 2|4|8]
```

Default: `--method bayer --levels 2 --matrix 8`

![dither example](patches/dither/example.jpg)

### jpeg-rot

Re-save as a low-quality JPEG many times, shifting a pixel each time so the damage piles up instead of settling.

```bash
python3 ./patches/jpeg-rot/jpeg-rot.py <input> [output] [--quality N] [--generations N]
```

Default: `--quality 5 --generations 80`

![jpeg-rot example](patches/jpeg-rot/example.jpg)

### ascii

Replace each cell with a bold character chosen by brightness, stretched to the image's own range, drawn in the cell's hue on black.

```bash
python3 ./patches/ascii/ascii.py <input> [output] [--cell PX] [--charset CHARS]
```

Default: `--cell 10 --charset " .:-=+*#%@"`

![ascii example](patches/ascii/example.jpg)

### isolate-threshold

Extract dark pixels from an image with a transparent background. Optionally recolor them and upscale with nearest-neighbor.

```bash
./patches/isolate-threshold/isolate-threshold.sh <input> [output] [--scale N] [--threshold N] [--color "#hex"]
```

Default: `--scale 1 --threshold 50 --color "#ff0000"`

![isolate-threshold example](patches/isolate-threshold/example.jpg)

### closest-palette

Snap every pixel to its nearest color in a given palette. No dithering -- hard color boundaries.

```bash
python3 ./patches/closest-palette/closest-palette.py <input> [output] --palette "#hex,#hex,..."
python3 ./patches/closest-palette/closest-palette.py <input> [output] --from-image ref.png --colors N
```

![closest-palette example](patches/closest-palette/example.jpg)

### invert-lightness

Invert the lightness channel in LAB color space — dark becomes light and vice versa, while hue and saturation are preserved.

```bash
python3 ./patches/invert-lightness/invert-lightness.py <input> [output]
```

![invert-lightness example](patches/invert-lightness/example.jpg)

### posterize-hsv

Quantize HSV channels independently for a posterized look with hue control.

```bash
python3 ./patches/posterize-hsv/posterize-hsv.py <input> [output] [--h-levels N] [--s-levels N] [--v-levels N]
```

Default: `--h-levels 8 --s-levels 4 --v-levels 4`

![posterize-hsv example](patches/posterize-hsv/example.jpg)

### thermal

Map brightness to a false-color thermal palette (black to blue to red to yellow to white).

```bash
python3 ./patches/thermal/thermal.py <input> [output]
```

![thermal example](patches/thermal/example.jpg)

### hue-isolate

Keep one hue band in full color and turn everything else gray.

```bash
python3 ./patches/hue-isolate/hue-isolate.py <input> [output] [--hue DEG] [--width DEG] [--amount N]
```

Default: `--hue 25 --width 20 --amount 1` (orange)

![hue-isolate example](patches/hue-isolate/example.jpg)

### channel-swap

Rearrange RGB channels — swap, duplicate, or reorder color channels.

```bash
python3 ./patches/channel-swap/channel-swap.py <input> [output] [--map B,G,R]
```

Default: `--map B,G,R` (swaps red and blue)

![channel-swap example](patches/channel-swap/example.jpg)

### recolor

Repaint the image's most prevalent colors with the colors you give, most prevalent first, keeping their light and shade. Grays, black and white are left alone.

```bash
python3 ./patches/recolor/recolor.py <input> [output] [--colors C1,C2] [--amount N] [--clusters N]
```

Default: `--colors "#1e3a8a,#facc15" --amount 1 --clusters 6`

![recolor example](patches/recolor/example.jpg)

### dot-halftone

Convert to a halftone dot grid where dot size varies with brightness. Pink dots on transparent background.

```bash
python3 ./patches/dot-halftone/dot-halftone.py <input> [output] [--spacing N] [--min-dot N] [--max-dot N] [--angle N]
```

![dot-halftone example](patches/dot-halftone/example.jpg)

### line-halftone

Variable-width lines whose thickness maps to brightness. Pink lines on transparent background.

```bash
python3 ./patches/line-halftone/line-halftone.py <input> [output] [--spacing N] [--min-width N] [--max-width N] [--angle N]
```

![line-halftone example](patches/line-halftone/example.jpg)

### cross-hatch

Multiple line-halftone passes at different angles, each gated by a brightness threshold. Darker areas get more layers of hatching. Pink lines on transparent background.

```bash
python3 ./patches/cross-hatch/cross-hatch.py <input> [output] [--layers N] [--spacing N] [--thresholds N,N,N]
```

![cross-hatch example](patches/cross-hatch/example.jpg)

### stipple

Random dot placement where density maps to brightness. Pink dots on transparent background.

```bash
python3 ./patches/stipple/stipple.py <input> [output] [--dots N] [--dot-size N] [--seed N]
```

![stipple example](patches/stipple/example.jpg)
