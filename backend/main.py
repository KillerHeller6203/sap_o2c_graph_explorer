import os
import shutil
from fastapi import FastAPI, Query, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from database import engine, Base
from ingest import ingest, TABLE_CONFIGS, DATA_DIR
from llm import process_nl_query, get_graph_data

# Ensure tables exist and data is loaded
Base.metadata.create_all(bind=engine)
ingest()

app = FastAPI(title="SAP O2C Graph Query API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Valid entity type folders (derived from ingest config)
VALID_ENTITY_TYPES = [folder for folder, _, _ in TABLE_CONFIGS]


class QueryRequest(BaseModel):
    query: str


@app.post("/query")
def submit_query(request: QueryRequest):
    return process_nl_query(request.query)


@app.get("/graph")
def graph_data(limit: int = Query(default=30, ge=5, le=100)):
    return get_graph_data(limit=limit)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/entity-types")
def entity_types():
    """Return the list of valid entity type folder names."""
    return {"entity_types": VALID_ENTITY_TYPES}


@app.post("/upload")
async def upload_file(
    entity_type: str = Form(...),
    file: UploadFile = File(...),
):
    """Accept a .jsonl file, save it to the correct data subfolder, then re-ingest."""
    # Validate entity type
    if entity_type not in VALID_ENTITY_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid entity_type '{entity_type}'. Must be one of: {VALID_ENTITY_TYPES}"
        )

    # Validate file extension
    if not file.filename.endswith(".jsonl"):
        raise HTTPException(status_code=400, detail="Only .jsonl files are accepted.")

    # Save file to data/<entity_type>/
    dest_dir = os.path.join(DATA_DIR, entity_type)
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, file.filename)

    try:
        with open(dest_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
    finally:
        file.file.close()

    # Re-run ingest to load new data into SQLite
    try:
        # Temporarily clear the "already ingested" check by removing row-count gate
        # ingest() uses INSERT OR IGNORE so it's safe to call repeatedly
        ingest()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File saved but ingest failed: {e}")

    return JSONResponse({"status": "ok", "message": f"File '{file.filename}' uploaded and ingested for '{entity_type}'."})


# Serve frontend
os.makedirs("static", exist_ok=True)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
