# Industrial Inspection Sample Images

This folder holds sample images for one-click demos of the Workbench's vision and OCR tools.

**It is empty on purpose.** The earlier samples came from datasets that forbid commercial use, so they were removed:

| Old file | Source | Licence |
| :--- | :--- | :--- |
| `metal_nut_surface_scratch.png` | MVTec AD | CC BY-NC-SA 4.0 (non-commercial) |
| `metal_nut_bent_deformation.png` | MVTec AD | CC BY-NC-SA 4.0 (non-commercial) |
| `cable_insulation_cut.png` | MVTec AD | CC BY-NC-SA 4.0 (non-commercial) |
| `structural_surface_crack.png` | MVTec AD | CC BY-NC-SA 4.0 (non-commercial) |
| `scanned_inspection_sheet.png` | FUNSD | Non-commercial research/education only |

## Adding samples

Only add images you own (your own photos, self-made scans) or that come with a licence allowing commercial use. Record the source and licence of each file in this README.

The samples API lists only files that exist here: `GET /documents/samples/list` returns an empty list until you add some, and `POST /documents/samples/load/{filename}` returns 404 for a missing file. Filenames and titles are defined in `backend/api/documents.py`.
