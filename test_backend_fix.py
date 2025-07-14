#!/usr/bin/env python3
"""
Test script for the Whatfix Ticket Analyzer backend
"""
import os
import sys
import json
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment variables if not already set
if "GOOGLE_API_KEY" not in os.environ:
    print("Warning: GOOGLE_API_KEY not set in environment")
    print("The system will attempt to use the default configuration")

from backend.crew import TicketAnalysisCrew

def test_backend():
    """Test the backend with a sample CSV file"""
    # You'll need to provide the path to your test CSV file
    csv_path = input("Enter the path to your test CSV file: ").strip()
    
    if not Path(csv_path).exists():
        print(f"Error: File not found: {csv_path}")
        return
    
    print("\nTesting backend with default configuration...")
    print("-" * 50)
    
    try:
        # Create crew with default configuration
        crew = TicketAnalysisCrew(csv_path)
        
        print("Running analysis...")
        result = crew.run()
        
        # Try to parse as JSON
        try:
            result_json = json.loads(result)
            print("\nAnalysis completed successfully!")
            print(f"\nMetadata: {json.dumps(result_json.get('metadata', {}), indent=2)}")
            print(f"\nTotal tickets analyzed: {len(result_json.get('ticket_summaries', []))}")
            
            if 'diagnostics_analysis' in result_json:
                diag = result_json['diagnostics_analysis']
                print(f"\nDiagnostics Summary:")
                print(f"  - Total tickets: {diag.get('summary', {}).get('total_tickets', 0)}")
                print(f"  - Diagnostics compatible: {diag.get('summary', {}).get('diagnostics_compatible_count', 0)}")
                print(f"  - Compatibility percentage: {diag.get('summary', {}).get('diagnostics_compatible_percentage', '0%')}")
            
        except json.JSONDecodeError:
            print("\nResult is not valid JSON. Raw output:")
            print(result[:500] + "..." if len(result) > 500 else result)
            
    except Exception as e:
        print(f"\nError occurred: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_backend()
