# VJ Stage Visual Production OS Backend

FastAPI service for project intake, screen specs, QC, and local production package generation.

## Run

```powershell
python -m pip install -r backend/requirements.txt
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

## Test

```powershell
python -m pytest backend/tests -v
```

## Key Routes

- `GET /health`
- `GET /projects`
- `POST /projects`
- `GET /projects/{project_id}`
- `GET /projects/{project_id}/screens`
- `POST /projects/{project_id}/screens`
- `GET /projects/{project_id}/qc`
- `POST /projects/{project_id}/generate`

Generated packages are written to `exports/<Project_Name>/` by default.
