"""
Crew for the Whatfix Ticket Analyzer with enhanced tracing and logging.

This module orchestrates the multi-agent CrewAI workflow for ticket analysis,
with comprehensive observability through Arize tracing.
"""
from crewai import Crew, Process
from .agents import TicketAgents
from .tasks import TicketTasks
import os
import logging

# Setup logger for crew operations
logger = logging.getLogger(__name__)

class TicketAnalysisCrew:
    """
    Multi-agent crew for analyzing support tickets with full observability.
    
    This class orchestrates three specialized agents to process support tickets,
    analyze their compatibility with automated diagnostics, and generate 
    comprehensive reports. All operations are automatically traced via Arize.
    """
    
    def __init__(self, csv_path: str, llm_provider: str = None, api_key: str = None):
        """
        Initialize the ticket analysis crew with configuration.
        
        Args:
            csv_path: Path to the CSV file containing ticket data
            llm_provider: LLM provider to use (gemini, openai, anthropic)
            api_key: API key for the LLM provider
        """
        logger.info(f"🔧 Initializing TicketAnalysisCrew for file: {csv_path}")
        
        self.csv_path = csv_path
        
        # Set environment variables for LLM configuration
        # Use provided values or fall back to environment defaults
        self.llm_provider = llm_provider or os.getenv('LLM_PROVIDER', 'gemini')
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
        
        logger.info(f"📡 LLM Provider: {self.llm_provider}")
        logger.info(f"🔑 API Key: {'configured' if self.api_key else 'using environment default'}")
        
        # Set environment variables for tools to use
        os.environ['LLM_PROVIDER'] = self.llm_provider
        if self.api_key:
            os.environ['GOOGLE_API_KEY'] = self.api_key
            os.environ['GEMINI_API_KEY'] = self.api_key
        
        # Initialize agents and tasks with enhanced logging
        logger.info("👥 Initializing agents...")
        self.agents = TicketAgents(api_key=self.api_key)
        logger.info("📋 Initializing tasks...")
        self.tasks = TicketTasks()
        logger.info("✅ TicketAnalysisCrew initialization complete")

    def run(self):
        """
        Execute the complete ticket analysis workflow with full tracing.
        
        This method orchestrates the three-agent workflow:
        1. TicketAnalysisAgent: Processes CSV and extracts summaries
        2. DiagnosticsAgent: Analyzes compatibility with automation
        3. ReportingAgent: Compiles final report with recommendations
        
        All agent interactions and LLM calls are automatically traced by Arize.
        
        Returns:
            str: JSON string containing the complete analysis results
        """
        logger.info("🚀 Starting CrewAI workflow execution...")
        
        try:
            # Create agents with enhanced logging
            logger.info("👤 Creating TicketAnalysisAgent...")
            ticket_analysis_agent = self.agents.ticket_analysis_agent()
            
            logger.info("🔍 Creating DiagnosticsAgent...")
            diagnostics_agent = self.agents.diagnostics_agent()
            
            logger.info("📊 Creating ReportingAgent...")
            reporting_agent = self.agents.reporting_agent()

            # Create tasks with proper context and logging
            logger.info("📋 Creating analyze_tickets_task...")
            analyze_tickets_task = self.tasks.analyze_tickets_task(
                ticket_analysis_agent,
                self.csv_path,
                self.llm_provider,
                self.api_key
            )
            
            logger.info("🔍 Creating diagnose_tickets_task...")
            diagnose_tickets_task = self.tasks.diagnose_tickets_task(
                diagnostics_agent,
                analyze_tickets_task  # Pass the task directly, not in a list
            )
            
            logger.info("📊 Creating reporting_task...")
            reporting_task = self.tasks.reporting_task(
                reporting_agent,
                [analyze_tickets_task, diagnose_tickets_task],
                self.csv_path,
                self.llm_provider
            )

            # Create crew with proper configuration and tracing
            logger.info("🎭 Creating Crew with sequential process...")
            crew = Crew(
                agents=[ticket_analysis_agent, diagnostics_agent, reporting_agent],
                tasks=[analyze_tickets_task, diagnose_tickets_task, reporting_task],
                process=Process.sequential,
                verbose=True  # Enable verbose logging for detailed tracing
            )

            # Execute crew workflow - this will be fully traced by Arize
            logger.info("⚡ Executing crew.kickoff() - all operations will be traced...")
            result = crew.kickoff()
            logger.info("✅ Crew execution completed successfully")
            
            # Process and return the result
            final_result = result.raw if hasattr(result, 'raw') else str(result)
            logger.info(f"📤 Returning result (length: {len(final_result)} characters)")
            
            return final_result
            
        except Exception as e:
            logger.error(f"❌ Error during crew execution: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error("Full stack trace:", exc_info=True)
            raise  # Re-raise the exception to be handled by the calling function
