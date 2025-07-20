"""
Arize tracing configuration for CrewAI LLM observability.

This module sets up comprehensive tracing for the ticket analyzer's CrewAI workflow,
allowing us to monitor agent interactions, LLM calls, and performance metrics
through the Arize platform.
"""

import os
import logging
from typing import Optional
from opentelemetry.sdk.trace import TracerProvider

# Configure logging for tracing operations
logger = logging.getLogger(__name__)

class ArizeTracingSetup:
    """
    Handles initialization and configuration of Arize tracing for CrewAI workflows.
    
    This class manages the setup of OpenTelemetry tracing with Arize backend,
    instrumenting CrewAI agents, LangChain operations, and LLM calls.
    """
    
    def __init__(self):
        self.tracer_provider: Optional[TracerProvider] = None
        self.is_initialized = False
        
    def initialize_tracing(
        self, 
        space_id: Optional[str] = None,
        api_key: Optional[str] = None,
        project_name: Optional[str] = None
    ) -> bool:
        """
        Initialize Arize tracing with environment-based configuration.
        
        Args:
            space_id: Arize space ID (falls back to ARIZE_SPACE_ID env var)
            api_key: Arize API key (falls back to ARIZE_API_KEY env var) 
            project_name: Project name for tracing (falls back to ARIZE_PROJECT_NAME env var)
            
        Returns:
            bool: True if tracing was successfully initialized, False otherwise
        """
        try:
            # Get configuration from parameters or environment variables
            space_id = space_id or os.getenv('ARIZE_SPACE_ID')
            api_key = api_key or os.getenv('ARIZE_API_KEY') 
            project_name = project_name or os.getenv('ARIZE_PROJECT_NAME', 'whatfix-ticket-analyzer')
            
            # Check if Arize credentials are available
            if not space_id or not api_key:
                logger.warning(
                    "Arize tracing disabled: Missing ARIZE_SPACE_ID or ARIZE_API_KEY environment variables. "
                    "Set these to enable LLM observability tracking."
                )
                return False
                
            logger.info(f"Initializing Arize tracing for project: {project_name}")
            
            # Import Arize OTEL registration (only when credentials are available)
            from arize.otel import register
            
            # Register Arize tracer provider with configuration
            self.tracer_provider = register(
                space_id=space_id,
                api_key=api_key,
                project_name=project_name
            )
            
            logger.info("Arize tracer provider registered successfully")
            
            # Initialize instrumentation for all relevant libraries
            self._setup_instrumentation()
            
            self.is_initialized = True
            logger.info("Arize tracing initialization completed successfully")
            return True
            
        except ImportError as e:
            logger.error(f"Failed to import Arize dependencies: {e}")
            logger.error("Install required packages: pip install arize-otel openinference-instrumentation-crewai")
            return False
        except Exception as e:
            logger.error(f"Unexpected error initializing Arize tracing: {e}")
            return False
    
    def _setup_instrumentation(self):
        """
        Set up instrumentation for CrewAI, LangChain, and LiteLLM.
        
        This method instruments all the key libraries used in our ticket analysis workflow
        to capture comprehensive tracing data for LLM interactions.
        """
        try:
            # Import instrumentors for different libraries
            from openinference.instrumentation.crewai import CrewAIInstrumentor
            from openinference.instrumentation.langchain import LangChainInstrumentor
            
            logger.info("Setting up CrewAI instrumentation...")
            # Instrument CrewAI operations (agents, tasks, crew execution)
            CrewAIInstrumentor().instrument(tracer_provider=self.tracer_provider)
            logger.info("CrewAI instrumentation configured")
            
            logger.info("Setting up LangChain instrumentation...")
            # Instrument LangChain operations (LLM calls, chains, tools)
            LangChainInstrumentor().instrument(tracer_provider=self.tracer_provider)
            logger.info("LangChain instrumentation configured")
            
            # Try to set up LiteLLM instrumentation if available
            try:
                from openinference.instrumentation.litellm import LiteLLMInstrumentor
                logger.info("Setting up LiteLLM instrumentation...")
                LiteLLMInstrumentor().instrument(tracer_provider=self.tracer_provider)
                logger.info("LiteLLM instrumentation configured")
            except ImportError:
                logger.info("LiteLLM instrumentation not available - skipping")
            
        except ImportError as e:
            logger.error(f"Failed to import instrumentation libraries: {e}")
            raise
        except Exception as e:
            logger.error(f"Error setting up instrumentation: {e}")
            raise
    
    def get_tracer_provider(self) -> Optional[TracerProvider]:
        """
        Get the configured tracer provider.
        
        Returns:
            TracerProvider or None if tracing is not initialized
        """
        return self.tracer_provider
    
    def is_tracing_enabled(self) -> bool:
        """
        Check if tracing is properly initialized and enabled.
        
        Returns:
            bool: True if tracing is active, False otherwise
        """
        return self.is_initialized and self.tracer_provider is not None


# Global tracing setup instance
_tracing_setup = ArizeTracingSetup()

def setup_arize_tracing(
    space_id: Optional[str] = None,
    api_key: Optional[str] = None, 
    project_name: Optional[str] = None
) -> bool:
    """
    Convenience function to initialize Arize tracing.
    
    This is the main entry point for setting up LLM observability in the application.
    
    Args:
        space_id: Arize space ID (optional, uses env var if not provided)
        api_key: Arize API key (optional, uses env var if not provided)
        project_name: Project name for grouping traces (optional, uses env var or default)
        
    Returns:
        bool: True if tracing setup succeeded, False otherwise
    """
    return _tracing_setup.initialize_tracing(space_id, api_key, project_name)

def get_tracing_status() -> dict:
    """
    Get current tracing status and configuration information.
    
    Returns:
        dict: Status information including whether tracing is enabled and configuration details
    """
    return {
        'enabled': _tracing_setup.is_tracing_enabled(),
        'initialized': _tracing_setup.is_initialized,
        'project_name': os.getenv('ARIZE_PROJECT_NAME', 'whatfix-ticket-analyzer'),
        'has_space_id': bool(os.getenv('ARIZE_SPACE_ID')),
        'has_api_key': bool(os.getenv('ARIZE_API_KEY'))
    }