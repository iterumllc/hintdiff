hintdiff
========

A modest browser-based tool for viewing differences in the hinting of
two fonts (which are assumed to have the same set of glyphs and
equivalent outline data in those glyphs).

To start using hintdiff first install the contents of this pythoh package (e.g.
with `pip install .`),

Then run `hintdiff` from the command line as described below and open
`https://127.0.0.1:5000` in a browser window. Differences are scored by
mean-square-difference between pixel intensity at each requested character
point size. Then glyphs are sorted by decreasing max score, where each
glyph that is at all different is displayed with its name, image, the
difference image for the highest scored point size, whether the stems and/or
body of the CharStrings are different, and all the scores.

Clicking on a glyph name will open a more detailed report with all generated
images and differences magnified. The magnification can be adjusted with
the slider. Pressing "View Differences" will open a dialog displaying a
2-up difference map of the CharStrings (as decoded by fontTools `ttx`).

Usage message:

```
usage: hintdiff.py [-h] [-m MAG] [-d DIFFMAG] [-c CHARSIZES [CHARSIZES ...]]
                   [-l LABELSIZE] [-r {fg,fm,b,b1,b5,b8,b4}] [-a] [-o]
                   ref_font mod_font

Show differences in hinted font files

positional arguments:
  ref_font              reference font
  mod_font              modified font

optional arguments:
  -h, --help            show this help message and exit
  -m MAG, --mag MAG     Default enlargement of pixel aps and difference maps
                        in the glyph report
  -d DIFFMAG, --diffmag DIFFMAG
                        Default enlargement of pixel aps and difference maps
                        in the glyph report
  -c CHARSIZES [CHARSIZES ...], --charsizes CHARSIZES [CHARSIZES ...]
                        List of integer point sizes to compare between fonts
  -l LABELSIZE, --labelsize LABELSIZE
                        Point size of the large glyph images displayed in the
                        main window
  -r {fg,fm,b,b1,b5,b8,b4}, --rendermode {fg,fm,b,b1,b5,b8,b4}
                        Modes: fg is RreeType grascale; fm is FreeType
                        monochome; b, b1, b5, b8, b4 are buildChar 1x1, 6x1,
                        6x5, 8x1, 4x4
  -a, --buildchar       Render with Adobe buildChar (implies monochrome)
  -o, --open            Open browser window after starting
```

The buildChar options will only be available when the `adobebc` package
is installed; otherwise the program will stop with an `ImportError`
exception.

When using `--open` the window will likely start out with an error (and may
remain that way before reloading manually).

Note that this tool intentionally runs a Flask server in development mode.  The
code current requires a single server as the state is stored in one class
variable.
