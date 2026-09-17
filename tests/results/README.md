# Test result reports

QA commits reports here (`SLICE_*.md`, feature names) **after** UAT/dogfood.

## Why `git pull` keeps aborting

A local agent often writes the **same path** (e.g. `CHUNK_ROLES.md`) as an untracked file while GitHub already has a commit of that file. Git will not overwrite untracked files.

**Do not** `git add .` to get past that. You will commit junk (`Untitled`) and diverge from origin.

```bash
mkdir -p tests/results/local
mv tests/results/THE_FILE.md tests/results/local/
git pull
```

`tests/results/local/` is gitignored. Drafts belong there until QA owns the canonical report.

## Cursor Source Control empty

Committed files do not show as edits. Untracked scratch used to clutter the view; it is ignored now. If the tree is dirty and Cursor still shows nothing, confirm the window folder is `/Users/marcbreneiser/Code/ragged` and run **Git: Refresh**.
