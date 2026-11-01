"""README blocks that depend on which repos are public: character cards, constellation links, project list, spotlight choice.
Standard library only. Rule: a link is only ever written for a repo that is really public.
Nothing in here names a specific repo: every name comes from profile.json.
"""
import html

def esc(s): return html.escape(str(s), quote=True)

def public_repos(prof, repos):
    """Set of lower-case repo names that are public. GitHub's answer wins; profile.json's 'public' flags are the fallback
    when GitHub can't be reached."""
    if repos is not None:
        return {r['name'].lower() for r in repos if not r.get('private') and not r.get('fork')}, 'GitHub'
    return {p['repo'].lower() for p in prof['projects'] if p.get('public')}, 'profile.json'

def is_public(repo, pub): return repo.lower() in pub

def url(prof, repo): return 'https://github.com/%s/%s' % (prof['user'], repo)

def spotlight_pool(prof, pub):
    pool = [a for a in prof['apps'] if is_public(a['repo'], pub)]
    return pool or []

def cards_block(prof, pub):
    out = ['<p align="center">']
    for a in prof['apps']:
        ok = is_public(a['repo'], pub)
        alt = '%s: %s card, %d stars. %s%s' % (a['name'], a['el'].capitalize(), a['stars'], a['line'], '' if ok else ' Private for now.')
        img = '<img src="art/card-%s%s.svg" width="196" alt="%s">' % (a['id'], '' if ok else '-private', esc(alt))
        out.append('<a href="%s">%s</a>' % (url(prof, a['repo']), img) if ok else img)
    out.append('</p>')
    return '\n'.join(out)

def links_block(prof, pub):
    names, hidden = [], []
    for a in prof['apps']:
        if is_public(a['repo'], pub): names.append('<a href="%s">%s</a>' % (url(prof, a['repo']), esc(a['name'])))
        else: names.append(esc(a['name'])); hidden.append(a['name'])
    out = '<p align="center">' + ' &middot; '.join(names) + '</p>'
    if hidden:
        if len(hidden) > 1: lst = ', '.join(hidden[:-1]) + ' and ' + hidden[-1]
        else: lst = hidden[0]
        out += '\n\n<p align="center"><sub>%s %s private for now.</sub></p>' % (esc(lst), 'are' if len(hidden) > 1 else 'is')
    return out

def projects_block(prof, pub):
    groups, order = {}, []
    for p in prof['projects']:
        if p['group'] not in groups: groups[p['group']] = []; order.append(p['group'])
        groups[p['group']].append(p)
    n_pub = sum(1 for p in prof['projects'] if is_public(p['repo'], pub)); n_priv = len(prof['projects']) - n_pub
    summary = 'All my projects (%d public%s)' % (n_pub, (', %d private for now' % n_priv) if n_priv else '')
    parts = []
    for g in order:
        parts.append('### %s\n\n| Project | What it is |\n| --- | --- |' % g)
        extra = []
        for p in groups[g]:
            what = p['what'].replace('|', '/')
            if is_public(p['repo'], pub): parts.append('| [%s](%s) | %s |' % (p['name'], url(prof, p['repo']), what))
            else: parts.append('| %s *(private for now)* | %s |' % (p['name'], what))
            if p.get('after'): extra.append(p['after'])
        parts.append('')
        for e in extra: parts.append(e + '\n')
    return '<details>\n<summary>%s</summary>\n\n%s\n</details>' % (summary, '\n'.join(parts).strip('\n') + '\n')
