import os
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from database import engine, Base
from ingest import ingest
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


# Serve frontend
os.makedirs("static", exist_ok=True)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
