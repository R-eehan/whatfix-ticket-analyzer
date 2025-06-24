import React, { useState } from 'react';
import FileUpload from './components/FileUpload';
import ProviderSelector from './components/ProviderSelector';
import ProgressIndicator from './components/ProgressIndicator';
import SummaryTable from './components/SummaryTable';
import OutreachTable from './components/OutreachTable';
import { AnalysisProgress, AnalysisResults } from './types';
import axios from 'axios';
import { FileText, AlertCircle } from 'lucide-react';

function App() {
  const [selectedProvider, setSelectedProvider] = useState('gemini');
  const [apiKey, setApiKey] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [progress, setProgress] = useState<AnalysisProgress | null>(null);
  const [results, setResults] = useState<AnalysisResults | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileUpload = async (file: File) => {
    if (!apiKey) {
      setError('Please enter an API key for the selected provider');
      return;
    }

    setError(null);
    setIsAnalyzing(true);
    setResults(null);
    setProgress(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('llm_provider', selectedProvider);
    formData.append('api_key', apiKey);

    try {
      const response = await axios.post('/api/analyze', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const { analysis_id } = response.data;
      setAnalysisId(analysis_id);

      // Start polling for progress
      pollProgress(analysis_id);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start analysis');
      setIsAnalyzing(false);
    }
  };

  const pollProgress = async (id: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`/api/progress/${id}`);
        const progressData: AnalysisProgress = response.data;
        
        setProgress(progressData);

        if (progressData.status === 'completed') {
          clearInterval(interval);
          setIsAnalyzing(false);
          if (progressData.results) {
            setResults(progressData.results);
          }
          // Clean up analysis data
          await axios.delete(`/api/analysis/${id}`);
        } else if (progressData.status === 'error') {
          clearInterval(interval);
          setIsAnalyzing(false);
          setError(progressData.error || 'Analysis failed');
        }
      } catch (err) {
        clearInterval(interval);
        setIsAnalyzing(false);
        setError('Failed to fetch progress');
      }
    }, 1000); // Poll every second
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <FileText className="h-8 w-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900">
              Whatfix Ticket Analyzer
            </h1>
          </div>
          <p className="text-gray-600">
            Analyze support tickets to identify opportunities for diagnostics automation
          </p>
        </div>

        {/* Configuration Section */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Configuration</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <ProviderSelector
              selectedProvider={selectedProvider}
              onProviderChange={setSelectedProvider}
            />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                API Key
              </label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={`Enter your ${selectedProvider.toUpperCase()} API key`}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        {/* File Upload Section */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Upload CSV File</h2>
          <FileUpload onFileUpload={handleFileUpload} disabled={isAnalyzing} />
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Progress Indicator */}
        {isAnalyzing && progress && (
          <div className="mb-6">
            <ProgressIndicator progress={progress} />
          </div>
        )}

        {/* Results Section */}
        {results && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-lg font-semibold mb-4">Analysis Summary</h2>
              <SummaryTable results={results} />
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-lg font-semibold mb-4">Diagnostics Outreach List</h2>
              <OutreachTable outreachList={results.author_outreach_list} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;