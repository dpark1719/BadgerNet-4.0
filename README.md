# BadgerNet 4.0

Visualization project for **UW–Madison** student origins and alumni-style outcomes: **Industry**, **Post-grad education**, **International outcomes**, and **three Student origins tabs** (undergraduate, graduate, doctorate), with **1y / 5y / 10y trend** charts where data provides series.

- **Code repository:** [github.com/dpark1719/BadgerNet-4.0](https://github.com/dpark1719/BadgerNet-4.0)
- **GitHub Project board:** [github.com/users/dpark1719/projects/2](https://github.com/users/dpark1719/projects/2)
- **Data contract:** [DATA_CONTRACT.md](./DATA_CONTRACT.md)
- **Collaboration:** [CONTRIBUTING.md](./CONTRIBUTING.md)

## Repo layout

| Path | Owner (convention) | Purpose |
|------|-------------------|---------|
| `backend/` | **David** | ETL, downloads, JSON generators, LinkedIn aggregate harvest (local secrets) |
| `frontend/` | **Rohan** | React UI, charts, deployment (when you choose a host) |
| `frontend/public/data/` | **David** generates | Static bundles the UI loads |
| `data/raw/` | **David** (local, gitignored) | Cached CSVs / exports |

## Quick start

### Backend (sample data)

```bash
cd backend && python3 scripts/generate_sample_data.py
```

### Frontend

```bash
cd frontend && npm install && npm run dev
```

Open the printed local URL (usually `http://localhost:5173`).

## Git remote

```bash
git remote add origin https://github.com/dpark1719/BadgerNet-4.0.git
git push -u origin main
git push -u origin david/backend
git push -u origin rohan/frontend
```

If the GitHub repo already has commits (e.g. a placeholder README), reconcile with `git pull origin main --allow-unrelated-histories` and merge, or coordinate a one-time force-with-lease after backup.

## Branches

- `main` — integration; keep deployable.
- `david/backend` — David’s default branch for data and scripts.
- `rohan/frontend` — Rohan’s default branch for UI and deploy.

See [CONTRIBUTING.md](./CONTRIBUTING.md) for how to avoid merge pain.
