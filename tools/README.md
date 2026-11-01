# What runs every day

`.github/workflows/profile.yml` runs `tools/update.py` once a day at 03:17 UTC (and whenever you press **Run workflow** in the Actions tab). The script uses only Python's built-in tools: nothing to install, no secrets.

It rewrites these, and only saves a commit when something really changed:

| What | Where it shows | Where the content comes from |
| --- | --- | --- |
| Moon banner (tonight's real phase, the month's sky) | top of the README | the date: plain moon maths, no website |
| Note of the day | "Note of the day" | the `notes` list in `profile.json` |
| Spotlight of the week | "This week's spotlight" | the `apps` list in `profile.json`, **public repos only** |
| Character cards and app links | "My apps, as a party" | the `apps` list, plus which repos are public |
| Project list | folded list "All my projects" | the `projects` list, plus which repos are public |
| Now building | "Now building" | the `now` list in `profile.json` |
| Levelling bars | "My stack, and what I'm levelling up" | the `levelling` list in `profile.json` |
| Recently updated | folded list near the bottom | GitHub's public repo list |
| Public activity graph | under "GitHub stats" | GitHub's public activity feed |
| The frame (top edge, bottom edge, dividers) | round the whole README | `frame` in `profile.json` |

## The frame

The decorative border round the README is made of pictures, because GitHub removes all styling: a top edge (`art/frame-top-*.svg`), a bottom edge and a thin divider above each section. The robot rewrites the two edges (the `FRAMETOP` and `FRAMEBOTTOM` blocks) and the six pictures every day from `tools/frame_art.py`, so they can't get lost; the dividers are plain lines in the README and are never touched. Before it writes anything, `update.py` checks that every word outside the marked blocks comes out unchanged.

Change the style by editing one line in `profile.json`: `"frame": {"style": "teyvat", "shape": "bookends"}`. Styles: `teyvat` (ornate gold), `moon` (slim moon-silver), `sumeru` (leaves). The shape `boxed` wraps everything in a table but GitHub draws its sides grey and can squeeze the page, so `bookends` is the one to use.

## Public and private repos

Every day the script asks GitHub which of your repos are really public. A **public** repo gets a link; a **private** one shows its card with a small "private for now" mark and no link, and it is skipped by the spotlight. Make a repo public and the next daily run turns its card into a link by itself. (`public` in `profile.json` is only a fallback for when GitHub can't be reached.)

If you rename a repo, change its `repo` value in `profile.json` (GitHub forwards old links, but the public check uses the new name).

## You edit one file: `profile.json`

It is **public**, so write only what you would say out loud. Change a number, add a note (use `|` where the line should break), add what you are building. The next daily run (or a manual run) picks it up.

## Two rules

- Never put a password or token in the README, in `profile.json` or in the workflow. The workflow does not need one.
- Never copy text from private notes or task files into `profile.json`.

## Try it without changing anything

```
python tools/update.py --dry-run --offline --date 2026-11-24
```

`--dry-run` shows what would change and writes nothing. `--date` pretends it is that day (handy for seeing every moon phase and season).

The letters inside the pictures are drawn from `glyphs.json` (Cinzel and Nunito Sans, both under the SIL Open Font License), so the pictures look the same on every computer. `icons.json` holds small copies of your app icons for the spotlight.
