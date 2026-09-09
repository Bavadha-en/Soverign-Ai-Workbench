# Industrial Inspection Sample Images Dataset

This directory contains curated, representative sample industrial inspection images and scanned technical logs for out-of-the-box demonstration of the Sovereign AI Workbench's Multimodal Vision (Moondream / LLaVA / LLaMA-Vision) and OCR extraction capabilities.

## Included Inspection Sample Images

| Filename | Type / Component | Defect / Feature | Recommended Vision / Agent Prompt |
| :--- | :--- | :--- | :--- |
| `metal_nut_surface_scratch.png` | Fastener / Hardware | Severe longitudinal scratch across thread & outer flank | *"Perform multimodal visual defect inspection on this metal fastener. Identify any surface scratches or thread anomalies."* |
| `metal_nut_bent_deformation.png` | Mechanical Component | Plastic deformation / bent structural geometry | *"Inspect this industrial hardware component for geometric deformation, bending, or physical anomalies."* |
| `cable_insulation_cut.png` | Electrical Cabling | Cut outer insulation exposing inner shielding | *"Analyze this electrical cable inspection image. Detect any cuts in the insulation or conductor exposure."* |
| `structural_surface_crack.png` | Material / Cladding | Linear fracture / stress crack indication | *"Inspect this structural material surface. Identify any linear cracks, fractures, or stress corrosion lines."* |
| `scanned_inspection_sheet.png` | Scanned Document / Form | Printed & handwritten industrial maintenance log | *"Extract text and structured tabular inspection readings from this scanned document using offline OCR."* |

## Usage in Workbench Demos

### 1. Web UI (One-Click Selection)
In the ConfigIQ Sovereign Workbench interface, select the **Industrial Image Inspection** preset or click on the sample image badges to attach the sample inspection image without needing to upload external files.

### 2. Python API / Agent Execution
```python
import requests

# Upload sample image to local storage
with open("datasets/sample_images/metal_nut_surface_scratch.png", "rb") as f:
    upload_res = requests.post("http://localhost:8000/documents/upload", files={"file": f}).json()

doc_id = upload_res["document_id"]

# Run autonomous inspection agent
run_res = requests.post("http://localhost:8000/agent/run", json={
    "task": "Perform visual defect inspection on uploaded component and extract anomaly bounding data.",
    "document_ids": [doc_id]
}).json()

print(run_res)
```
