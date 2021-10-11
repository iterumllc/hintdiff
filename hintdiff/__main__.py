import sys
import argparse
import webbrowser
from hintdiff import app, diffState

def main():
    desc = "Show differences in hinted font files"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("-m", '--mag', type=int, default=8, help="Default enlargement of pixel aps and difference maps in the glyph report")
    parser.add_argument("-d", '--diffmag', type=int, default=8, help="Default enlargement of pixel aps and difference maps in the glyph report")
    parser.add_argument("-c", "--charsizes", type=int, nargs="+", default=[8,10,12,14,16,20], help="List of integer point sizes to compare between fonts")
    parser.add_argument('-l', '--labelsize', type=int, default=70, help="Point size of the large glyph images displayed in the main window")
    parser.add_argument('-o', '--open', action='store_true', help="Open browser window after starting")
    parser.add_argument('ref_font', help='reference font')
    parser.add_argument('mod_font', help='modified font')

    args = parser.parse_args()

    diffState.init(args.ref_font, args.mod_font, mag=args.mag,
                   diffmag=args.diffmag, labelsize=args.labelsize,
                   charsizes=args.charsizes)
    if args.open:
        webbrowser.open('http://127.0.0.1:5000')
    app.run(debug=False)

if __name__ == '__main__':
    main()
