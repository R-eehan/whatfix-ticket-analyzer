import React from 'react';
import { AnalysisResults } from '../types';
import { CheckCircle, XCircle, AlertCircle, TrendingUp } from 'lucide-react';

interface SummaryTableProps {
  results: AnalysisResults;
}

const SummaryTable: React.FC<SummaryTableProps> = ({ results }) => {
  //Debug log
  console.log('Results receiveed:', results);
  console.log('Diagnostics analysis:', results?.diagnostics_analysis);
  const { metadata = {}, diagnostics_analysis = {}, ticket_summaries = [] } = results || {};
  
  // Ensure nested properties exist
  const summary = diagnostics_analysis.summary || {};
  const categoryDistribution = diagnostics_analysis.category_distribution || {};
  const recommendations = diagnostics_analysis.recommendations || [];
  const complexIssues = diagnostics_analysis.complex_issues || [];

  // Calculate average comments safely
  const avgComments = ticket_summaries.length > 0 
    ? (ticket_summaries.reduce((acc, t) => acc + (t.comment_count || 0), 0) / ticket_summaries.length).toFixed(1)
    : '0.0';

  return (
    <div className="space-y-6">
      {/* Overall Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-blue-600">Total Tickets</p>
              <p className="text-2xl font-bold text-blue-900">
                {summary.total_tickets || 0}
              </p>
            </div>
            <AlertCircle className="h-8 w-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-green-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-green-600">Diagnostics Compatible</p>
              <p className="text-2xl font-bold text-green-900">
                {summary.diagnostics_compatible_count || 0}
              </p>
              <p className="text-xs text-green-600 mt-1">
                {summary.diagnostics_compatible_percentage || '0%'}
              </p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-500" />
          </div>
        </div>

        <div className="bg-red-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-red-600">Complex Issues</p>
              <p className="text-2xl font-bold text-red-900">
                {summary.complex_issues_count || 0}
              </p>
            </div>
            <XCircle className="h-8 w-8 text-red-500" />
          </div>
        </div>

        <div className="bg-purple-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-purple-600">Avg Comments</p>
              <p className="text-2xl font-bold text-purple-900">
                {avgComments}
              </p>
            </div>
            <TrendingUp className="h-8 w-8 text-purple-500" />
          </div>
        </div>
      </div>

      {/* Category Distribution */}
      {Object.keys(categoryDistribution).length > 0 && (
        <div>
          <h3 className="text-md font-semibold mb-3">Issue Categories</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Category
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Count
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Percentage
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {Object.entries(categoryDistribution)
                  .sort(([, a], [, b]) => b - a)
                  .map(([category, count]) => (
                    <tr key={category}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {category}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {count}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {summary.total_tickets > 0 
                          ? ((count / summary.total_tickets) * 100).toFixed(1) 
                          : '0.0'}%
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div>
          <h3 className="text-md font-semibold mb-3">Recommendations</h3>
          <div className="space-y-3">
            {recommendations.map((rec, index) => (
              <div key={index} className="border-l-4 border-blue-500 bg-blue-50 p-4">
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <span className="inline-flex items-center justify-center h-8 w-8 rounded-full bg-blue-600 text-white text-sm font-medium">
                      {index + 1}
                    </span>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-blue-900">{rec.type}</p>
                    <p className="text-sm text-blue-800 mt-1">{rec.recommendation}</p>
                    <p className="text-xs text-blue-600 mt-1">Reason: {rec.reason}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Complex Issues */}
      {complexIssues.length > 0 && (
        <div>
          <h3 className="text-md font-semibold mb-3">Complex Issues Requiring Attention</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Ticket ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Issue
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Comments
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {complexIssues.slice(0, 5).map((issue) => (
                  <tr key={issue.ticket_id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {issue.ticket_id}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500 whitespace-normal">
                      {issue.issue}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {issue.comment_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default SummaryTable;
