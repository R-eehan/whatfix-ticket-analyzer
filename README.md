# Whatfix Ticket Analyzer

A web application to analyze support tickets and identify those that could be resolved using Whatfix's Diagnostics feature.

## Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

## Setup Instructions

### 1. Clone/Create the Project Structure

```bash
mkdir whatfix-ticket-analyzer
cd whatfix-ticket-analyzer
```

### 2. Backend Setup

#### 2.1 Create Backend Directory
```bash
mkdir backend
cd backend
```

#### 2.2 Copy Your Existing Code
- Copy your existing Python code (from paste.txt) into `backend/ticket_analyzer.py`

#### 2.3 Install Dependencies
```bash
pip install -r requirements.txt
```

#### 2.4 Set Environment Variables (Optional)
If you want to use API keys from environment variables:
```bash
export GOOGLE_API_KEY="your-gemini-api-key"
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### 3. Frontend Setup

#### 3.1 Navigate to Frontend Directory
```bash
cd ../frontend
```

#### 3.2 Install Dependencies
```bash
npm install
```

### 4. Running the Application

#### 4.1 Start the Backend (Terminal 1)
```bash
cd backend
uvicorn main:app --reload --port 8000
```
The API will be available at `http://localhost:8000`
API documentation will be at `http://localhost:8000/docs`

#### 4.2 Start the Frontend (Terminal 2)
```bash
cd frontend
npm run dev
```
The frontend will be available at `http://localhost:5173`

## Usage

1. Open your browser and navigate to `http://localhost:5173`
2. Select your preferred LLM provider from the dropdown
3. Enter your API key for the selected provider
4. Upload a CSV file (max 10MB) with support ticket data
5. Click "Analyze Tickets"
6. View the results in two tables:
   - Summary table with overall statistics
   - Outreach table with individual ticket details

## CSV Format Requirements

The CSV must contain the following columns:
- `Zendesk Tickets ID`
- `Zendesk Comments ID`
- `Zendesk Comments Body`
- `Zendesk Tickets Ent ID`
- `Zendesk Tickets Subject`
- `Zendesk Tickets Root Cause` (optional)
- `Support Ticket Output Gpt Subcategory` (optional)

## Troubleshooting

### Backend Issues
- Ensure all Python dependencies are installed
- Check that the API is running on port 8000
- Verify API keys are set correctly

### Frontend Issues
- Clear browser cache if styles don't load
- Check console for any JavaScript errors
- Ensure backend is running before uploading files

### CORS Issues
- The backend is configured to allow CORS from the frontend
- If you change ports, update the CORS settings in `backend/main.py`