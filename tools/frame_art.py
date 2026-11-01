"""The decorative frame around the README: a top cap, a bottom cap and a thin divider, in three styles.

STANDARD LIBRARY ONLY (it runs on GitHub's runner). GitHub strips CSS, so the frame is made of pictures:
  art/frame-top-dark.svg    art/frame-top-light.svg
  art/frame-bottom-dark.svg art/frame-bottom-light.svg
  art/frame-divider-dark.svg art/frame-divider-light.svg
The style is chosen by "frame" in profile.json: "teyvat" (ornate gold), "moon" (slim moon-silver) or "sumeru" (leaf).
Every picture is 640 wide and scales to the width of the README (width="100%"), so the corners stay at the edges.
Nothing here is a game asset: just lines, curls, leaves and stars.
"""
import math

W = 640
VARIANTS = ('teyvat', 'moon', 'sumeru')
NAMES = {'teyvat': 'Teyvat gold', 'moon': 'Moon silver', 'sumeru': 'Sumeru leaf'}

def f2(v):
    s = ('%.2f' % v).rstrip('0').rstrip('.')
    return s if s not in ('-0', '') else '0'

def sparkle(cx, cy, R, fill, extra='', k=.16):
    k = R * k
    d = 'M%s %sQ%s %s %s %sQ%s %s %s %sQ%s %s %s %sQ%s %s %s %sZ' % (
        f2(cx), f2(cy - R), f2(cx + k), f2(cy - k), f2(cx + R), f2(cy), f2(cx + k), f2(cy + k), f2(cx), f2(cy + R),
        f2(cx - k), f2(cy + k), f2(cx - R), f2(cy), f2(cx - k), f2(cy - k), f2(cx), f2(cy - R))
    return '<path d="%s" fill="%s" %s/>' % (d, fill, extra)

def diamond(cx, cy, r, fill, extra=''):
    return '<path d="M%s %sL%s %sL%s %sL%s %sZ" fill="%s" %s/>' % (f2(cx), f2(cy - r), f2(cx + r), f2(cy), f2(cx), f2(cy + r), f2(cx - r), f2(cy), fill, extra)

def crescent(cx, cy, r, fill, tilt=-25, extra=''):
    """A moon: a circle with a bite taken out of it, turned by `tilt` degrees."""
    # outer arc radius r, inner arc radius r*.82, centres 0.42r apart
    ri = r * .84; off = r * .46
    # intersection points of circle A (0,0,r) and circle B (off,0,ri)
    x = (r * r - ri * ri + off * off) / (2 * off); y = math.sqrt(max(r * r - x * x, 0))
    d = 'M%s %sA%s %s 0 1 0 %s %sA%s %s 0 1 1 %s %sZ' % (f2(x), f2(-y), f2(r), f2(r), f2(x), f2(y), f2(ri), f2(ri), f2(x), f2(-y))
    return '<path transform="translate(%s %s) rotate(%s)" d="%s" fill="%s" %s/>' % (f2(cx), f2(cy), tilt, d, fill, extra)

def leaf(x, y, ang, L, Wd, fill, vein=None, extra=''):
    """A pointed leaf growing from (x,y) in direction ang (degrees, 0 = right, 90 = down)."""
    d = 'M0 0C%s %s %s %s %s 0C%s %s %s %s 0Z' % (f2(L * .25), f2(-Wd), f2(L * .72), f2(-Wd * .8), f2(L), f2(L * .72), f2(Wd * .8), f2(L * .25), f2(Wd))
    out = '<path transform="translate(%s %s) rotate(%s)" d="%s" fill="%s" %s/>' % (f2(x), f2(y), f2(ang), d, fill, extra)
    if vein:
        out += '<path transform="translate(%s %s) rotate(%s)" d="M%s 0H%s" stroke="%s" stroke-width=".7" stroke-linecap="round" fill="none"/>' % (f2(x), f2(y), f2(ang), f2(L * .1), f2(L * .8), vein)
    return out

def dots(pts, r, fill, extra=''):
    return ''.join('<circle cx="%s" cy="%s" r="%s" fill="%s" %s/>' % (f2(x), f2(y), f2(r), fill, extra) for x, y in pts)

def wrap(h, defs, body, title):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-label="%s">'
            '<title>%s</title><defs>%s</defs>%s</svg>' % (W, h, W, h, title, title, defs, body))

EDGE = -8   # nudge each half outwards so the frame's sides sit on the very edge of the README, level with the pictures inside it

def mirror(inner):
    """The right half is the left half turned round the middle (and nudged out to the edge)."""
    inner = '<g transform="translate(%d 0)">%s</g>' % (EDGE, inner)
    return '<g>%s</g><g transform="translate(%d 0) scale(-1 1)">%s</g>' % (inner, W, inner)

def flip(inner, h):
    return '<g transform="translate(0 %d) scale(1 -1)">%s</g>' % (h, inner)

# ------------------------------------------------------------------ palettes (dark README / light README)
PAL = {
    'teyvat': {'dark': dict(a='#F3D79C', b='#D3BC8E', c='#8E7647', glow='#F3D79C'),
               'light': dict(a='#A9692C', b='#8A6A2A', c='#C8A464', glow='#C8892F')},
    'moon':   {'dark': dict(a='#E8EEFB', b='#AEBDDA', c='#6B7A9E', glow='#BFD0F2'),
               'light': dict(a='#4A5B80', b='#6B7B9F', c='#A9B4CC', glow='#7C8DB4')},
    'sumeru': {'dark': dict(a='#C9EC7C', b='#7FC46A', c='#3E7A4E', glow='#B8E36B', gold='#D3BC8E'),
               'light': dict(a='#5C8A24', b='#3F7F3A', c='#8DB872', glow='#6A9A2E', gold='#8A6A2A')},
}

# ================================================================== TEYVAT: ornate gold
# one half of the top cap, drawn on a 320 x 64 area, the horizontal rule at y = 34, the corner turning down on the left.
def teyvat_half(p, h=64):
    a, b, c = p['a'], p['b'], p['c']
    y = 34
    s = []
    # outer rule + the side return (fades out downwards) with a chamfered corner
    s.append('<path d="M26 %d H%d" stroke="url(#rule)" stroke-width="1.7" fill="none" stroke-linecap="round"/>' % (y, 268))
    s.append('<path d="M26 %d L13 %d V%d" stroke="url(#ret)" stroke-width="1.7" fill="none" stroke-linecap="round" stroke-linejoin="round"/>' % (y, y + 13, h))
    # inner hairline
    s.append('<path d="M31 %d H%d" stroke="url(#rule)" stroke-width=".8" opacity=".75" fill="none" stroke-linecap="round"/>' % (y + 6, 252))
    s.append('<path d="M31 %d L19 %d V%d" stroke="url(#ret)" stroke-width=".8" opacity=".75" fill="none" stroke-linejoin="round"/>' % (y + 6, y + 18, h))
    # corner: studs and a filigree scroll curling up and over the rule
    s.append(diamond(26, y, 4.6, a))
    s.append(diamond(13, y + 13, 3.2, b))
    s.append('<circle cx="26" cy="%d" r="1.3" fill="#0d1220" opacity=".55"/>' % y)
    s.append('<path d="M33 %d C44 %d 58 %d 62 %d C66 %d 60 %d 56 %d C53 %d 56 %d 59 %d" stroke="%s" stroke-width="1.3" fill="none" stroke-linecap="round"/>' % (
        y - 1, y - 14, y - 22, y - 15, y - 8, y - 6, y - 10, y - 13, y - 17, y - 16, a))
    s.append('<path d="M70 %d C80 %d 92 %d 100 %d C108 %d 118 %d 126 %d" stroke="%s" stroke-width="1" fill="none" stroke-linecap="round" opacity=".85"/>' % (
        y - 2, y - 9, y - 11, y - 5, y + 1, y - 2, y - 7, b))
    s.append(dots([(60, y - 18), (128, y - 7), (94, y - 11.5)], 1.5, a))
    s.append(leaf(33, y - 3, -62, 14, 3.4, b, extra='opacity=".9"'))
    s.append(leaf(20, y - 6, -108, 11, 2.8, b, extra='opacity=".8"'))
    # little stars in the empty sky above the rule
    s.append(sparkle(168, 14, 4.2, a, 'opacity=".9"'))
    s.append(sparkle(224, 21, 2.6, b, 'opacity=".8"'))
    s.append(dots([(196, 12), (140, 17), (250, 12)], 1, b, 'opacity=".8"'))
    # end-of-rule diamond chain towards the middle
    s.append(diamond(275, y, 3.4, a)); s.append(diamond(287, y, 2.2, b)); s.append(diamond(296, y, 1.5, b))
    return ''.join(s)

def teyvat_defs(p, h):
    a, b, c = p['a'], p['b'], p['c']
    return ('<linearGradient id="rule" gradientUnits="userSpaceOnUse" x1="26" y1="0" x2="300" y2="0"><stop offset="0" stop-color="%s"/><stop offset=".45" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>'
            '<linearGradient id="ret" gradientUnits="userSpaceOnUse" x1="0" y1="34" x2="0" y2="%d"><stop offset="0" stop-color="%s"/><stop offset=".7" stop-color="%s" stop-opacity=".7"/><stop offset="1" stop-color="%s" stop-opacity="0"/></linearGradient>'
            '<radialGradient id="halo"><stop offset="0" stop-color="%s" stop-opacity=".45"/><stop offset="1" stop-color="%s" stop-opacity="0"/></radialGradient>') % (
                a, b, a, h, a, b, b, p['glow'], p['glow'])

def teyvat_top(p):
    h = 64; y = 34
    mid = []
    mid.append('<circle cx="320" cy="%d" r="30" fill="url(#halo)"/>' % y)
    mid.append(crescent(317, y - 1, 13.5, 'url(#rule)', tilt=-28))
    mid.append(sparkle(332, y - 8, 7.5, p['a']))
    mid.append(sparkle(340, y + 6, 3.2, p['b']))
    mid.append(dots([(306, y - 20), (345, y - 17)], 1.1, p['b']))
    mid.append(diamond(320, y + 20, 2.6, p['b']))
    mid.append('<path d="M302 %d H338" stroke="%s" stroke-width=".7" opacity="0"/>' % (y, p['b']))
    return wrap(h, teyvat_defs(p, h), mirror(teyvat_half(p, h)) + ''.join(mid), 'Gold frame, top edge: a crescent moon and a star between scrolls')

def teyvat_bottom(p):
    h = 64
    mid = []
    y = 34
    mid.append('<circle cx="320" cy="%d" r="28" fill="url(#halo)"/>' % y)
    mid.append(sparkle(320, y, 12.5, p['a']))
    mid.append(diamond(320, y, 3.2, '#0d1220' if p is PAL['teyvat']['dark'] else '#FFFFFF', 'opacity=".55"'))
    mid.append(diamond(304, y, 2.8, p['b'])); mid.append(diamond(336, y, 2.8, p['b']))
    mid.append(dots([(310, y - 15), (331, y + 15)], 1.1, p['b']))
    # bottom cap = the top cap turned over (the star moves to the other side so it is not a copy)
    return wrap(h, teyvat_defs(p, h), flip(mirror(teyvat_half(p, h)), h) + flip(''.join(mid), h), 'Gold frame, bottom edge: a four-point star between scrolls')

def teyvat_divider(p):
    h = 26; y = 13
    half = ('<path d="M120 %d H300" stroke="url(#dv)" stroke-width="1.2" stroke-linecap="round"/>'
            '<path d="M150 %d H290" stroke="url(#dv)" stroke-width=".6" opacity=".7" transform="translate(0 4)"/>' % (y, y - 4 + 0))
    half = ('<path d="M96 %d H292" stroke="url(#dv)" stroke-width="1.2" stroke-linecap="round" fill="none"/>' % y +
            '<path d="M140 %d H282" stroke="url(#dv)" stroke-width=".6" opacity=".7" fill="none"/>' % (y + 4) +
            diamond(298, y, 2.6, p['b']) + diamond(306, y, 1.6, p['b']) +
            dots([(96, y)], 1.8, p['a']) +
            '<path d="M13 2 V24" stroke="%s" stroke-width="1.5" stroke-linecap="round"/>' % p['b'] + diamond(13, y, 3, p['a']) + '<path d="M19 6 V20" stroke="%s" stroke-width=".8" opacity=".7"/>' % p['b'])
    defs = ('<linearGradient id="dv" gradientUnits="userSpaceOnUse" x1="96" y1="0" x2="300" y2="0"><stop offset="0" stop-color="%s" stop-opacity="0"/><stop offset=".55" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>' % (p['b'], p['b'], p['a']))
    mid = diamond(320, y, 5.2, p['a']) + sparkle(320, y, 10, p['a'], 'opacity=".95"') + diamond(320, y, 2, '#0d1220' if p is PAL['teyvat']['dark'] else '#FFFFFF', 'opacity=".6"')
    return wrap(h, defs, mirror(half) + mid, 'Gold divider with a small star')

# ================================================================== MOON: slim silver, Tsukimi
def moon_half(p, h=64):
    a, b, c = p['a'], p['b'], p['c']
    y = 34
    s = []
    s.append('<path d="M20 %d H282" stroke="url(#rule)" stroke-width="1.1" fill="none" stroke-linecap="round"/>' % y)
    s.append('<path d="M20 %d C12 %d 11 %d 11 %d V%d" stroke="url(#ret)" stroke-width="1.1" fill="none" stroke-linecap="round"/>' % (y, y, y + 6, y + 14, h))
    # tiny star dots drifting along the rule, like stars over a horizon
    pts = [(46, y - 8, 1.1), (88, y - 14, .9), (130, y - 6, 1.3), (176, y - 15, .9), (212, y - 8, 1.1), (246, y - 16, .8), (60, y + 9, .8), (150, y + 8, .9), (232, y + 9, .8), (110, y + 12, .7)]
    for x, yy, r in pts: s.append('<circle cx="%s" cy="%s" r="%s" fill="%s" opacity=".85"/>' % (f2(x), f2(yy), r, b))
    s.append(sparkle(70, y - 11, 3.4, a, 'opacity=".9"')); s.append(sparkle(196, y - 11, 2.7, a, 'opacity=".8"'))
    s.append(sparkle(20, y, 5.2, a))
    s.append('<circle cx="11" cy="%d" r="1.6" fill="%s"/>' % (y + 14, b))
    s.append('<path d="M286 %d H298" stroke="%s" stroke-width="1.1" stroke-linecap="round"/>' % (y, a))
    return ''.join(s)

def moon_defs(p, h):
    return ('<linearGradient id="rule" gradientUnits="userSpaceOnUse" x1="20" y1="0" x2="300" y2="0"><stop offset="0" stop-color="%s"/><stop offset=".5" stop-color="%s" stop-opacity=".75"/><stop offset="1" stop-color="%s"/></linearGradient>'
            '<linearGradient id="ret" gradientUnits="userSpaceOnUse" x1="0" y1="34" x2="0" y2="%d"><stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s" stop-opacity="0"/></linearGradient>'
            '<radialGradient id="halo"><stop offset="0" stop-color="%s" stop-opacity=".5"/><stop offset="1" stop-color="%s" stop-opacity="0"/></radialGradient>') % (
                p['a'], p['b'], p['a'], h, p['a'], p['b'], p['glow'], p['glow'])

def moon_top(p):
    h = 64; y = 34
    mid = ['<circle cx="320" cy="%d" r="34" fill="url(#halo)"/>' % y,
           crescent(318, y, 15, p['a'], tilt=-30), sparkle(334, y - 7, 5.2, p['a']),
           dots([(298, y - 12), (346, y + 10), (306, y + 13)], 1, p['b'], 'opacity=".9"')]
    return wrap(h, moon_defs(p, h), mirror(moon_half(p, h)) + ''.join(mid), 'Silver frame, top edge: a crescent moon among small stars')

def moon_bottom(p):
    h = 64; y = 34
    mid = ['<circle cx="320" cy="%d" r="30" fill="url(#halo)"/>' % y, sparkle(320, y, 7.5, p['a']), sparkle(338, y - 7, 3, p['b']), sparkle(303, y + 6, 2.6, p['b'])]
    return wrap(h, moon_defs(p, h), flip(mirror(moon_half(p, h)), h) + flip(''.join(mid), h), 'Silver frame, bottom edge: three small stars')

def moon_divider(p):
    h = 26; y = 13
    half = ('<path d="M120 %d H298" stroke="url(#dv)" stroke-width="1" stroke-linecap="round" fill="none"/>' % y +
            dots([(160, y - 5), (214, y + 5), (258, y - 4)], .9, p['b'], 'opacity=".9"') +
            '<path d="M11 3 V23" stroke="%s" stroke-width="1" stroke-linecap="round" opacity=".8"/>' % p['b'] + sparkle(11, y, 4, p['a']))
    defs = '<linearGradient id="dv" gradientUnits="userSpaceOnUse" x1="120" y1="0" x2="300" y2="0"><stop offset="0" stop-color="%s" stop-opacity="0"/><stop offset="1" stop-color="%s"/></linearGradient>' % (p['b'], p['a'])
    return wrap(h, defs, mirror(half) + crescent(320, y, 7.5, p['a'], tilt=-30) + sparkle(329, y - 3, 3, p['a']), 'Silver divider with a small crescent moon')

# ================================================================== SUMERU: leaves and vines
def sumeru_half(p, h=64):
    a, b, c, g = p['a'], p['b'], p['c'], p['gold']
    y = 34
    s = []
    s.append('<path d="M30 %d H282" stroke="url(#rule)" stroke-width="1.4" fill="none" stroke-linecap="round"/>' % y)
    s.append('<path d="M30 %d C17 %d 14 %d 14 %d V%d" stroke="url(#ret)" stroke-width="1.4" fill="none" stroke-linecap="round"/>' % (y, y, y + 6, y + 18, h))
    # a gold hairline under the vine
    s.append('<path d="M34 %d H262" stroke="%s" stroke-width=".7" opacity=".6"/>' % (y + 5, g))
    # a vine that wanders over the rule with leaf pairs
    s.append('<path d="M34 %d C60 %d 70 %d 96 %d S140 %d 168 %d S226 %d 256 %d" stroke="%s" stroke-width=".9" fill="none" opacity=".8" stroke-linecap="round"/>' % (
        y - 2, y - 14, y + 8, y - 8, y - 10, y - 4, y + 3, y - 8, b))
    for x, yy, ang, L in [(52, y - 10, -52, 15), (68, y - 4, 38, 11), (110, y - 6, -40, 14), (128, y - 9, 28, 10), (162, y - 8, -58, 13), (190, y - 2, 36, 12), (222, y - 2, -34, 11), (240, y - 8, 30, 10)]:
        s.append(leaf(x, yy, ang, L, 3.6, b if (x // 10) % 2 else a, vein=c, extra='opacity=".92"'))
    # the corner: a bigger leaf pair + a gold bud
    s.append(leaf(20, y - 4, -50, 24, 6.2, a, vein=c))
    s.append(leaf(20, y - 4, -100, 19, 5.2, b, vein=c))
    s.append(leaf(16, y + 8, 95, 16, 4.2, b, vein=c, extra='opacity=".8"'))
    s.append(diamond(14, y + 20, 2.8, g))
    s.append('<circle cx="30" cy="%d" r="2.6" fill="%s"/>' % (y, g))
    s.append(dots([(266, y - 6), (276, y - 3)], 1.1, g))
    return ''.join(s)

def sumeru_defs(p, h):
    return ('<linearGradient id="rule" gradientUnits="userSpaceOnUse" x1="30" y1="0" x2="300" y2="0"><stop offset="0" stop-color="%s"/><stop offset=".5" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>'
            '<linearGradient id="ret" gradientUnits="userSpaceOnUse" x1="0" y1="34" x2="0" y2="%d"><stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s" stop-opacity="0"/></linearGradient>'
            '<radialGradient id="halo"><stop offset="0" stop-color="%s" stop-opacity=".42"/><stop offset="1" stop-color="%s" stop-opacity="0"/></radialGradient>') % (
                p['gold'], p['b'], p['gold'], h, p['b'], p['b'], p['glow'], p['glow'])

def sumeru_top(p):
    h = 64; y = 34; a, b, c, g = p['a'], p['b'], p['c'], p['gold']
    mid = ['<circle cx="320" cy="%d" r="32" fill="url(#halo)"/>' % y,
           leaf(320, y + 4, -90, 23, 6.5, a, vein=c),
           leaf(320, y + 4, -132, 17, 4.8, b, vein=c), leaf(320, y + 4, -48, 17, 4.8, b, vein=c),
           leaf(320, y + 4, -170, 11, 3.2, b, extra='opacity=".85"'), leaf(320, y + 4, -10, 11, 3.2, b, extra='opacity=".85"'),
           diamond(320, y + 8, 4.2, g), '<circle cx="320" cy="%d" r="1.3" fill="#0d1220" opacity=".5"/>' % (y + 8)]
    return wrap(h, sumeru_defs(p, h), mirror(sumeru_half(p, h)) + ''.join(mid), 'Leaf frame, top edge: a sprouting leaf between vines')

def sumeru_bottom(p):
    h = 64; y = 34; a, b, c, g = p['a'], p['b'], p['c'], p['gold']
    mid = ['<circle cx="320" cy="%d" r="30" fill="url(#halo)"/>' % y,
           leaf(320, y, -90, 13, 4.2, a, vein=c), leaf(320, y, 90, 13, 4.2, b, vein=c), leaf(320, y, 0, 13, 4.2, b, vein=c), leaf(320, y, 180, 13, 4.2, a, vein=c),
           diamond(320, y, 3.6, g)]
    return wrap(h, sumeru_defs(p, h), flip(mirror(sumeru_half(p, h)), h) + flip(''.join(mid), h), 'Leaf frame, bottom edge: four leaves round a seed')

def sumeru_divider(p):
    h = 26; y = 13; a, b, c, g = p['a'], p['b'], p['c'], p['gold']
    half = ('<path d="M110 %d H296" stroke="url(#dv)" stroke-width="1.1" stroke-linecap="round" fill="none"/>' % y +
            leaf(150, y, -40, 10, 2.8, b, extra='opacity=".85"') + leaf(190, y, 40, 10, 2.8, b, extra='opacity=".85"') + leaf(232, y, -40, 9, 2.6, a, extra='opacity=".85"') +
            diamond(300, y, 1.8, g) +
            '<path d="M14 2 V24" stroke="%s" stroke-width="1.3" stroke-linecap="round"/>' % b + leaf(14, y, -65, 9, 2.6, a, extra='opacity=".9"') + leaf(14, y, 65, 9, 2.6, a, extra='opacity=".9"') + diamond(14, y, 2, g))
    defs = '<linearGradient id="dv" gradientUnits="userSpaceOnUse" x1="110" y1="0" x2="300" y2="0"><stop offset="0" stop-color="%s" stop-opacity="0"/><stop offset="1" stop-color="%s"/></linearGradient>' % (b, g)
    return wrap(h, defs, mirror(half) + leaf(320, y + 4, -90, 11, 3.4, a) + leaf(320, y + 4, -135, 8, 2.4, b) + leaf(320, y + 4, -45, 8, 2.4, b) + diamond(320, y + 5, 2, g), 'Leaf divider with a small sprout')

# ------------------------------------------------------------------ the public part
MAKERS = {'teyvat': (teyvat_top, teyvat_bottom, teyvat_divider),
          'moon': (moon_top, moon_bottom, moon_divider),
          'sumeru': (sumeru_top, sumeru_bottom, sumeru_divider)}

def frame_files(variant):
    """{'art/frame-top-dark.svg': svg text, ...} for one style. Same file names for every style, so switching style
    is only a change of "frame" in profile.json."""
    if variant not in MAKERS: variant = 'teyvat'
    top, bottom, divider = MAKERS[variant]
    out = {}
    for t in ('dark', 'light'):
        p = PAL[variant][t]
        out['art/frame-top-%s.svg' % t] = top(p)
        out['art/frame-bottom-%s.svg' % t] = bottom(p)
        out['art/frame-divider-%s.svg' % t] = divider(p)
    return out

def all_files():
    """Every style under its own name (frame-<style>-top-dark.svg ...), for the preview page."""
    out = {}
    for v in VARIANTS:
        for k, s in frame_files(v).items():
            out[k.replace('frame-', 'frame-%s-' % v)] = s
    return out
