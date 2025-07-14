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
            
            The LLM provider and API key have been configured in the environment.
            Current configuration:
            - LLM Provider: {llm_provider}
            - API Key: {'Configured' if api_key else 'Using environment default'}
            
            Process each ticket and extract:
            1. Ticket ID and metadata
            2. Customer issue summary
            3. Resolution steps taken
            4. Category of the issue
            5. Type of resolution
            
            Return a comprehensive list of ticket summaries with all extracted information as a JSON string.
            """,
            agent=agent,
            expected_output='A JSON string containing metadata and a list of dictionaries, where each dictionary contains a detailed summary of a support ticket including ticket_id, issue_summary, resolution_summary, category, and other metadata.'
        )

    def diagnose_tickets_task(self, agent, context_task: Task):
        return Task(
            description="""
            Analyze the ticket summaries from the previous task for diagnostics compatibility.
            
            The previous task returns a JSON string. Parse it to extract the ticket_summaries array.
            
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
            
            Return the analysis as a JSON string.
            """,
            agent=agent,
            expected_output='A JSON string containing diagnostics analysis including compatible tickets, statistics, category distribution, and actionable recommendations.',
            context=[context_task]  # Properly set context as a list
        )

    def reporting_task(self, agent, context_tasks: List[Task], csv_path: str, llm_provider: str):
        return Task(
            description=f"""
            Create a final comprehensive report based on:
            1. Ticket summaries from the analysis task
            2. Diagnostics compatibility analysis
            
            The previous tasks return JSON strings. Parse them and combine the data.
            
            The report should include:
            - Executive summary with key findings
            - Detailed ticket analysis results  
            - Diagnostics opportunities and recommendations
            - Outreach list of customers who could benefit from diagnostics
            - Actionable next steps
            
            Combine the data from both previous tasks into a single analysis_data object with structure:
            {{
                "ticket_data": <output from task 1>,
                "diagnostics_data": <output from task 2>
            }}
            
            Return the final report as a JSON string.
            """,
            agent=agent,
            expected_output='A JSON string containing the final report with all analysis results, recommendations, and outreach lists formatted for easy consumption.',
            context=context_tasks  # Pass the list of context tasks
        )
