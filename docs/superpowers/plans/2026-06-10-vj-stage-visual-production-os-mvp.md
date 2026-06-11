# VJ Stage Visual Production OS MVP Implementation Plan

Goal: build a local React/Vite + FastAPI MVP that creates stage visual projects, stores screen specs, runs QC, and generates production folders, pixel maps, AE JSX, C4D Python, and delivery markdown.

Architecture: `backend/` owns SQLite persistence and filesystem generation. `frontend/` calls the FastAPI API and previews projects, QC, screens, and generated artifacts.

Implemented scope:

- Backend models, SQLite database, sample seed data, FastAPI routes, QC, and production package generation.
- Pixel map PNGs, safe-area PNG, SVG mask, mapping JSON, AE JSX, C4D Python, screen spec, QC report, and delivery markdown.
- React/Vite UI for project creation, screen entry, QC, generation, stage preview, and Chinese/English switching.
- Backend and frontend test coverage plus GitHub Actions CI.
