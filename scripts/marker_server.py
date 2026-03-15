"""
Marker PDF API server - runs on GPU server only.

Setup on GPU server:
  ssh xyzxyzserver
  conda activate vivriti
  pip install fastapi uvicorn
  python scripts/marker_server.py

Exposes Marker as REST API on port 8001.
Models load into A100 on first request and stay cached.
"""
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import os
import tempfile

import uvicorn


app = FastAPI(title="Marker PDF API")

_converter = None


def get_converter():
    global _converter
    if _converter is None:
        from marker.converters.pdf import PdfConverter
        from marker.models import create_model_dict

        _converter = PdfConverter(artifact_dict=create_model_dict())
    return _converter


@app.get("/health")
def health():
    import torch

    return {
        "status": "ok",
        "cuda_available": torch.cuda.is_available(),
        "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
    }


@app.post("/convert")
async def convert_pdf(pdf_file: UploadFile = File(...)):
    converter = get_converter()
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(await pdf_file.read())
        tmp_path = tmp.name
    try:
        rendered = converter(tmp_path)
        return JSONResponse({"markdown": rendered.markdown, "success": True})
    except Exception as exc:
        return JSONResponse(
            {"markdown": "", "success": False, "error": str(exc)},
            status_code=500,
        )
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
