

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse

from api.ocr import ResidencePermitProcessor


app = FastAPI()

@app.post("/ocr/")
async def ocr(file: UploadFile = File(...), lang: str = "swe"):
    # Load image from upload
    image_bytes = await file.read()

    text = ResidencePermitProcessor().process_document(image_bytes, "output.txt")

    if "error" in text:
        return JSONResponse({"error": text["error"]})


    return JSONResponse({"extracted_text": text['translated_text']})
