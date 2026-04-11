# Contributing — David & Rohan

## Branch ownership

| Branch | Primary person | Touch these paths |
|--------|----------------|-------------------|
| `david/backend` | **David** | `backend/`, `data/` (except don’t commit `data/raw/`), `frontend/public/data/*.json` when regenerating datasets |
| `rohan/frontend` | **Rohan** | `frontend/` **except** treat `frontend/public/data/` as **David’s output** — don’t hand-edit JSON unless coordinating |

`main` should always run: regenerate data (if needed) + `npm run build` in `frontend/`.

## How to avoid problems when both work at once

1. **Stay in your lane (directories).** The shared artifact that changes often is `frontend/public/data/*.json` (six tab bundles plus `meta.json`). David owns regenerating it; Rohan consumes it. If Rohan needs new fields, update [DATA_CONTRACT.md](./DATA_CONTRACT.md) first and ping David.

2. **Short-lived merges.** At least once a day (or before a big UI change): merge `main` into your branch (`git merge main` or `git rebase main`) so conflicts stay small.

3. **Coordinate contract changes.** If either of you changes JSON shape, update `DATA_CONTRACT.md` in the **same PR** as the producer or consumer change.

4. **Don’t force-push shared branches.** Avoid `git push --force` on `main`, `david/backend`, or `rohan/frontend` unless you both agree.

5. **PR checklist before merging to `main`.**
   - [ ] `python3 backend/scripts/generate_sample_data.py` (or real pipeline) succeeds
   - [ ] `cd frontend && npm run build` succeeds
   - [ ] New charts show `meta.disclaimer` when `source` is `sample` or `linkedin`

6. **Merge strategy.** Prefer **merge commits** or **squash** into `main` — pick one as a team and stick to it.

## First-time git setup (example)

```bash
git checkout david/backend    # or rohan/frontend
git pull origin main          # if remote exists
# ... work only in your folders ...
git add -A
git commit -m "Describe change"
git push -u origin david/backend
```

Then open a PR into `main` on GitHub.

## Remote

```bash
git remote add origin https://github.com/dpark1719/BadgerNet-4.0.git
git push -u origin main
git push -u origin david/backend
git push -u origin rohan/frontend
```

Link the repository to the [BadgerNet 4.0 project](https://github.com/users/dpark1719/projects/2) in GitHub project settings if you want issues and PRs on that board.
