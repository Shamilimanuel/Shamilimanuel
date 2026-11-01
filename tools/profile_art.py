"""The pictures and text blocks that change by themselves: moon + season banner, note of the day,
weekly spotlight, levelling bars, "Now building" and "Recently updated".

STANDARD LIBRARY ONLY, so GitHub's runner can import it without installing anything.
Text in every picture is drawn from outlines in glyphs.json (Cinzel and Nunito Sans, both OFL),
because GitHub shows SVGs through <img>, which cannot load fonts. Animation is SMIL only.
Nothing here is a copied game asset.
"""
import datetime, html, json, math, random, zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
GL = json.loads((HERE / 'glyphs.json').read_text(encoding='utf-8'))
ICONS = json.loads((HERE / 'icons.json').read_text(encoding='utf-8')) if (HERE / 'icons.json').exists() else {}

EL = dict(pyro='#FF8A5C', hydro='#5CC4F5', anemo='#5FD3AE', electro='#B18BEC', dendro='#A8D04A', cryo='#9FE0F0', geo='#F2C463')
ELN = ['pyro', 'hydro', 'anemo', 'electro', 'dendro', 'cryo', 'geo']
SYNODIC = 29.530588853

def f2(v):
    s = ('%.2f' % v).rstrip('0').rstrip('.')
    return s if s not in ('-0', '') else '0'

def esc(s): return html.escape(str(s), quote=True)

# ------------------------------------------------------------------ text as outlines
def measure(font, s, size, ls=0.0):
    g = GL[font]; w = 0.0
    for ch in s: w += g['adv'].get(ch, g['upem'] * .3) * size / g['upem'] + ls
    return w - ls if s else 0.0

def text(font, s, size, x, y, fill, anchor='start', ls=0.0, extra=''):
    g = GL[font]; sc = size / g['upem']
    w = measure(font, s, size, ls)
    if anchor == 'middle': x -= w / 2
    elif anchor == 'end': x -= w
    out, cx = [], x
    for ch in s:
        p = g['path'].get(ch)
        if p: out.append('<path transform="translate(%s %s) scale(%.5f %.5f)" d="%s"/>' % (f2(cx), f2(y), sc, -sc, p))
        cx += g['adv'].get(ch, g['upem'] * .3) * sc + ls
    return '<g fill="%s" %s>%s</g>' % (fill, extra, ''.join(out))

def sparkle(cx, cy, R, fill, extra=''):
    k = R * .16
    d = 'M%s %sQ%s %s %s %sQ%s %s %s %sQ%s %s %s %sQ%s %s %s %sZ' % (
        f2(cx), f2(cy - R), f2(cx + k), f2(cy - k), f2(cx + R), f2(cy), f2(cx + k), f2(cy + k), f2(cx), f2(cy + R),
        f2(cx - k), f2(cy + k), f2(cx - R), f2(cy), f2(cx - k), f2(cy - k), f2(cx), f2(cy - R))
    return '<path d="%s" fill="%s" %s/>' % (d, fill, extra)

def star_pts(cx, cy, R):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5; r = R if i % 2 == 0 else R * .42
        pts.append('%s,%s' % (f2(cx + r * math.cos(a)), f2(cy + r * math.sin(a))))
    return ' '.join(pts)

GLYPH = {   # the element marks, 24x24 box
    'pyro': ('f', 'M12 2.6c.6 3.4 5.6 5.6 5.6 10.6a5.6 5.6 0 0 1-11.2 0c0-2.6 1.4-3.8 2.6-5.6.6 1 .6 1.8.5 2.8C11 8.4 12.2 5.6 12 2.6z'),
    'hydro': ('f', 'M12 2.6C9.4 6.6 5.6 9.9 5.6 14.2a6.4 6.4 0 0 0 12.8 0c0-4.3-3.8-7.6-6.4-11.6z'),
    'anemo': ('s', 'M3.5 8.5h9.2a2.9 2.9 0 1 0-2.9-2.9M2.5 13h14.8a3 3 0 1 1-3 3M5.5 18h6.5'),
    'electro': ('f', 'M13.4 2.2L5.2 13.2h5.4l-1.2 8.6 9.4-12.4h-5.6z'),
    'dendro': ('s', 'M5 19.2C4.6 10.4 9.6 4.8 19.6 4.2c.2 10-4.8 15.2-12.6 15M5 19.2l8.6-8.6'),
    'cryo': ('s', 'M12 2.5v19M3.8 7.2l16.4 9.6M20.2 7.2L3.8 16.8M9.5 4.2L12 6.4l2.5-2.2M9.5 19.8L12 17.6l2.5 2.2'),
    'geo': ('s', 'M12 2.4l8 7.2-8 12-8-12z M4 9.6h16M12 2.4l-3.4 7.2L12 21.6l3.4-12z'),
}
def glyph(el, x, y, size, col=None, sw=1.9):
    col = col or EL[el]; kind, d = GLYPH[el]; sc = size / 24
    a = ('fill="%s"' % col) if kind == 'f' else ('fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" stroke-linejoin="round"' % (col, sw))
    return '<g transform="translate(%s %s) scale(%.4f) translate(-12 -12)"><path d="%s" %s/></g>' % (f2(x), f2(y), sc, d, a)

# ------------------------------------------------------------------ the moon and the seasons
def to_date(d):
    if isinstance(d, datetime.datetime): return d.date()
    if isinstance(d, datetime.date): return d
    return datetime.date.fromisoformat(str(d))

def moon_age(d):
    """Days since new moon (0 .. 29.53), for noon UTC on that date. Plain astronomy, no network."""
    d = to_date(d)
    jd = (datetime.datetime(d.year, d.month, d.day, 12) - datetime.datetime(1970, 1, 1)).total_seconds() / 86400 + 2440587.5
    return ((jd - 2451550.1) % SYNODIC + SYNODIC) % SYNODIC

def phase_name(age):
    p = age / SYNODIC
    return ('New moon' if p < .03 or p > .97 else 'Waxing crescent' if p < .22 else 'First quarter' if p < .28 else 'Waxing gibbous' if p < .47
            else 'Full moon' if p < .53 else 'Waning gibbous' if p < .72 else 'Last quarter' if p < .78 else 'Waning crescent')

def season_of(d):
    m = to_date(d).month   # meteorological seasons: the first of the month switches it
    return 'spring' if m in (3, 4, 5) else 'summer' if m in (6, 7, 8) else 'autumn' if m in (9, 10, 11) else 'winter'

SEASONS = {
    'autumn': dict(d=('#2a1b33', '#120b16'), l=('#F6DDB5', '#E8B88C'), glow='#b0602e', glowl='#E88E4A', p='leaf', c=('#FF8A5C', '#F2C463', '#C8602B', '#E0A040')),
    'winter': dict(d=('#13264d', '#0a1428'), l=('#E3EEF8', '#BED0EA'), glow='#6fb6dc', glowl='#9FD2F0', p='snow', c=('#FFFFFF', '#DDF3FF')),
    'spring': dict(d=('#1c2750', '#161a38'), l=('#F8E4EC', '#DDD6F0'), glow='#b5679c', glowl='#E8A2C6', p='petal', c=('#F6B3CF', '#FFE0EA', '#E896BB')),
    'summer': dict(d=('#102a4a', '#0a1a30'), l=('#DFF1F2', '#BFE2EE'), glow='#2f9bd0', glowl='#5CC4F5', p='fly', c=('#F8E08A', '#FFF3B8')),
}

def moon_shapes(cx, cy, R, age, dark):
    """The moon: a dim disc, plus the lit part as one path. Waxing = lit on the right, waning = lit on the left."""
    p = age / SYNODIC; k = math.cos(2 * math.pi * p); rx = round(R * abs(k), 2)
    wax = p < .5; gib = k < 0
    sweep = (1 if gib else 0) if wax else (0 if gib else 1)
    lit = 'M%s %sA%s %s 0 0 %d %s %sA%s %s 0 0 %d %s %sZ' % (cx, cy - R, R, R, 1 if wax else 0, cx, cy + R, rx, R, sweep, cx, cy - R)
    out = '<circle cx="%s" cy="%s" r="%s" fill="%s" fill-opacity="%s" stroke="%s" stroke-opacity=".5"/>' % (
        cx, cy, R, '#20284a' if dark else '#8d86b4', '.95' if dark else '.4', '#3a4270' if dark else '#8d86b4')
    out += '<clipPath id="litc"><path d="%s"/></clipPath><path d="%s" fill="url(#moon)"/>' % (lit, lit)
    out += ('<g clip-path="url(#litc)" fill="#B79A5C" fill-opacity=".26"><circle cx="%s" cy="%s" r="%s"/><circle cx="%s" cy="%s" r="%s"/>'
            '<circle cx="%s" cy="%s" r="%s"/><circle cx="%s" cy="%s" r="%s"/></g>') % (
        cx - R * .28, cy - R * .2, R * .2, cx + R * .3, cy + R * .28, R * .26, cx + R * .22, cy - R * .42, R * .1, cx - R * .4, cy + R * .38, R * .12)
    return out

def particles(season, W, H, dark):
    S = SEASONS[season]; r = random.Random(zlib.crc32(season.encode())); out = []
    for i in range(18):
        x = r.random() * W; c = S['c'][i % len(S['c'])]; dur = 9 + r.random() * 7; begin = -r.random() * 14; dx = (r.random() - .5) * 90
        if S['p'] == 'fly':
            y = 90 + r.random() * 190
            out.append('<circle cx="%s" cy="%s" r="2.6" fill="%s"><animate attributeName="opacity" values=".1;1;.1" dur="%ss" begin="%ss" repeatCount="indefinite"/>'
                       '<animateTransform attributeName="transform" type="translate" values="0 0;%s -12;0 0" dur="%ss" begin="%ss" repeatCount="indefinite"/></circle>' % (
                f2(x), f2(y), c if dark else '#D6A24E', f2(3 + r.random() * 3), f2(begin), f2(dx / 6), f2(3 + r.random() * 3), f2(begin)))
            continue
        if S['p'] == 'snow': shape = '<circle cx="0" cy="0" r="%s" fill="%s"/>' % (f2(1.6 + r.random() * 2.2), c if dark else '#FFFFFF')
        else:
            rx, ry = (6, 3.1) if S['p'] == 'leaf' else (4.6, 2.6)
            shape = '<ellipse cx="0" cy="0" rx="%s" ry="%s" fill="%s" transform="rotate(%d)"/>' % (rx, ry, c, r.randint(0, 180))
        out.append('<g><animateTransform attributeName="transform" type="translate" values="%s -20;%s %s;%s %s" dur="%ss" begin="%ss" repeatCount="indefinite"/>%s</g>' % (
            f2(x), f2(x + dx), f2(H * .55), f2(x), f2(H + 20), f2(dur), f2(begin), shape))
    return ''.join(out)

def banner_svg(theme, age, season):
    W, H = 1200, 300; dark = theme == 'dark'; S = SEASONS[season]; sky = S['d'] if dark else S['l']
    rnd = random.Random(7); d = []
    label = phase_name(age)
    d.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-label="Shamil, student, gamer, PC builder. Tonight\'s moon: %s. %s sky.">' % (W, H, W, H, label.lower(), season.capitalize()))
    d.append('<title>Shamil</title><defs>')
    d.append('<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>' % sky)
    d.append('<radialGradient id="hz" cx=".4" cy="1" r=".8"><stop offset="0" stop-color="%s" stop-opacity="%s"/><stop offset="1" stop-color="%s" stop-opacity="0"/></radialGradient>' % (
        S['glow'] if dark else S['glowl'], '.55' if dark else '.6', S['glow'] if dark else S['glowl']))
    d.append('<radialGradient id="halo" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="%s" stop-opacity="%s"/><stop offset=".4" stop-color="%s" stop-opacity=".18"/><stop offset="1" stop-color="%s" stop-opacity="0"/></radialGradient>' % (
        ('#F3D79C', '.55', '#D3BC8E', '#D3BC8E') if dark else ('#F3C97E', '.7', '#F3C97E', '#F3C97E')))
    d.append('<radialGradient id="moon" cx=".38" cy=".34" r=".8"><stop offset="0" stop-color="%s"/><stop offset=".55" stop-color="%s"/><stop offset="1" stop-color="%s"/></radialGradient>' % (
        ('#FFFBEA', '#F6E3B4', '#D9BE82') if dark else ('#FFF6D8', '#EED08E', '#C99A45')))
    d.append('<linearGradient id="name" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="%s"/><stop offset=".5" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>' % (
        ('#FFF1C9', '#F3D79C', '#C9A24E') if dark else ('#C8892F', '#A9692C', '#7A4A14')))
    d.append('<linearGradient id="trail" x1="1" y1="0" x2="0" y2="0"><stop offset="0" stop-color="%s" stop-opacity=".95"/><stop offset="1" stop-color="%s" stop-opacity="0"/></linearGradient>' % (('#fff',) * 2 if dark else ('#C8892F',) * 2))
    d.append('<filter id="blur" x="-60%" y="-400%" width="220%" height="900%"><feGaussianBlur stdDeviation="14"/></filter>')
    d.append('<filter id="glowf" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="3"/></filter>')
    d.append('<clipPath id="rr"><rect width="%d" height="%d" rx="18"/></clipPath></defs>' % (W, H))
    d.append('<g clip-path="url(#rr)"><rect width="%d" height="%d" fill="url(#sky)"/><rect width="%d" height="%d" fill="url(#hz)"/>' % (W, H, W, H))
    cloud = '#8E88C8' if dark else '#FFFFFF'
    for (cx, cy, rx, ry, op, dur, dx) in ((300, 255, 260, 22, .13 if dark else .55, 70, 60), (860, 232, 300, 26, .11 if dark else .5, 90, -70), (1100, 270, 220, 18, .12 if dark else .5, 80, 50)):
        d.append('<ellipse cx="%d" cy="%d" rx="%d" ry="%d" fill="%s" fill-opacity="%s" filter="url(#blur)"><animateTransform attributeName="transform" type="translate" values="0 0;%d 0;0 0" dur="%ds" repeatCount="indefinite" calcMode="spline" keyTimes="0;.5;1" keySplines=".45 0 .55 1;.45 0 .55 1"/></ellipse>' % (cx, cy, rx, ry, cloud, op, dx, dur))
    scol = '#FFFFFF' if dark else '#D6A24E'
    for i in range(110):
        x = rnd.random() * W; y = rnd.random() * (H - 20)
        if 70 < x < 640 and 50 < y < 250 and rnd.random() < .5: continue
        r = .5 + rnd.random() ** 2 * 1.6; base = (.25 + rnd.random() * .5) * (1 if dark else .85); dur = 3 + rnd.random() * 5
        d.append('<circle cx="%s" cy="%s" r="%s" fill="%s" opacity="%s"><animate attributeName="opacity" values="%s;%s;%s" dur="%ss" begin="-%ss" repeatCount="indefinite"/></circle>' % (
            f2(x), f2(y), f2(r), scol, f2(base), f2(base), f2(min(1, base + .5)), f2(base), f2(dur), f2(rnd.random() * dur)))
    for (sx, sy, sr, dl) in ((640, 60, 9, 0), (760, 190, 6, 1.4), (930, 48, 7, 2.6), (1160, 262, 8, .8), (560, 262, 5, 3.3), (1120, 50, 5, 2)):
        d.append('<g transform="translate(%d %d)"><g opacity="0"><animate attributeName="opacity" values="0;1;0" dur="4.2s" begin="%ss" repeatCount="indefinite"/>%s</g></g>' % (
            sx, sy, dl, sparkle(0, 0, sr * 1.5, '#FFF1C9' if dark else '#C8892F')))
    d.append(particles(season, W, H, dark))
    for (x1, y1, dl, dur) in ((760, 40, 2, 14), (300, 20, 8, 17)):
        d.append('<g opacity="0"><animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;.02;.06;.12;1" dur="%ds" begin="%ss" repeatCount="indefinite"/>'
                 '<animateTransform attributeName="transform" type="translate" values="0 0;-260 120" keyTimes="0;.14" calcMode="linear" dur="%ds" begin="%ss" repeatCount="indefinite" additive="sum"/>'
                 '<g transform="translate(%d %d) rotate(25)"><rect x="0" y="-1" width="120" height="2" rx="1" fill="url(#trail)"/></g></g>' % (dur, dl, dur, dl, x1, y1))
    # tonight's moon
    d.append('<g><animate attributeName="opacity" values="1;.9;1" dur="9s" repeatCount="indefinite"/>')
    d.append('<circle cx="1030" cy="112" r="190" fill="url(#halo)" opacity="%s"><animate attributeName="r" values="175;205;175" dur="9s" repeatCount="indefinite" calcMode="spline" keyTimes="0;.5;1" keySplines=".45 0 .55 1;.45 0 .55 1"/></circle>' % f2(.3 + .7 * (1 - math.cos(2 * math.pi * age / SYNODIC)) / 2))
    d.append('<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -5;0 0" dur="12s" repeatCount="indefinite" calcMode="spline" keyTimes="0;.5;1" keySplines=".45 0 .55 1;.45 0 .55 1"/>')
    d.append(moon_shapes(1030, 112, 64, age, dark))
    d.append('</g></g>')
    d.append(text('cinzel_semibold', label.upper(), 17, 1030, 224, '#F3D79C' if dark else '#4a3a2a', 'middle', 3.2))
    d.append('<g opacity=".98">' + text('cinzel_bold', 'SHAMIL', 96, 84, 170, 'url(#name)', 'start', 16) + '</g>')
    gold = '#D3BC8E' if dark else '#B8944A'
    d.append('<path d="M86 196H292 M308 196H560" stroke="%s" stroke-width="1.4" stroke-linecap="round"/><path d="M300 189l7 7-7 7-7-7z" fill="%s"/>' % (gold, gold))
    d.append('<path d="M567 196l4 4-4 4-4-4z" fill="%s" opacity=".7"/><path d="M79 196l4 4-4 4-4-4z" fill="%s" opacity=".7"/>' % (gold, gold))
    d.append(text('cinzel_regular', 'STUDENT   ·   GAMER   ·   PC BUILDER', 19, 86, 238, '#D3BC8E' if dark else '#6B5A33', 'start', 4.5))
    for i, e in enumerate(ELN):
        cx = 92 + i * 28
        d.append('<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -4;0 0" dur="%ss" begin="-%ss" repeatCount="indefinite" calcMode="spline" keyTimes="0;.5;1" keySplines=".45 0 .55 1;.45 0 .55 1"/>'
                 '<circle cx="%d" cy="272" r="8" fill="%s" opacity=".35" filter="url(#glowf)"/><circle cx="%d" cy="272" r="4.2" fill="%s"/></g>' % (3 + i * .4, f2(i * .7), cx, EL[e], cx, EL[e]))
    d.append('</g><rect x=".75" y=".75" width="%s" height="%s" rx="17.5" fill="none" stroke="%s" stroke-opacity="%s" stroke-width="1.5"/></svg>' % (W - 1.5, H - 1.5, '#D3BC8E' if dark else '#B8944A', '.5' if dark else '.7'))
    return '\n'.join(d)

# ------------------------------------------------------------------ note of the day
def note_svg(lines, label='NOTE OF THE DAY'):
    W, H = 640, 170
    d = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-label="Note of the day: %s">' % (W, H, W, H, esc(' '.join(lines)))]
    d.append('<title>Note of the day</title><defs><linearGradient id="p" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFFBF0"/><stop offset="1" stop-color="#F3EAD3"/></linearGradient></defs>')
    d.append('<rect x="2" y="2" width="%d" height="%d" rx="12" fill="url(#p)" stroke="#C9A24E" stroke-width="1.6"/><rect x="9" y="9" width="%d" height="%d" rx="8" fill="none" stroke="#D3BC8E" stroke-width=".8"/>' % (W - 4, H - 4, W - 18, H - 18))
    d.append(sparkle(36, 36, 10, '#C9A24E') + sparkle(W - 36, H - 36, 10, '#C9A24E') + sparkle(W - 32, 32, 5, '#D3BC8E') + sparkle(32, H - 32, 5, '#D3BC8E'))
    d.append(text('cinzel_bold', label, 12, W / 2, 40, '#9A6B1E', 'middle', 3.4))
    y = 82 if len(lines) > 1 else 94
    for ln in lines:
        d.append(text('cinzel_semibold', ln, 24, W / 2, y, '#2B3142', 'middle')); y += 32
    d.append(text('nunito_sans_regular', 'my own words', 12.5, W / 2, H - 22, '#6b6f7e', 'middle'))
    d.append('</svg>')
    return '\n'.join(d)

# ------------------------------------------------------------------ spotlight of the week
def spotlight_svg(app, week):
    W, H = 1000, 250; col = EL[app['el']]; d = []
    d.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-label="Spotlight of the week: %s, %d stars. %s">' % (W, H, W, H, esc(app['name']), app['stars'], esc(app['line'])))
    d.append('<title>This week\'s spotlight: %s</title><defs>' % esc(app['name']))
    d.append('<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#171d3a"/><stop offset="1" stop-color="#0b0f1e"/></linearGradient>')
    d.append('<radialGradient id="neb" cx=".2" cy=".5" r=".6"><stop offset="0" stop-color="%s" stop-opacity=".45"/><stop offset="1" stop-color="%s" stop-opacity="0"/></radialGradient>' % (col, col))
    d.append('<linearGradient id="nm" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFF1C9"/><stop offset=".5" stop-color="#F3D79C"/><stop offset="1" stop-color="#C9A24E"/></linearGradient>')
    d.append('<clipPath id="rr"><rect width="%d" height="%d" rx="16"/></clipPath><clipPath id="ic"><rect x="62" y="64" width="124" height="124" rx="28"/></clipPath></defs>' % (W, H))
    d.append('<g clip-path="url(#rr)"><rect width="%d" height="%d" fill="url(#bg)"/><rect width="%d" height="%d" fill="url(#neb)"/>' % (W, H, W, H))
    r = random.Random(week + 5)
    for i in range(70):
        x, y = r.random() * W, r.random() * H; rr = .5 + r.random() ** 2 * 1.4; dur = 3 + r.random() * 4
        d.append('<circle cx="%s" cy="%s" r="%s" fill="#fff" opacity=".5"><animate attributeName="opacity" values=".15;.9;.15" dur="%ss" begin="-%ss" repeatCount="indefinite"/></circle>' % (f2(x), f2(y), f2(rr), f2(dur), f2(r.random() * dur)))
    d.append(sparkle(840, 80, 74, col, 'opacity=".1"') + sparkle(930, 180, 34, '#F3D79C', 'opacity=".15"') + sparkle(740, 196, 22, col, 'opacity=".2"'))
    d.append('<circle cx="124" cy="126" r="86" fill="#0d1220" fill-opacity=".7" stroke="%s" stroke-width="2.4"/><circle cx="124" cy="126" r="98" fill="none" stroke="%s" stroke-opacity=".3" stroke-width="5"/>' % (col, col))
    icon = ICONS.get(app.get('icon') or '')
    if icon: d.append('<image href="%s" x="62" y="64" width="124" height="124" clip-path="url(#ic)"/>' % icon)
    else: d.append(glyph(app['el'], 124, 126, 84, col, 1.7))
    d.append(text('cinzel_regular', 'THIS WEEK’S SPOTLIGHT   ·   ' + app['kind'], 14, 252, 66, '#D3BC8E', 'start', 3.4))
    size = 48 if len(app['name']) > 9 else 58
    d.append(text('cinzel_bold', app['name'], size, 250, 130, 'url(#nm)', 'start', 1))
    d.append(text('nunito_sans_semibold', app['line'], 19, 252, 168, '#C9CCDA'))
    for s in range(5):
        d.append('<polygon points="%s" fill="%s"/>' % (star_pts(262 + s * 28, 206, 11.5), '#F3D79C' if s < app['stars'] else '#3a4270'))
    d.append('</g><rect x=".75" y=".75" width="%s" height="%s" rx="15.5" fill="none" stroke="#D3BC8E" stroke-opacity=".45" stroke-width="1.5"/></svg>' % (W - 1.5, H - 1.5))
    return '\n'.join(d)

# ------------------------------------------------------------------ levelling bars
def level_svg(theme, skills):
    dark = theme == 'dark'; W = 640; row = 46; H = 92 + len(skills) * row
    bg = '#0D1220' if dark else '#F6F1E7'; ink = '#ECE5D8' if dark else '#2B3142'; dim = '#B1B4C0' if dark else '#545866'
    hi = '#F3D79C' if dark else '#8A5A12'; track = '#222b4d' if dark else '#E1D6BB'; line = 'rgba(211,188,142,.4)' if dark else 'rgba(140,110,50,.4)'
    d = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-label="Levelling up, self-rated: %s">' % (
        W, H, W, H, esc(', '.join('%s level %d of %d' % (s['name'], s['level'], s['max']) for s in skills)))]
    d.append('<title>Currently levelling up</title><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#C9A24E"/><stop offset="1" stop-color="#F3D79C"/></linearGradient></defs>')
    d.append('<rect x=".5" y=".5" width="%d" height="%d" rx="12" fill="%s" stroke="%s"/>' % (W - 1, H - 1, bg, line))
    d.append(text('cinzel_bold', 'CURRENTLY LEVELLING UP', 17, 28, 40, hi, 'start', 2))
    d.append(text('nunito_sans_regular', 'Self-rated. Honest, mostly.', 13, W - 28, 40, dim, 'end'))
    for i, s in enumerate(skills):
        y = 84 + i * row; stars = min(5, s['level'] // 4); frac = max(0, min(1, s['level'] / float(s['max'])))
        d.append(text('nunito_sans_bold', s['name'], 15, 28, y, ink))
        for k in range(5): d.append('<polygon points="%s" fill="%s"/>' % (star_pts(W - 232 + k * 18, y - 5, 7.5), ('#F3D79C' if dark else '#C9953E') if k < stars else track))
        d.append(text('nunito_sans_regular', 'Lv %d / %d' % (s['level'], s['max']), 13, W - 28, y, dim, 'end'))
        d.append('<rect x="28" y="%d" width="%d" height="8" rx="4" fill="%s"/>' % (y + 10, W - 56, track))
        d.append('<rect x="28" y="%d" width="0" height="8" rx="4" fill="url(#g)"><animate attributeName="width" from="0" to="%s" dur="1.1s" begin="%ss" fill="freeze"/></rect>' % (y + 10, f2(frac * (W - 56)), f2(i * .12)))
    d.append('</svg>')
    return '\n'.join(d)

# ------------------------------------------------------------------ README blocks
def inline_md(s):
    """Tiny safe subset: *italic* only. Everything else is plain text."""
    out, parts = [], esc(s).split('*')
    for i, p in enumerate(parts): out.append('<i>%s</i>' % p if i % 2 else p)
    return ''.join(out)

def now_block(items):
    rows = []
    for it in items:
        rows.append('  <tr>\n    <td width="80" align="center"><img src="%s" width="64" alt="%s icon"></td>\n    <td><b>%s</b>, %s%s</td>\n  </tr>' % (
            esc(it['icon']), esc(it['app']), esc(it['app']), inline_md(it['text']), (' <i>%s</i>' % esc(it['status'])) if it.get('status') else ''))
    return '<table>\n' + '\n'.join(rows) + '\n</table>'

def ago(pushed, today):
    d = datetime.datetime.fromisoformat(pushed.replace('Z', '+00:00')).date(); n = (today - d).days
    if n <= 0: return 'today'
    if n == 1: return 'yesterday'
    if n < 14: return '%d days ago' % n
    if n < 60: return '%d weeks ago' % (n // 7)
    return d.strftime('%d %b %Y').lstrip('0')

def short(s, n=88):
    s = ' '.join((s or '').split())
    if len(s) <= n: return s
    for sep in (': ', '. ', '; '):          # prefer a clean stop at the first clause
        i = s.find(sep)
        if 25 <= i <= n: return s[:i].rstrip(',;:.')
    cut = s[:n].rsplit(' ', 1)[0].rstrip(',;:.')
    return cut + '...'

def recent_block(repos, today, user, names, exclude, limit=5):
    rows = []
    for r in sorted([r for r in repos if not r.get('fork') and not r.get('private') and r['name'] not in exclude], key=lambda r: r['pushed_at'], reverse=True)[:limit]:
        nm = names.get(r['name'], r['name'])
        rows.append('| [%s](https://github.com/%s/%s) | %s | %s |' % (nm.replace('|', ' '), user, r['name'], short(r.get('description')).replace('|', '/'), ago(r['pushed_at'], today)))
    if not rows: return '*Nothing to show yet.*'
    return '| Project | What it is | Last updated |\n| --- | --- | --- |\n' + '\n'.join(rows)

# ------------------------------------------------------------------ public activity graph (drawn here, no outside host)
def activity_counts(events, today, days=31):
    """How many public events (pushes, new repos, releases, ...) on each of the last `days` days (UTC). Oldest first."""
    counts = [0] * days
    for e in events:
        try: d = datetime.date.fromisoformat(e['created_at'][:10])
        except Exception: continue
        i = days - 1 - (today - d).days
        if 0 <= i < days: counts[i] += 1
    return counts

def activity_svg(theme, counts, today):
    dark = theme == 'dark'; W, H = 900, 280; n = len(counts)
    bg = '#0D1220' if dark else '#F6F1E7'; ink = '#ECE5D8' if dark else '#2B3142'; dim = '#B1B4C0' if dark else '#545866'
    hi = '#F3D79C' if dark else '#8A5A12'; gold = '#D3BC8E' if dark else '#A9692C'; line = 'rgba(211,188,142,.35)' if dark else 'rgba(140,110,50,.4)'
    top = max(4, int(math.ceil(max(counts) / 2.0)) * 2) if counts else 4
    L, R, T, B = 58, W - 30, 70, 214
    X = lambda i: L + i * (R - L) / float(n - 1)
    Y = lambda v: B - v * (B - T) / float(top)
    d = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-label="Public activity on GitHub over the last %d days: %d events in total.">' % (W, H, W, H, n, sum(counts))]
    d.append('<title>Public activity, last %d days</title><defs><linearGradient id="ar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="%s" stop-opacity=".5"/><stop offset="1" stop-color="%s" stop-opacity="0"/></linearGradient></defs>' % (n, gold, gold))
    d.append('<rect x=".5" y=".5" width="%d" height="%d" rx="12" fill="%s" stroke="%s"/>' % (W - 1, H - 1, bg, line))
    d.append(text('cinzel_bold', 'PUBLIC ACTIVITY, LAST %d DAYS' % n, 16, W / 2, 40, hi, 'middle', 2.4))
    for g in range(0, top + 1, max(1, top // 4)):
        d.append('<line x1="%d" x2="%d" y1="%s" y2="%s" stroke="%s" stroke-dasharray="3 5"/>' % (L, R, f2(Y(g)), f2(Y(g)), line))
        d.append(text('nunito_sans_regular', str(g), 12, L - 12, Y(g) + 4, dim, 'end'))
    for i in range(n):
        day = today - datetime.timedelta(days=n - 1 - i)
        if i % 5 == 0 or i == n - 1: d.append(text('nunito_sans_regular', str(day.day), 12, X(i), B + 22, dim, 'middle'))
    pts = ['%s %s' % (f2(X(i)), f2(Y(v))) for i, v in enumerate(counts)]
    d.append('<path d="M%s L%s L%s Z" fill="url(#ar)"/>' % (' L'.join(pts), f2(X(n - 1)) + ' ' + str(B), f2(X(0)) + ' ' + str(B)))
    d.append('<path d="M%s" fill="none" stroke="%s" stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="0"><animate attributeName="stroke-dashoffset" values="1;0" dur="2.2s" begin="0s" fill="freeze"/></path>' % (' L'.join(pts), hi))
    for i, v in enumerate(counts):
        if v: d.append('<circle cx="%s" cy="%s" r="3.6" fill="%s" stroke="%s" stroke-width="2"/>' % (f2(X(i)), f2(Y(v)), bg, gold))
    d.append(text('nunito_sans_regular', 'Pushes, new repos and releases a day, from GitHub\u2019s public feed', 12.5, W / 2, H - 14, dim, 'middle'))
    d.append('</svg>')
    return '\n'.join(d)
