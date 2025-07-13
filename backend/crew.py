"""
Crew for the Whatfix Ticket Analyzer.
"""
from crewai import Crew, Process
from .agents import TicketAgents
from .tasks import TicketTasks
import os

class TicketAnalysisCrew:
    def __init__(self, csv_path: str, llm_provider: str, api_key: str):
        self.csv_path = csv_path
        self.llm_provider = llm_provider
        self.api_key = api_key
        
        # Set environment variable for Gemini
        if llm_provider.lower() == 'gemini' and api_key:
            os.environ["GEMINI_API_KEY"] = api_key
        
        # Initialize agents with API key
        self.agents = TicketAgents(api_key=api_key)
        self.tasks = TicketTasks()

    def run(self):
        # Create agents
        ticket_analysis_agent = self.agents.ticket_analysis_agent()
        diagnostics_agent = self.agents.diagnostics_agent()
        reporting_agent = self.agents.reporting_agent()

        # Create tasks with proper context
        analyze_tickets_task = self.tasks.analyze_tickets_task(
            ticket_analysis_agent,
            self.csv_path,
            self.llm_provider,
            self.api_key
        )
        
        diagnose_tickets_task = self.tasks.diagnose_tickets_task(
            diagnostics_agent,
            analyze_tickets_task  # Pass the task directly, not in a list
        )
        
        reporting_task = self.tasks.reporting_task(
            reporting_agent,
            [analyze_tickets_task, diagnose_tickets_task],
            self.csv_path,
            self.llm_provider
        )

        # Create crew with proper configuration
        crew = Crew(
            agents=[ticket_analysis_agent, diagnostics_agent, reporting_agent],
            tasks=[analyze_tickets_task, diagnose_tickets_task, reporting_task],
            process=Process.sequential,
            verbose=True
        )

        # Run crew
        result = crew.kickoff()
        
        # Return the final output from the reporting task
        return result.raw if hasattr(result, 'raw') else str(result)