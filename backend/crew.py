"""
Crew for the Whatfix Ticket Analyzer.
"""
from crewai import Crew
from .agents import TicketAgents
from .tasks import TicketTasks

class TicketAnalysisCrew:
    def __init__(self, csv_path: str, llm_provider: str, api_key: str):
        self.csv_path = csv_path
        self.llm_provider = llm_provider
        self.api_key = api_key
        self.agents = TicketAgents()
        self.tasks = TicketTasks()

    def run(self):
        # Create agents
        ticket_analysis_agent = self.agents.ticket_analysis_agent()
        diagnostics_agent = self.agents.diagnostics_agent()
        reporting_agent = self.agents.reporting_agent()

        # Create tasks
        analyze_tickets_task = self.tasks.analyze_tickets_task(
            ticket_analysis_agent,
            self.csv_path,
            self.llm_provider,
            self.api_key
        )
        diagnose_tickets_task = self.tasks.diagnose_tickets_task(
            diagnostics_agent,
            [analyze_tickets_task]
        )
        reporting_task = self.tasks.reporting_task(
            reporting_agent,
            [analyze_tickets_task, diagnose_tickets_task],
            self.csv_path,
            self.llm_provider
        )

        # Create crew
        crew = Crew(
            agents=[ticket_analysis_agent, diagnostics_agent, reporting_agent],
            tasks=[analyze_tickets_task, diagnose_tickets_task, reporting_task],
            verbose=True
        )

        # Run crew
        result = crew.kickoff()
        return result
