"""
FastAPI backend for Whatfix Ticket Analyzer
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
import tempfile
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import numpy as np

# Import the existing ticket analyzer
from ticket_analyzer import WhatfixTicketAnalyzer

app = FastAPI(title="Whatfix Ticket Analyzer API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thread pool for CPU-bound operations
executor = ThreadPoolExecutor(max_workers=2)

# Store for tracking analysis progress
analysis_progress = {}


class AnalysisRequest(BaseModel):
    llm_provider: str = "gemini"
    api_key: str


class AnalysisProgress(BaseModel):
    status: str  # "processing", "completed", "error"
    current_ticket: Optional[int] = None
    total_tickets: Optional[int] = None
    progress_percentage: Optional[float] = None
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
    """
    Analyze support tickets from CSV file
    """
    # Validate file size (10MB limit)
    contents = await file.read()
    file_size = len(contents) / (1024 * 1024)  # Convert to MB
    
    if file_size > 10:
        raise HTTPException(status_code=413, detail="File size exceeds 10MB limit")
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    # Create a unique analysis ID
    import uuid
    analysis_id = str(uuid.uuid4())
    
    # Initialize progress tracking
    analysis_progress[analysis_id] = {
        "status": "processing",
        "current_ticket": 0,
        "total_tickets": 0,
        "progress_percentage": 0,
        "error": None,
        "results": None
    }
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv') as tmp_file:
        tmp_file.write(contents)
        tmp_file_path = tmp_file.name
    
    # Start analysis in background
    background_tasks.add_task(
        run_analysis,
        analysis_id,
        tmp_file_path,
        llm_provider,
        api_key
    )
    
    return {"analysis_id": analysis_id, "message": "Analysis started"}


async def run_analysis(analysis_id: str, file_path: str, llm_provider: str, api_key: str):
    """
    Run the ticket analysis in background
    """
    try:
        # Create custom analyzer that reports progress
        class ProgressAnalyzer(WhatfixTicketAnalyzer):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.analysis_id = analysis_id
            
            def _process_all_tickets(self, df):
                """Override to add progress tracking"""
                grouped = df.groupby('Zendesk Tickets ID')
                summaries = []
                total_tickets = len(grouped)
                
                # Update total tickets
                analysis_progress[self.analysis_id]["total_tickets"] = total_tickets
                
                for i, (ticket_id, ticket_comments) in enumerate(grouped):
                    # Update progress
                    analysis_progress[self.analysis_id]["current_ticket"] = i + 1
                    analysis_progress[self.analysis_id]["progress_percentage"] = ((i + 1) / total_tickets) * 100
                    
                    # Process ticket
                    ticket_data = self.processor.process_ticket_comments(ticket_comments)
                    summary = self.processor.summarize_ticket(ticket_data)
                    summary['author_email'] = self._extract_author_email(ticket_comments)
                    summaries.append(summary)
                
                return summaries
        
        # Initialize analyzer
        analyzer = ProgressAnalyzer(llm_provider=llm_provider, api_key=api_key)
        analyzer.analysis_id = analysis_id
        
        # Run analysis
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(
            executor,
            analyzer.analyze_csv,
            file_path,
            None  # No output directory needed
        )
        
        # Update progress with results
        analysis_progress[analysis_id]["status"] = "completed"
        analysis_progress[analysis_id]["results"] = results
        
    except Exception as e:
        analysis_progress[analysis_id]["status"] = "error"
        analysis_progress[analysis_id]["error"] = str(e)
    finally:
        # Clean up temporary file
        if os.path.exists(file_path):
            os.remove(file_path)


def convert_numpy(obj):
    if isinstance(obj, dict):
        return {k: convert_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy(i) for i in obj]
    elif isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj


@app.get("/progress/{analysis_id}")
async def get_progress(analysis_id: str):
    """
    Get analysis progress
    """
    if analysis_id not in analysis_progress:
        raise HTTPException(status_code=404, detail="Analysis ID not found")
    progress = analysis_progress[analysis_id]
    return convert_numpy(progress)


@app.delete("/analysis/{analysis_id}")
async def cleanup_analysis(analysis_id: str):
    """
    Clean up analysis data
    """
    if analysis_id in analysis_progress:
        del analysis_progress[analysis_id]
        return {"message": "Analysis data cleaned up"}
    
    raise HTTPException(status_code=404, detail="Analysis ID not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)