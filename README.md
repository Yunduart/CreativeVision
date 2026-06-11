# VJ Project OS

This workspace contains two related local prototypes:

- Existing root Next.js prototype for VJ project management.
- New MVP in `backend/` and `frontend/` for a VJ / Stage Visual Production OS generator.

The new MVP keeps the requested stack isolated from the existing Next app:

- Frontend: React + Vite
- Backend: Python FastAPI
- Geometry: Shapely
- Image generation: Pillow + OpenCV dependency
- SVG generation: svgwrite
- Video wrapper: FFmpeg CLI probe wrapper
- Database: SQLite
- Output: local filesystem packages under `exports/`

## Run The MVP Backend

```powershell
python -m pip install -r backend/requirements.txt
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

Backend routes:

- `GET /health`
- `GET /projects`
- `POST /projects`
- `GET /projects/{project_id}`
- `GET /projects/{project_id}/screens`
- `POST /projects/{project_id}/screens`
- `GET /projects/{project_id}/qc`
- `POST /projects/{project_id}/generate`

## Run The MVP Frontend

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Open `http://127.0.0.1:5173`.

## Test And Build

```powershell
python -m pytest backend/tests -v
cd frontend
npm.cmd run build
```

## Generated Package

`POST /projects/{project_id}/generate` creates:

- `00_Input`
- `01_Analysis`
- `02_ScreenSpec`
- `03_PixelMap`
- `04_AE`
- `05_C4D`
- `06_Export`
- `07_Onsite`
- `08_Archive`

Generated files include:

- `01_Analysis/qc_report.md`
- `02_ScreenSpec/screen_spec.md`
- `03_PixelMap/project_pixelmap_full.png`
- `03_PixelMap/project_pixelmap_numbered.png`
- `03_PixelMap/project_pixelmap_safearea.png`
- `03_PixelMap/project_pixelmap_mask.svg`
- `03_PixelMap/project_mapping.json`
- `04_AE/create_project.jsx`
- `05_C4D/create_stage_scene.py`
- `07_Onsite/delivery_spec.md`

Sample project data is available at `sample_data/sample_project.json`.
