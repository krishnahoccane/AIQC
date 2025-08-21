from fastapi import FastAPI, UploadFile, File

app = FastAPI()

@app.post("/process_audio")
async def process_audio(file: UploadFile = File(...)):
    return {"filename": file.filename}
