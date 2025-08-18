import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { format, addDays, startOfDay } from 'date-fns';
import { Calendar, ChevronLeft, ChevronRight } from 'lucide-react';
import { api, type PaginatedResponse, type Match } from '../lib/api';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';
import { Link } from 'react-router-dom';

export function Fixtures() {
  const today = startOfDay(new Date());
  const [dateFrom, setDateFrom] = useState(format(today, 'yyyy-MM-dd'));
  const [dateTo, setDateTo] = useState(format(addDays(today, 7), 'yyyy-MM-dd'));
  const [page, setPage] = useState(1);

  const { data, isLoading, error, refetch } = useQuery<PaginatedResponse<Match>>({
    queryKey: ['fixtures', dateFrom, dateTo, page],
    queryFn: () => api.getFixtures({ 
      date_from: dateFrom, 
      date_to: dateTo, 
      page, 
      page_size: 20 
    }),
    placeholderData: (previousData) => previousData,
  });

  const handleDateChange = (from: string, to: string) => {
    setDateFrom(from);
    setDateTo(to);
    setPage(1);
  };

  if (isLoading) return <LoadingState message="Loading fixtures..." />;
  if (error) return <ErrorState message="Failed to load fixtures" onRetry={refetch} />;
  if (!data || data.data.length === 0) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Upcoming Fixtures</h1>
        <DateRangePicker 
          dateFrom={dateFrom} 
          dateTo={dateTo} 
          onChange={handleDateChange} 
        />
        <EmptyState 
          icon={<Calendar />}
          title="No fixtures found"
          message="Try selecting a different date range"
        />
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Upcoming Fixtures</h1>
      
      <DateRangePicker 
        dateFrom={dateFrom} 
        dateTo={dateTo} 
        onChange={handleDateChange} 
      />

      {/* Fixtures Table */}
      <div className="mt-6 bg-white shadow-sm rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Date & Time
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Match
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Competition
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Venue
              </th>
              <th className="relative px-6 py-3">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.data.map((match) => (
              <tr key={match.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {format(new Date(match.match_date), 'MMM dd, HH:mm')}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">
                    {match.home_team.name} vs {match.away_team.name}
                  </div>
                  {match.status !== 'scheduled' && (
                    <div className="text-sm text-gray-500">
                      {match.home_score} - {match.away_score}
                    </div>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {match.competition}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {match.venue || '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <Link
                    to={`/match/${match.id}`}
                    className="text-blue-600 hover:text-blue-900"
                  >
                    View Details
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {data.total_pages > 1 && (
        <div className="mt-6 flex items-center justify-between">
          <div className="flex-1 flex justify-between sm:hidden">
            <button
              onClick={() => setPage(page - 1)}
              disabled={page === 1}
              className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(page + 1)}
              disabled={page === data.total_pages}
              className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
            >
              Next
            </button>
          </div>
          <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700">
                Showing page <span className="font-medium">{page}</span> of{' '}
                <span className="font-medium">{data.total_pages}</span>
              </p>
            </div>
            <div>
              <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                <button
                  onClick={() => setPage(page - 1)}
                  disabled={page === 1}
                  className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                >
                  <ChevronLeft className="h-5 w-5" />
                </button>
                <button
                  onClick={() => setPage(page + 1)}
                  disabled={page === data.total_pages}
                  className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                >
                  <ChevronRight className="h-5 w-5" />
                </button>
              </nav>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Date Range Picker Component
function DateRangePicker({ 
  dateFrom, 
  dateTo, 
  onChange 
}: { 
  dateFrom: string; 
  dateTo: string; 
  onChange: (from: string, to: string) => void;
}) {
  return (
    <div className="bg-white p-4 rounded-lg shadow-sm">
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <label htmlFor="date-from" className="block text-sm font-medium text-gray-700">
            From Date
          </label>
          <input
            type="date"
            id="date-from"
            value={dateFrom}
            onChange={(e) => onChange(e.target.value, dateTo)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          />
        </div>
        <div className="flex-1">
          <label htmlFor="date-to" className="block text-sm font-medium text-gray-700">
            To Date
          </label>
          <input
            type="date"
            id="date-to"
            value={dateTo}
            onChange={(e) => onChange(dateFrom, e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          />
        </div>
        <div className="flex items-end">
          <button
            onClick={() => {
              const today = new Date();
              onChange(
                format(today, 'yyyy-MM-dd'),
                format(addDays(today, 7), 'yyyy-MM-dd')
              );
            }}
            className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            Next 7 Days
          </button>
        </div>
      </div>
    </div>
  );
}