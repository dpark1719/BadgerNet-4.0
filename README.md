# BadgerNet 4.0

Visualization project for **UW–Madison** student origins and alumni-style outcomes across four tabs: **Industry**, **Post-grad education**, **International outcomes**, and **Student origins**.

- **GitHub Project board:** [github.com/users/dpark1719/projects/2](https://github.com/users/dpark1719/projects/2)
- **Data contract:** [DATA_CONTRACT.md](./DATA_CONTRACT.md)
- **Collaboration:** [CONTRIBUTING.md](./CONTRIBUTING.md)

## Repo layout

| Path | Owner (convention) | Purpose |
|------|-------------------|---------|
| `backend/` | **David** | ETL, downloads, JSON generators |
| `frontend/` | **Rohan** | React UI, charts, styling |
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

## Branches

- `main` — integration; keep deployable.
- `david/backend` — David’s default branch for data and scripts.
- `rohan/frontend` — Rohan’s default branch for UI.

See [CONTRIBUTING.md](./CONTRIBUTING.md) for how to avoid merge pain.
