import asyncio

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse

from api.worker import process_ocr


app = FastAPI()

@app.post("/ocr/")
async def ocr(file: UploadFile = File(...), lang: str = "swe"):
    # Load image from upload
    image_bytes = await file.read()

    task = process_ocr.delay(image_bytes)

    # Wait for result (polling Redis backend)
    while not task.ready():
        await asyncio.sleep(0.2)

    result = task.result

    return JSONResponse({"extracted_text": result['text']})
