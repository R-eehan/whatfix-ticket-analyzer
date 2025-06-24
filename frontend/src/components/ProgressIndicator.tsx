import React from 'react';
import { AnalysisProgress } from '../types';
import { Loader2 } from 'lucide-react';

interface ProgressIndicatorProps {
  progress: AnalysisProgress;
}

const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({ progress }) => {
  const percentage = progress.progress_percentage || 0;

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center gap-3 mb-4">
        <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
        <h3 className="text-lg font-semibold">Analyzing Tickets...</h3>
      </div>
      
      <div className="space-y-3">
        {/* Progress Bar */}
        <div>
          <div className="flex justify-between items-center mb-1">
            <span className="text-sm font-medium text-gray-700">Progress</span>
            <span className="text-sm text-gray-600">{percentage.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className="bg-blue-600 h-2.5 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${percentage}%` }}
            />
          </div>
        </div>

        {/* Ticket Counter */}
        {progress.current_ticket && progress.total_tickets && (
          <div className="text-sm text-gray-600">
            Processing ticket {progress.current_ticket} of {progress.total_tickets}
          </div>
        )}

        {/* Status Message */}
        <div className="text-sm text-gray-500 italic">
          {progress.status === 'processing' && progress.current_ticket === 0
            ? 'Initializing analysis...'
            : progress.status === 'processing'
            ? 'Analyzing ticket content and generating summaries...'
            : 'Finalizing results...'}
        </div>
      </div>
    </div>
  );
};

export default ProgressIndicator;