# Arize LLM Observability Setup Guide

This guide explains how to set up Arize tracing for comprehensive LLM observability in the Whatfix Ticket Analyzer.

## 🎯 What Gets Traced

The Arize integration automatically captures:

- **CrewAI Agent Interactions**: All agent communications and task executions
- **LLM API Calls**: Token usage, latency, and response quality for Gemini/OpenAI/Anthropic
- **Tool Executions**: Ticket analysis, diagnostics analysis, and reporting tool operations
- **Error Tracking**: Failed LLM calls, timeouts, and processing errors
- **Performance Metrics**: End-to-end workflow timing and resource usage

## 🔧 Required Environment Variables

### Arize Configuration (Required for Tracing)

```bash
# Get these from your Arize account
export ARIZE_SPACE_ID="your-space-id-here"
export ARIZE_API_KEY="your-arize-api-key-here"
export ARIZE_PROJECT_NAME="whatfix-ticket-analyzer"  # Optional, defaults to this value
```

### LLM Provider Configuration (Existing)

```bash
# Default LLM provider (already configured)
export LLM_PROVIDER="gemini"  # Options: gemini, openai, anthropic

# API Keys for LLM providers
export GOOGLE_API_KEY="your-gemini-api-key"     # For Gemini
export GEMINI_API_KEY="your-gemini-api-key"     # Alternative name for Gemini
export OPENAI_API_KEY="your-openai-api-key"     # For OpenAI
export ANTHROPIC_API_KEY="your-anthropic-key"   # For Anthropic
```

## 📦 Installation

1. **Install new dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

   The following packages were added for Arize tracing:
   - `openinference-instrumentation-crewai`
   - `openinference-instrumentation-langchain` 
   - `openinference-instrumentation-litellm`
   - `arize-otel`

## 🚀 Getting Started

### Step 1: Get Arize Credentials

1. Sign up for an Arize account at https://arize.com/
2. Create a new project or use an existing one
3. Navigate to Settings → API Keys
4. Copy your Space ID and API Key

### Step 2: Set Environment Variables

Create a `.env` file or set environment variables:

```bash
# Required for tracing
export ARIZE_SPACE_ID="12345"
export ARIZE_API_KEY="your-arize-api-key"

# Existing LLM configuration
export GOOGLE_API_KEY="your-gemini-key"
```

### Step 3: Start the Application

```bash
# From the project root
./start_servers.sh
```

Or manually:

```bash
# Terminal 1 - Backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2 - Frontend  
cd frontend
npm run dev
```

## 📊 Verifying Tracing Setup

### Check API Status

Visit `http://localhost:8000/` to see tracing status:

```json
{
  "message": "Whatfix Ticket Analyzer API",
  "version": "1.0.0", 
  "tracing": {
    "enabled": true,
    "initialized": true,
    "project_name": "whatfix-ticket-analyzer",
    "has_space_id": true,
    "has_api_key": true
  }
}
```

### Check Health Endpoint

Visit `http://localhost:8000/health`:

```json
{
  "status": "healthy",
  "services": {
    "api": "running",
    "llm_tracing": "enabled"
  },
  "tracing": {
    "enabled": true,
    "initialized": true,
    "project_name": "whatfix-ticket-analyzer",
    "has_space_id": true,
    "has_api_key": true
  }
}
```

### Log Output

Look for these log messages during startup:

```
✅ Arize tracing initialized successfully - LLM calls will be monitored
```

If tracing fails, you'll see:

```
⚠️ Arize tracing not initialized - running without LLM observability
To enable tracing, set ARIZE_SPACE_ID and ARIZE_API_KEY environment variables
```

## 🔍 What You'll See in Arize

Once tracing is active and you run ticket analysis, you'll see:

### Agent Traces
- **TicketAnalysisAgent**: CSV processing and ticket summarization
- **DiagnosticsAgent**: Compatibility analysis with automation patterns
- **ReportingAgent**: Final report compilation and outreach list generation

### LLM Call Details
- **Prompts**: Full system prompts and user inputs sent to LLMs
- **Responses**: Complete LLM responses and extracted JSON
- **Metrics**: Token counts, latency, cost estimation
- **Errors**: Failed calls, timeouts, and rate limits

### Tool Executions
- **TicketAnalysisTool**: File processing and LLM orchestration
- **DiagnosticsAnalysisTool**: Pattern matching and scoring
- **ReportingTool**: Data compilation and export generation

## 🛠 Troubleshooting

### Issue: "Arize tracing not initialized"

**Cause**: Missing environment variables

**Solution**: 
```bash
echo $ARIZE_SPACE_ID  # Should show your space ID
echo $ARIZE_API_KEY   # Should show your API key
```

### Issue: "Failed to import Arize dependencies"

**Cause**: Missing packages

**Solution**:
```bash
cd backend
pip install arize-otel openinference-instrumentation-crewai
```

### Issue: No traces visible in Arize

**Cause**: Multiple possibilities

**Check**:
1. Environment variables are set correctly
2. Backend logs show "Arize tracing initialized successfully"
3. Run a ticket analysis to generate traces
4. Wait 1-2 minutes for traces to appear in Arize UI

### Enhanced Logging

The application now includes comprehensive logging with emojis for easy identification:

- 🚀 Process start
- ✅ Success operations  
- ❌ Errors and failures
- ⚠️ Warnings
- 🔧 Configuration
- 📊 Data processing
- 🎯 Key operations

Set log level to DEBUG for maximum detail:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

## 🎛 Advanced Configuration

### Custom Project Names

Set different project names for different environments:

```bash
export ARIZE_PROJECT_NAME="whatfix-ticket-analyzer-dev"    # Development
export ARIZE_PROJECT_NAME="whatfix-ticket-analyzer-prod"   # Production
```

### Disabling Tracing

To run without tracing (useful for development):

```bash
unset ARIZE_SPACE_ID
unset ARIZE_API_KEY
```

The application will continue to work normally but without LLM observability.

## 📈 Monitoring Best Practices

1. **Monitor Token Usage**: Track LLM costs across different ticket volumes
2. **Track Performance**: Monitor agent execution times and identify bottlenecks  
3. **Error Monitoring**: Set up alerts for failed LLM calls or processing errors
4. **Quality Monitoring**: Review LLM outputs for accuracy and consistency

## 🔗 Useful Links

- [Arize Documentation](https://arize.com/docs/)
- [CrewAI Tracing Guide](https://arize.com/docs/ax/integrations/frameworks-and-platforms/crewai/crewai-tracing)
- [OpenInference Documentation](https://github.com/Arize-ai/openinference)