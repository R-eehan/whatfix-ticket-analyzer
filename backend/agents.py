"""
Agents for the Whatfix Ticket Analyzer crew.
"""
from crewai import Agent
from .tools import TicketAnalysisTool, DiagnosticsAnalysisTool, ReportingTool

ticket_analysis_tool = TicketAnalysisTool()
diagnostics_analysis_tool = DiagnosticsAnalysisTool()
reporting_tool = ReportingTool()

class TicketAgents:
    def ticket_analysis_agent(self):
        return Agent(
            role='Ticket Analysis Agent',
            goal='Analyze a CSV file of support tickets, process them, and return a list of ticket summaries.',
            backstory='An expert in processing and understanding support ticket data. Your goal is to extract meaningful information from the raw ticket data.',
            tools=[ticket_analysis_tool],
            verbose=True,
            allow_delegation=False
        )

    def diagnostics_agent(self):
        return Agent(
            role='Diagnostics Agent',
            goal='Analyze a list of ticket summaries for diagnostics compatibility and return a detailed analysis.',
            backstory='A specialist in identifying patterns and opportunities for automation in support tickets. Your goal is to determine which tickets could have been resolved with automated diagnostics.',
            tools=[diagnostics_analysis_tool],
            verbose=True,
            allow_delegation=False
        )

    def reporting_agent(self):
        return Agent(
            role='Reporting Agent',
            goal='Compile the final report from ticket summaries and diagnostics analysis, including an outreach list.',
            backstory='A meticulous agent who creates comprehensive and easy-to-understand reports. Your goal is to present the findings of the analysis in a clear and actionable format.',
            tools=[reporting_tool],
            verbose=True,
            allow_delegation=False
        )
