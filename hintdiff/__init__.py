import sys
import numpy as np
from io import BytesIO
from difflib import HtmlDiff

from flask import Flask, render_template, make_response, abort, send_from_directory

from fontTools.ttLib import TTFont
from fontTools.misc.xmlWriter import XMLWriter

import freetype

from PIL import Image, ImageOps, ImageChops


htmldiff = HtmlDiff(tabsize=2, wrapcolumn=50)
labelsize = 67

class FFace:
    def __init__(self, fname):
        self.ttfont = TTFont(fname)
        self.ftfont = freetype.Face(fname)
        self.CFF().decompileAllCharStrings()
    
    def CFF(self):
        return self.ttfont['CFF '].cff[0]

class diffState:
    theState = None

    @classmethod
    def init(cls, *args, **kwargs):
        cls.theState = cls(*args, **kwargs)

    def __init__(self, rface, mface, labelsize, mag, diffmag, charsizes):
        self.rface = FFace(rface)
        self.mface = FFace(mface)
        self.labelsize = labelsize
        self.charsizes = charsizes
        self.mag = mag
        self.diffmag = diffmag

        self.buildDiffData(self.mface.ttfont.getGlyphOrder())
        self.buildImages()

    def buildDiffData(self, gnames):
        self.diffdata = diffdata = {}

        rcff = self.rface.CFF()
        mcff = self.mface.CFF()
        for gn in gnames:
            if gn == '.notdef':
                continue
            rcs = self.toCharString(rcff, gn)
            mcs = self.toCharString(mcff, gn)
            rh, rb = self.splitCS(rcs)
            mh, mb = self.splitCS(mcs)
            dd = {}
            if rh != mh:
                dd['stems'] = (rh, mh)
            if rb != mb:
                dd['body'] = (rb, mb)
            if dd:
                dd['cs'] = (rcs, mcs)
                diffdata[gn] = dd

    @staticmethod
    def toCharString(td, gn):
        writer = XMLWriter(BytesIO())
        writer.file.seek(0)
        writer.file.truncate()
        td.CharStrings[gn].toXML(writer)
        s = writer.file.getvalue().decode("utf-8")
        return s

    @staticmethod
    def splitCS(s):
        i = s.find('cntrmask')
        if i == -1:
            i = s.find('hintmask')
        if i != -1:
            return (s[0:i] + '\n', s[i:])
        i = s.find('vstem')
        if i == -1:
            i = s.find('hstem')
        if i != -1:
            i += 6
            return (s[0:i], s[i:])
        return (None, s)

    @staticmethod
    def weightedDiff(i1, i2):
        t1 = np.array(i1, dtype='int16')
        t2 = np.array(i2, dtype='int16')
        sd = t1 - t2
        c1 = np.array(np.fabs(np.fmin(sd, 0)), dtype='uint8')
        c2 = np.array(np.fmax(sd, 0), dtype='uint8')
        wm = np.fabs(sd)
        c3 = np.array(wm, dtype='uint8')
        weight = np.square(wm).mean()
        ic1 = Image.fromarray(c1, 'L')
        ic2 = Image.fromarray(c2, 'L')
        ic3 = Image.fromarray(c3, 'L')
        try:
            o = Image.merge('RGB', (ic1, ic3, ic2))
            return weight, o
        except:
            print(sys.exc_info()[0])
            return weight, i1

    def getImages(self, gname, cs):
        iinfo = []
        for fface in (self.rface, self.mface):
            face = fface.ftfont
            # gindex = face.get_name_index(gname.encode('ascii'))
            gindex = fface.ttfont.getGlyphID(gname)
            try:
                face.load_glyph(gindex)
                bitmap = face.glyph.bitmap
                offsets = (face.glyph.bitmap_left, face.glyph.bitmap_top)
                bitmap = np.array(bitmap.buffer,
                                  dtype=np.uint8).reshape((bitmap.rows,
                                                           bitmap.width))
                iinfo.append([bitmap, offsets])
            except:
                print("Couldn't generate " + gname + " at charsize " + str(cs))
                return (None, None)
        # Use the offsets to reshape the bitmaps to match each other,
        # adding leading or trailing zeros to the 2D arrays as needed
        i = 0 if iinfo[0][1][0] < iinfo[1][1][0] else 1
        d = iinfo[(i+1)%2][1][0] - iinfo[i][1][0]
        for _ in range(d):
            iinfo[i][0] = np.insert(iinfo[i][0], 0, 0, axis=1)
        i = 0 if iinfo[0][0].shape[1] < iinfo[1][0].shape[1] else 1
        d = iinfo[(i+1)%2][0].shape[1] - iinfo[i][0].shape[1]
        for _ in range(d):
            iinfo[i][0] = np.append(iinfo[i][0],
                                    np.zeros((iinfo[i][0].shape[0], 1),
                                             dtype='uint8'), axis=1)
        i = 0 if iinfo[0][1][1] < iinfo[1][1][1] else 1
        d = iinfo[(i+1)%2][1][1] - iinfo[i][1][1]
        for _ in range(d):
            iinfo[i][0] = np.insert(iinfo[i][0], 0, 0, axis=0)
        i = 0 if iinfo[0][0].shape[0] < iinfo[1][0].shape[0] else 1
        d = iinfo[(i+1)%2][0].shape[0] - iinfo[i][0].shape[0]
        for _ in range(d):
            iinfo[i][0] = np.append(iinfo[i][0],
                                    np.zeros((1, iinfo[i][0].shape[1]),
                                             dtype='uint8'), axis=0)
        try:
            return (Image.fromarray(iinfo[0][0]), Image.fromarray(iinfo[1][0]))
        except:
            print("Unexpected error:", sys.exc_info()[0])
            return (None, None)
    
    def buildImages(self):
        imgdata = {}
        for cs in (self.labelsize, *self.charsizes):
            self.rface.ftfont.set_char_size( cs*64 )
            self.mface.ftfont.set_char_size( cs*64 )
            for gn, gdd in self.diffdata.items():
                gimg = self.getImages(gn, cs)
                if cs == self.labelsize:
                    gdd['images'] = { 'label': gimg[1] }
                    continue
                if not gimg[0] or not gimg[1]:
                    continue
                weight, idiff = self.weightedDiff(gimg[0], gimg[1])
                if weight > 0:
                    wd = gdd.get('weights', None)
                    if not wd:
                        wd = gdd['weights'] = {}
                    wd[cs] = weight
                    imgs = gdd.get('images', None)
                    csimgs = imgs[cs] = {}
                    csimgs['Reference'] = gimg[0]
                    csimgs['Modified'] = gimg[1]
                    csimgs['Difference'] = idiff 

def maxWeight(item):
    gdd = item[1]
    wd = gdd.get('weights', None)
    if not wd:
        return -1
    w, s = max(((w, s) for s, w in wd.items()))
    gdd['worstsize'] = s
    gdd['images']['worst'] = gdd['images'][s]
    return w

def imgToPNGIO(cache, path, invert=True):
    cn = ' : '.join((str(s) for s in path))
    cached = cache.get(cn, None)
    if cached is not None:
        return cached
    l = diffState.theState.diffdata
    for ln in path:
        print(ln)
        l = l.get(ln, None)
        if l is None:
            return None
    img = l
    if invert:
        img = ImageOps.invert(img)
    buf = cache[cn] = BytesIO()
    img.save(buf, 'PNG')
    return buf

app = Flask(__name__)

imagecache = {}

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/hintdiff.js')
def serve_hdjs():
    ds = diffState.theState
    return render_template("hintdiff.js", mag = ds.mag, diffmag = ds.diffmag)

@app.route('/image/<gname>/<typ>')
@app.route('/image/<gname>/<typ>/<siz>')
def getLabel(gname, typ, siz=0):
    if gname is not None:
        img = None
        if typ == 'label':
            img = imgToPNGIO(imagecache, (gname, 'images', 'label'))
        elif typ == 'max_diff':
            img = imgToPNGIO(imagecache, (gname, 'images', 'worst', 'Difference'))
        else:
            img = imgToPNGIO(imagecache, (gname, 'images', int(siz), typ))
        if img:
            response = make_response(img.getvalue())
            response.headers.set('Content-Type', 'image/png')
            return response
    abort(404)

@app.route('/csdiff/<gname>')
def csdiff(gname):
    ds = diffState.theState
    gdd = ds.diffdata.get(gname, None)
    if not gdd:
        abort(404)
    cst = gdd['cs']
    dstr = htmldiff.make_table(cst[0].split('\n'), cst[1].split('\n'))
    return render_template('csdiff.html', gn=gname, csdiff=dstr)

@app.route('/report/<gname>')
def glyph_report(gname):
    ds = diffState.theState
    gdd = ds.diffdata.get(gname, None)
    if not gdd:
        abort(404)
    stemdiff = gdd.get('stems', False)
    bodydiff = gdd.get('body', False)
    return render_template('glyphrep.html', gn=gname, gdd=gdd, mag=ds.mag,
                           stemdiff=stemdiff, bodydiff=bodydiff,
                           sizes=ds.charsizes)

@app.route('/')
def entry_point():
    ds = diffState.theState
    dits = sorted(diffState.theState.diffdata.items(), key=maxWeight,
                  reverse=True)
    return render_template('main.html', sortedDD=dits, sizes=ds.charsizes)
