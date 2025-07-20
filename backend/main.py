"""
FastAPI backend for Whatfix Ticket Analyzer with Arize LLM Observability
"""
import os
import logging
import json

# --- GLOBAL LLM CONFIGURATION ---
# Set default LLM provider if not already set
if "LLM_PROVIDER" not in os.environ:
    os.environ["LLM_PROVIDER"] = "gemini"

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

# Import Arize tracing setup - for LLM observability and monitoring
from .tracing import setup_arize_tracing, get_tracing_status

# Setup logging with enhanced formatting for debugging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
)

app = FastAPI(title="Whatfix Ticket Analyzer API")

# Initialize Arize tracing for LLM observability
# This sets up comprehensive monitoring of CrewAI agents, LLM calls, and workflow execution
logger = logging.getLogger(__name__)
logger.info("Initializing Arize tracing for LLM observability...")

tracing_success = setup_arize_tracing()
if tracing_success:
    logger.info("✅ Arize tracing initialized successfully - LLM calls will be monitored")
else:
    logger.warning("⚠️ Arize tracing not initialized - running without LLM observability")
    logger.info("To enable tracing, set ARIZE_SPACE_ID and ARIZE_API_KEY environment variables")

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
    """
    Root endpoint with system status including tracing information.
    """
    tracing_status = get_tracing_status()
    return {
        "message": "Whatfix Ticket Analyzer API", 
        "version": "1.0.0",
        "tracing": tracing_status
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint with detailed system status.
    """
    tracing_status = get_tracing_status()
    return {
        "status": "healthy",
        "services": {
            "api": "running",
            "llm_tracing": "enabled" if tracing_status["enabled"] else "disabled"
        },
        "tracing": tracing_status
    }

@app.post("/analyze")
async def analyze_tickets(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    llm_provider: Optional[str] = None,
    api_key: Optional[str] = None
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
    
    # Pass optional parameters
    background_tasks.add_task(run_analysis, analysis_id, tmp_file_path, llm_provider, api_key)
    
    return {"analysis_id": analysis_id, "message": "Analysis started"}

async def run_analysis(analysis_id: str, file_path: str, llm_provider: Optional[str], api_key: Optional[str]):
    """
    Execute ticket analysis with comprehensive tracing and error handling.
    
    This function orchestrates the entire CrewAI workflow with full observability
    through Arize tracing, capturing all agent interactions and LLM calls.
    """
    analysis_logger = logging.getLogger(f"analysis.{analysis_id}")
    analysis_logger.info(f"🚀 Starting analysis {analysis_id} with LLM provider: {llm_provider or 'default'}")
    
    # Log tracing status for this analysis
    tracing_status = get_tracing_status()
    analysis_logger.info(f"📊 Tracing status: {'enabled' if tracing_status['enabled'] else 'disabled'}")
    
    try:
        # Create crew with optional parameters - this will be traced by Arize
        analysis_logger.info("🔧 Initializing TicketAnalysisCrew...")
        crew = TicketAnalysisCrew(file_path, llm_provider, api_key)
        analysis_logger.info("✅ TicketAnalysisCrew initialized successfully")
        
        # Run the crew workflow in executor - all agent interactions will be traced
        analysis_logger.info("🎯 Starting CrewAI workflow execution...")
        loop = asyncio.get_running_loop()
        results_str = await loop.run_in_executor(executor, crew.run)
        analysis_logger.info("✅ CrewAI workflow completed successfully")
        
        # Parse the JSON string result with enhanced error handling
        analysis_logger.info("📋 Processing analysis results...")
        try:
            results = json.loads(results_str)
            analysis_logger.info(f"✅ Results parsed successfully - found {len(results.get('ticket_summaries', []))} ticket summaries")
        except json.JSONDecodeError as json_error:
            analysis_logger.warning(f"⚠️ JSON parsing failed: {json_error}")
            analysis_logger.info("🔄 Wrapping raw output in results object")
            # If it's not valid JSON, wrap it in a results object
            results = {
                "raw_output": results_str,
                "parse_error": str(json_error),
                "timestamp": asyncio.get_event_loop().time()
            }
        
        # Update progress with success status
        analysis_progress[analysis_id]["status"] = "completed"
        analysis_progress[analysis_id]["results"] = results
        analysis_logger.info(f"🎉 Analysis {analysis_id} completed successfully")
        
    except Exception as e:
        # Enhanced error logging with full stack trace
        analysis_logger.error(f"❌ Analysis {analysis_id} failed with error: {str(e)}")
        analysis_logger.error(f"Error type: {type(e).__name__}")
        analysis_logger.error("Full stack trace:", exc_info=True)
        
        # Store error information
        analysis_progress[analysis_id]["status"] = "error"
        analysis_progress[analysis_id]["error"] = str(e)
        analysis_progress[analysis_id]["error_type"] = type(e).__name__
        
    finally:
        # Cleanup temporary file with logging
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                analysis_logger.info(f"🧹 Temporary file cleaned up: {file_path}")
            except Exception as cleanup_error:
                analysis_logger.warning(f"⚠️ Failed to cleanup temporary file {file_path}: {cleanup_error}")
        else:
            analysis_logger.warning(f"⚠️ Temporary file not found for cleanup: {file_path}")

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
