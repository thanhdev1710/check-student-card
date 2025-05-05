from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from ocr import process_ocr

app = FastAPI()

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ping")
async def ping():
    return {"message": "pong"}


@app.post("/ocr")
async def ocr_endpoint(file: UploadFile = File(...)):
    result = process_ocr(file)
    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])
    return result
