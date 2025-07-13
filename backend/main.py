"""
FastAPI backend for Whatfix Ticket Analyzer
"""
import os
import logging

# --- GLOBAL LLM CONFIGURATION ---
# This is the most robust way to ensure the correct LLM and API key are used by all components.
# It configures the underlying 'litellm' library that crewAI uses.
os.environ["LITELLM_MODEL"] = "gemini/gemini-2.5"
if "GOOGLE_API_KEY" in os.environ:
    os.environ["LITELLM_API_KEY"] = os.environ["GOOGLE_API_KEY"]

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import tempfile
import asyncio
from concurrent.futures import ThreadPoolExecutor
import numpy as np

# Import the crew
from .crew import TicketAnalysisCrew

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(title="Whatfix Ticket Analyzer API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thread pool for CPU-bound operations
executor = ThreadPoolExecutor(max_workers=2)

# Store for tracking analysis progress
analysis_progress = {}

class AnalysisProgress(BaseModel):
    status: str
    error: Optional[str] = None
    results: Optional[Dict] = None

@app.get("/")
async def root():
    return {"message": "Whatfix Ticket Analyzer API", "version": "1.0.0"}

@app.post("/analyze")
async def analyze_tickets(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    llm_provider: str = "gemini",
    api_key: str = ""
):
    contents = await file.read()
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    import uuid
    analysis_id = str(uuid.uuid4())
    
    analysis_progress[analysis_id] = {"status": "processing", "error": None, "results": None}
    
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv') as tmp_file:
        tmp_file.write(contents)
        tmp_file_path = tmp_file.name
    
    background_tasks.add_task(run_analysis, analysis_id, tmp_file_path, llm_provider, api_key)
    
    return {"analysis_id": analysis_id, "message": "Analysis started"}

async def run_analysis(analysis_id: str, file_path: str, llm_provider: str, api_key: str):
    try:
        # The API key from the UI is now used to set the environment variable if it's not already set.
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
            os.environ["LITELLM_API_KEY"] = api_key

        crew = TicketAnalysisCrew(file_path, llm_provider, api_key)
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(executor, crew.run)
        
        analysis_progress[analysis_id]["status"] = "completed"
        analysis_progress[analysis_id]["results"] = results
        
    except Exception as e:
        logging.error(f"An error occurred during analysis for ID {analysis_id}:", exc_info=True)
        analysis_progress[analysis_id]["status"] = "error"
        analysis_progress[analysis_id]["error"] = str(e)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

def convert_numpy(obj):
    if isinstance(obj, np.integer): return int(obj)
    if isinstance(obj, np.floating): return float(obj)
    if isinstance(obj, np.ndarray): return obj.tolist()
    if isinstance(obj, dict): return {k: convert_numpy(v) for k, v in obj.items()}
    if isinstance(obj, list): return [convert_numpy(i) for i in obj]
    return obj

@app.get("/progress/{analysis_id}", response_model=AnalysisProgress)
async def get_progress(analysis_id: str):
    if analysis_id not in analysis_progress:
        raise HTTPException(status_code=404, detail="Analysis ID not found")
    progress_data = analysis_progress[analysis_id]
    
    # Ensure results are JSON serializable
    if progress_data.get("results"):
        progress_data["results"] = convert_numpy(progress_data["results"])
        
    return progress_data

@app.delete("/analysis/{analysis_id}")
async def cleanup_analysis(analysis_id: str):
    if analysis_id in analysis_progress:
        del analysis_progress[analysis_id]
        return {"message": "Analysis data cleaned up"}
    raise HTTPException(status_code=404, detail="Analysis ID not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)