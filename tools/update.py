#!/usr/bin/env python3
"""Daily update for Shamil's GitHub profile README. Standard library only.

What it rewrites (nothing else is touched):
  art/banner-dark.svg, art/banner-light.svg   tonight's real moon phase + the season's sky
  art/note.svg                                the note of the day (his own lines in profile.json)
  art/spotlight.svg                           this week's spotlight app
  art/levelling-dark.svg, -light.svg          the levelling bars (profile.json)
  art/activity-dark.svg, -light.svg           public activity of the last 31 days (GitHub's public events feed)
  README.md, between pairs of <!--NAME:START--> / <!--NAME:END--> lines:
     BANNER, NOTE, SPOTLIGHT, LEVEL, NOW (profile.json), RECENT and ACTIVITY (public GitHub API),
     CARDS, LINKS and PROJECTS (profile.json + which repos GitHub says are public: only public repos get a link)

It only writes a file when its content really changed, so the workflow only commits real changes.
It uses no secrets: the optional GITHUB_TOKEN is the workflow's own temporary token, used read-only
to ask GitHub for his PUBLIC repos. No network is needed for anything else.

Try it safely:   python tools/update.py --dry-run --date 2026-11-24 --offline
"""
import argparse, datetime, json, os, re, sys, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import profile_art as pa
import profile_blocks as pb

KEYS = ['BANNER', 'NOTE', 'SPOTLIGHT', 'LEVEL', 'NOW', 'RECENT', 'ACTIVITY', 'CARDS', 'LINKS', 'PROJECTS']

def block_re(key):
    return re.compile(r'(<!--%s:START-->)(.*?)(<!--%s:END-->)' % (key, key), re.S)

def put_block(text, key, content):
    return block_re(key).sub(lambda m: m.group(1) + '\n\n' + content.strip('\n') + '\n\n' + m.group(3), text, count=1)

def picture(name, alt, attrs):
    return ('<picture>\n  <source media="(prefers-color-scheme: dark)" srcset="art/%s-dark.svg">\n'
            '  <source media="(prefers-color-scheme: light)" srcset="art/%s-light.svg">\n'
            '  <img alt="%s" src="art/%s-light.svg" %s>\n</picture>') % (name, name, pa.esc(alt), name, attrs)

def fetch_repos(user, token):
    req = urllib.request.Request('https://api.github.com/users/%s/repos?per_page=100&sort=pushed' % user,
                                 headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'profile-readme-updater'})
    if token: req.add_header('Authorization', 'Bearer ' + token)
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode('utf-8'))

def fetch_events(user, token):
    out = []
    for page in (1, 2, 3):
        req = urllib.request.Request('https://api.github.com/users/%s/events/public?per_page=100&page=%d' % (user, page),
                                     headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'profile-readme-updater'})
        if token: req.add_header('Authorization', 'Bearer ' + token)
        with urllib.request.urlopen(req, timeout=25) as r: got = json.loads(r.read().decode('utf-8'))
        out += got
        if len(got) < 100: break
    return out

def build(today, prof, repos, events=None):
    """Return ({relative file: new text}, {block name: new text}, summary lines)."""
    files, blocks, info = {}, {}, []
    age = pa.moon_age(today); season = pa.season_of(today); phase = pa.phase_name(age)
    info.append('moon: %s (day %.1f), season: %s' % (phase, age, season))
    for t in ('dark', 'light'):
        files['art/banner-%s.svg' % t] = pa.banner_svg(t, age, season)
        files['art/levelling-%s.svg' % t] = pa.level_svg(t, prof['levelling'])
    article = 'an' if season == 'autumn' else 'a'
    blocks['BANNER'] = '<p align="center">\n' + picture('banner', "Shamil: student, gamer, PC builder. Tonight's moon: %s, under %s %s sky." % (phase.lower(), article, season), 'width="100%"') + '\n</p>'
    notes = prof['notes']; note = notes[today.toordinal() % len(notes)].split('|')
    files['art/note.svg'] = pa.note_svg(note)
    blocks['NOTE'] = '<p align="center">\n<img alt="Note of the day: %s" src="art/note.svg" width="460">\n</p>' % pa.esc(' '.join(note))
    info.append('note: ' + ' '.join(note))
    pub, src = pb.public_repos(prof, repos)
    iso = today.isocalendar(); week = iso[0] * 53 + iso[1]; pool = pb.spotlight_pool(prof, pub)
    if pool:
        app = pool[week % len(pool)]
        files['art/spotlight.svg'] = pa.spotlight_svg(app, week)
        blocks['SPOTLIGHT'] = (('<p align="center">' + chr(10) + '<a href="%s"><img alt="This week&#x27;s spotlight: %s, %d stars. %s" src="art/spotlight.svg" width="100%%"></a>' + chr(10) + '</p>')
                               % (pb.url(prof, app['repo']), pa.esc(app['name']), app['stars'], pa.esc(app['line'])))
        info.append('spotlight: %s (week %d, chosen from %d public apps)' % (app['name'], iso[1], len(pool)))
    else:
        info.append('spotlight: no public app, left as it is')
    blocks['CARDS'] = pb.cards_block(prof, pub); blocks['LINKS'] = pb.links_block(prof, pub); blocks['PROJECTS'] = pb.projects_block(prof, pub)
    info.append('public repos (from %s): %d of %d projects' % (src, sum(1 for p in prof['projects'] if pb.is_public(p['repo'], pub)), len(prof['projects'])))
    blocks['LEVEL'] = '<p align="center">\n' + picture('levelling', 'Levelling up, self-rated: ' + ', '.join('%s level %d of %d' % (s['name'], s['level'], s['max']) for s in prof['levelling']), 'width="560"') + '\n</p>'
    blocks['NOW'] = pa.now_block(prof['now'])
    if repos is not None:
        rc = prof.get('recent', {})
        blocks['RECENT'] = pa.recent_block(repos, today, prof['user'], rc.get('show_as', {}), set(rc.get('hide_repos', [])), rc.get('limit', 5))
        info.append('recent: list rebuilt from %d public repos' % len(repos))
    else:
        info.append('recent: skipped (no repo list), block left as it is')
    if events is not None:
        counts = pa.activity_counts(events, today)
        for t in ('dark', 'light'): files['art/activity-%s.svg' % t] = pa.activity_svg(t, counts, today)
        blocks['ACTIVITY'] = '<p align="center">' + chr(10) + picture('activity', 'Public activity on GitHub over the last 31 days: %d events in total.' % sum(counts), 'width="720"') + chr(10) + '</p>'
        info.append('activity: %d public events in the last 31 days' % sum(counts))
    else:
        info.append('activity: skipped (no events), picture left as it is')
    return files, blocks, info

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--root', default=str(HERE.parent), help='the repo folder (default: the folder above tools/)')
    ap.add_argument('--date', help='pretend today is this date (YYYY-MM-DD), for testing')
    ap.add_argument('--dry-run', action='store_true', help='show what would change, write nothing')
    ap.add_argument('--offline', action='store_true', help='do not call GitHub (leaves the RECENT block alone)')
    ap.add_argument('--events-file', help='read the public events from this JSON file instead of calling GitHub')
    ap.add_argument('--repos-file', help='read the repo list from this JSON file instead of calling GitHub')
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    today = datetime.date.fromisoformat(a.date) if a.date else datetime.datetime.now(datetime.timezone.utc).date()
    prof = json.loads((root / 'profile.json').read_text(encoding='utf-8'))
    readme_p = root / 'README.md'; readme = readme_p.read_text(encoding='utf-8')
    missing = [k for k in KEYS if not block_re(k).search(readme)]
    if missing:
        print('ERROR: README.md is missing the marker lines for: ' + ', '.join(missing), file=sys.stderr); return 1
    repos = None
    if a.repos_file: repos = json.loads(Path(a.repos_file).read_text(encoding='utf-8'))
    elif not a.offline:
        try: repos = fetch_repos(prof['user'], os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN'))
        except Exception as e: print('warning: could not reach GitHub (%s). The recent list stays as it is.' % e)
    events = None
    if a.events_file: events = json.loads(Path(a.events_file).read_text(encoding='utf-8'))
    elif not a.offline:
        try: events = fetch_events(prof['user'], os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN'))
        except Exception as e: print('warning: could not read public events (%s). The activity picture stays as it is.' % e)
    files, blocks, info = build(today, prof, repos, events)
    for line in info: print(' ', line)
    new_readme = readme
    for k, v in blocks.items(): new_readme = put_block(new_readme, k, v)
    changed = []
    for rel, content in files.items():
        p = root / rel
        old = p.read_text(encoding='utf-8') if p.exists() else None
        if old != content:
            changed.append(rel)
            if not a.dry_run:
                p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(content.encode('utf-8'))
    if new_readme != readme:
        changed.append('README.md')
        if not a.dry_run: readme_p.write_bytes(new_readme.encode('utf-8'))
    print(('would change' if a.dry_run else 'changed') + ': ' + (', '.join(changed) if changed else 'nothing'))
    return 0

if __name__ == '__main__':
    sys.exit(main())
