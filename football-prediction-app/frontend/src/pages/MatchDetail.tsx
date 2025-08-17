import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import { Calendar, MapPin, Trophy, ArrowLeft } from 'lucide-react';
import { api } from '../lib/api';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';

export function MatchDetail() {
  const { id } = useParams<{ id: string }>();
  const matchId = parseInt(id || '0', 10);

  const { data: match, isLoading, error, refetch } = useQuery({
    queryKey: ['match', matchId],
    queryFn: () => api.getMatchDetails(matchId),
    enabled: !!matchId,
  });

  if (isLoading) return <LoadingState message="Loading match details..." />;
  if (error) return <ErrorState message="Failed to load match details" onRetry={refetch} />;
  if (!match) return <ErrorState message="Match not found" />;

  const isFinished = match.status === 'finished';
  const isLive = match.status === 'in_play';

  return (
    <div>
      {/* Back button */}
      <Link
        to="/fixtures"
        className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 mb-4"
      >
        <ArrowLeft className="w-4 h-4 mr-1" />
        Back to fixtures
      </Link>

      {/* Match Header */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <div className="flex flex-col sm:flex-row items-center justify-between">
          {/* Home Team */}
          <div className="text-center sm:text-right flex-1">
            <h2 className="text-2xl font-bold text-gray-900">
              {match.home_team.name}
            </h2>
            {match.home_team.logo_url && (
              <img
                src={match.home_team.logo_url}
                alt={match.home_team.name}
                className="h-20 w-20 mx-auto sm:ml-auto sm:mr-0 mt-2 object-contain"
              />
            )}
          </div>

          {/* Score or VS */}
          <div className="mx-8 text-center">
            {isFinished || isLive ? (
              <div>
                <div className="text-4xl font-bold text-gray-900">
                  {match.home_score} - {match.away_score}
                </div>
                {match.home_score_halftime !== null && match.away_score_halftime !== null && (
                  <div className="text-sm text-gray-500 mt-1">
                    HT: {match.home_score_halftime} - {match.away_score_halftime}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-3xl font-bold text-gray-400">VS</div>
            )}
            {isLive && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 mt-2">
                LIVE
              </span>
            )}
          </div>

          {/* Away Team */}
          <div className="text-center sm:text-left flex-1">
            <h2 className="text-2xl font-bold text-gray-900">
              {match.away_team.name}
            </h2>
            {match.away_team.logo_url && (
              <img
                src={match.away_team.logo_url}
                alt={match.away_team.name}
                className="h-20 w-20 mx-auto sm:mr-auto sm:ml-0 mt-2 object-contain"
              />
            )}
          </div>
        </div>

        {/* Match Info */}
        <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
          <div className="flex items-center justify-center sm:justify-start">
            <Calendar className="w-4 h-4 mr-2 text-gray-400" />
            <span className="text-gray-600">
              {format(new Date(match.match_date), 'PPpp')}
            </span>
          </div>
          {match.venue && (
            <div className="flex items-center justify-center">
              <MapPin className="w-4 h-4 mr-2 text-gray-400" />
              <span className="text-gray-600">{match.venue}</span>
            </div>
          )}
          {match.competition && (
            <div className="flex items-center justify-center sm:justify-end">
              <Trophy className="w-4 h-4 mr-2 text-gray-400" />
              <span className="text-gray-600">{match.competition}</span>
            </div>
          )}
        </div>
      </div>

      {/* Match Details */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Match Information */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Match Information
          </h3>
          <dl className="space-y-3">
            <div className="flex justify-between">
              <dt className="text-sm font-medium text-gray-500">Status</dt>
              <dd className="text-sm text-gray-900 capitalize">{match.status}</dd>
            </div>
            {match.season && (
              <div className="flex justify-between">
                <dt className="text-sm font-medium text-gray-500">Season</dt>
                <dd className="text-sm text-gray-900">{match.season}</dd>
              </div>
            )}
            {match.round && (
              <div className="flex justify-between">
                <dt className="text-sm font-medium text-gray-500">Round</dt>
                <dd className="text-sm text-gray-900">{match.round}</dd>
              </div>
            )}
            {match.referee && (
              <div className="flex justify-between">
                <dt className="text-sm font-medium text-gray-500">Referee</dt>
                <dd className="text-sm text-gray-900">{match.referee}</dd>
              </div>
            )}
            {match.attendance && (
              <div className="flex justify-between">
                <dt className="text-sm font-medium text-gray-500">Attendance</dt>
                <dd className="text-sm text-gray-900">
                  {match.attendance.toLocaleString()}
                </dd>
              </div>
            )}
          </dl>
        </div>

        {/* Actions */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Actions</h3>
          <div className="space-y-3">
            <Link
              to={`/predictions?match=${matchId}`}
              className="block w-full text-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              View Predictions
            </Link>
            <button
              disabled
              className="block w-full text-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-400 bg-gray-50 cursor-not-allowed"
            >
              Head to Head (Coming Soon)
            </button>
            <button
              disabled
              className="block w-full text-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-400 bg-gray-50 cursor-not-allowed"
            >
              Live Stats (Coming Soon)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}