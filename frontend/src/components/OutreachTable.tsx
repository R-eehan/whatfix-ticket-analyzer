import React, { useState } from 'react';
import { AuthorOutreach } from '../types';
import { Mail, Search, Download } from 'lucide-react';

interface OutreachTableProps {
  outreachList: AuthorOutreach[];
}

const OutreachTable: React.FC<OutreachTableProps> = ({ outreachList = [] }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');

  // Get unique categories
  const categories = Array.from(
    new Set(outreachList.map((item) => item.derived_category))
  );

  // Filter data
  const filteredData = outreachList.filter((item) => {
    const matchesSearch =
      item.author_email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.issue_summary.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.ticket_id.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesCategory =
      selectedCategory === 'all' || item.derived_category === selectedCategory;

    return matchesSearch && matchesCategory;
  });

  // Export to CSV
  const exportToCSV = () => {
    const headers = [
      'Ticket ID',
      'Author Email',
      'Issue Summary',
      'Resolution Summary',
      'Category',
      'Resolution Type',
    ];

    const csvContent = [
      headers.join(','),
      ...filteredData.map((item) =>
        [
          item.ticket_id,
          item.author_email,
          `"${item.issue_summary.replace(/"/g, '""')}"`,
          `"${item.resolution_summary.replace(/"/g, '""')}"`,
          item.derived_category,
          item.resolution_type,
        ].join(',')
      ),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'diagnostics_outreach_list.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div>
      {/* Controls */}
      <div className="mb-4 flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search by email, ticket ID, or issue..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
        <div className="sm:w-48">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Categories</option>
            {categories.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
        </div>
        <button
          onClick={exportToCSV}
          className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 transition-colors flex items-center gap-2"
        >
          <Download className="h-4 w-4" />
          Export CSV
        </button>
      </div>

      {/* Summary */}
      <div className="mb-4 text-sm text-gray-600">
        Showing {filteredData.length} of {outreachList.length} tickets eligible for diagnostics
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Ticket ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Author Email
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Issue Summary
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Resolution Summary
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Category
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Resolution Type
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredData.map((item) => (
              <tr key={item.ticket_id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {item.ticket_id}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  <a
                    href={`mailto:${item.author_email}`}
                    className="text-blue-600 hover:text-blue-800 flex items-center gap-1"
                  >
                    <Mail className="h-3 w-3" />
                    {item.author_email}
                  </a>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500 whitespace-normal">
                  {item.issue_summary}
                </td>
                <td className="px-6 py-4 text-sm text-gray-500 whitespace-normal">
                  {item.resolution_summary}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {item.derived_category}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {item.resolution_type}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filteredData.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No tickets found matching your criteria
        </div>
      )}
    </div>
  );
};

export default OutreachTable;