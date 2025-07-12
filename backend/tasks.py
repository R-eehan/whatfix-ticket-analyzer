"""
Tasks for the Whatfix Ticket Analyzer crew.
"""
from crewai import Task
from .agents import TicketAgents

agents = TicketAgents()

class TicketTasks:
    def analyze_tickets_task(self, agent, csv_path, llm_provider, api_key):
        return Task(
            description=f'Analyze the support tickets from the CSV file located at {csv_path}. Use the {llm_provider} LLM provider. The key for the {llm_provider} is {api_key}',
            agent=agent,
            expected_output='A list of dictionaries, where each dictionary is a summary of a support ticket.',
            inputs={'csv_path': csv_path, 'llm_provider': llm_provider, 'api_key': api_key}
        )

    def diagnose_tickets_task(self, agent, context):
        return Task(
            description='Analyze the ticket summaries for diagnostics compatibility.',
            agent=agent,
            expected_output='A dictionary containing the diagnostics analysis.',
            context=context
        )

    def reporting_task(self, agent, context, csv_path, llm_provider):
        return Task(
            description='Create a final report based on the ticket summaries and diagnostics analysis.',
            agent=agent,
            expected_output='A dictionary containing the final report.',
            context=context,
            inputs={'csv_path': csv_path, 'llm_provider': llm_provider}
        )
