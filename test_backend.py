import os
from backend.crew import TicketAnalysisCrew

# Make sure your API key is set
if not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    print("Please set GEMINI_API_KEY or GOOGLE_API_KEY environment variable")
    exit(1)

# Test with a sample CSV file
csv_path = "/Users/reehanahmed/Downloads/zendesk_reselection_tickets_limited.csv"  # Update this path
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

try:
    crew = TicketAnalysisCrew(
        csv_path=csv_path,
        llm_provider="gemini",
        api_key=api_key
    )
    
    print("Starting crew analysis...")
    result = crew.run()
    print("Analysis complete!")
    print(result)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()