import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { format, addDays, startOfDay } from 'date-fns';
import { TrendingUp, ChevronLeft, ChevronRight } from 'lucide-react';
import { api, type PaginatedResponse, type Prediction } from '../lib/api';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';
import { Link } from 'react-router-dom';

export function Predictions() {
  const today = startOfDay(new Date());
  const [dateFrom, setDateFrom] = useState(format(today, 'yyyy-MM-dd'));
  const [dateTo, setDateTo] = useState(format(addDays(today, 7), 'yyyy-MM-dd'));
  const [page, setPage] = useState(1);

  const { data, isLoading, error, refetch } = useQuery<PaginatedResponse<Prediction>>({
    queryKey: ['predictions', dateFrom, dateTo, page],
    queryFn: () => api.getPredictions({ 
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

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'text-green-600 bg-green-100';
    if (confidence >= 60) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getOutcomeColor = (outcome: string) => {
    if (outcome.includes('Home')) return 'text-blue-600';
    if (outcome.includes('Away')) return 'text-purple-600';
    return 'text-gray-600';
  };

  if (isLoading) return <LoadingState message="Loading predictions..." />;
  if (error) return <ErrorState message="Failed to load predictions" onRetry={refetch} />;
  if (!data || data.data.length === 0) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Match Predictions</h1>
        <DateRangePicker 
          dateFrom={dateFrom} 
          dateTo={dateTo} 
          onChange={handleDateChange} 
        />
        <EmptyState 
          icon={<TrendingUp />}
          title="No predictions available"
          message="Try selecting a different date range"
        />
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Match Predictions</h1>
      
      <DateRangePicker 
        dateFrom={dateFrom} 
        dateTo={dateTo} 
        onChange={handleDateChange} 
      />

      {/* Predictions List */}
      <div className="mt-6 space-y-4">
        {data.data.map((prediction) => (
          <div key={prediction.id} className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                {prediction.match && (
                  <>
                    <div className="text-sm text-gray-500 mb-1">
                      {format(new Date(prediction.match.match_date), 'MMM dd, yyyy HH:mm')}
                    </div>
                    <h3 className="text-lg font-medium text-gray-900">
                      {prediction.match.home_team.name} vs {prediction.match.away_team.name}
                    </h3>
                    <div className="text-sm text-gray-500 mt-1">
                      {prediction.match.competition}
                    </div>
                  </>
                )}
              </div>
              
              <Link
                to={`/match/${prediction.match_id}`}
                className="text-blue-600 hover:text-blue-900 text-sm"
              >
                View Match
              </Link>
            </div>

            <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* Predicted Outcome */}
              <div>
                <div className="text-sm font-medium text-gray-500">Predicted Outcome</div>
                <div className={`mt-1 text-lg font-semibold ${getOutcomeColor(prediction.predicted_outcome || '')}`}>
                  {prediction.predicted_outcome}
                </div>
              </div>

              {/* Confidence */}
              {prediction.confidence && (
                <div>
                  <div className="text-sm font-medium text-gray-500">Confidence</div>
                  <div className="mt-1">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getConfidenceColor(prediction.confidence)}`}>
                      {prediction.confidence.toFixed(1)}%
                    </span>
                  </div>
                </div>
              )}

              {/* Prediction Type */}
              <div>
                <div className="text-sm font-medium text-gray-500">Model Type</div>
                <div className="mt-1 text-sm text-gray-900">
                  {prediction.prediction_type}
                </div>
              </div>
            </div>

            {/* Probabilities */}
            {(prediction.home_win_probability || prediction.draw_probability || prediction.away_win_probability) && (
              <div className="mt-4 grid grid-cols-3 gap-4">
                <div className="text-center p-3 bg-gray-50 rounded">
                  <div className="text-sm font-medium text-gray-500">Home Win</div>
                  <div className="mt-1 text-lg font-semibold text-gray-900">
                    {(prediction.home_win_probability! * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded">
                  <div className="text-sm font-medium text-gray-500">Draw</div>
                  <div className="mt-1 text-lg font-semibold text-gray-900">
                    {(prediction.draw_probability! * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded">
                  <div className="text-sm font-medium text-gray-500">Away Win</div>
                  <div className="mt-1 text-lg font-semibold text-gray-900">
                    {(prediction.away_win_probability! * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Pagination */}
      {data.total_pages > 1 && (
        <div className="mt-6 flex items-center justify-center">
          <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
            <button
              onClick={() => setPage(page - 1)}
              disabled={page === 1}
              className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <span className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
              Page {page} of {data.total_pages}
            </span>
            <button
              onClick={() => setPage(page + 1)}
              disabled={page === data.total_pages}
              className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </nav>
        </div>
      )}
    </div>
  );
}

// Reuse DateRangePicker from Fixtures
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