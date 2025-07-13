"""
Tasks for the Whatfix Ticket Analyzer crew.
"""
from crewai import Task
from typing import List, Dict

class TicketTasks:
    def analyze_tickets_task(self, agent, csv_path: str, llm_provider: str, api_key: str):
        return Task(
            description=f"""
            Analyze the support tickets from the CSV file located at {csv_path}.
            
            Process each ticket and extract:
            1. Ticket ID and metadata
            2. Customer issue summary
            3. Resolution steps taken
            4. Category of the issue
            5. Type of resolution
            
            Return a comprehensive list of ticket summaries with all extracted information.
            """,
            agent=agent,
            expected_output='A list of dictionaries, where each dictionary contains a detailed summary of a support ticket including ticket_id, issue_summary, resolution_summary, category, and other metadata.'
        )

    def diagnose_tickets_task(self, agent, context_task: Task):
        return Task(
            description="""
            Analyze the ticket summaries from the previous task for diagnostics compatibility.
            
            For each ticket, determine:
            1. Whether it could be resolved with automated diagnostics
            2. What type of diagnostics would be needed
            3. Compatibility score
            4. Specific recommendations
            
            Provide statistics on:
            - Total tickets that could use diagnostics
            - Category distribution
            - Resolution type patterns
            - High-impact opportunities
            """,
            agent=agent,
            expected_output='A comprehensive dictionary containing diagnostics analysis including compatible tickets, statistics, category distribution, and actionable recommendations.',
            context=[context_task]  # Properly set context as a list
        )

    def reporting_task(self, agent, context_tasks: List[Task], csv_path: str, llm_provider: str):
        return Task(
            description=f"""
            Create a final comprehensive report based on:
            1. Ticket summaries from the analysis task
            2. Diagnostics compatibility analysis
            
            The report should include:
            - Executive summary with key findings
            - Detailed ticket analysis results
            - Diagnostics opportunities and recommendations
            - Outreach list of customers who could benefit from diagnostics
            - Actionable next steps
            
            Format the report in a clear, professional manner suitable for stakeholders.
            """,
            agent=agent,
            expected_output='A complete dictionary containing the final report with all analysis results, recommendations, and outreach lists formatted for easy consumption.',
            context=context_tasks  # Pass the list of context tasks
        )