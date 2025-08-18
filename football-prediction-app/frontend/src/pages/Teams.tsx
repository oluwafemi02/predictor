import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Users, ChevronLeft, ChevronRight, X } from 'lucide-react';
import { api, type Team, type PaginatedResponse } from '../lib/api';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';

export function Teams() {
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);

  const { data, isLoading, error, refetch } = useQuery<PaginatedResponse<Team>>({
    queryKey: ['teams', search, page],
    queryFn: () => api.getTeams({ search, page, page_size: 20 }),
    placeholderData: (previousData) => previousData,
  });

  const handleSearch = (value: string) => {
    setSearch(value);
    setPage(1);
  };

  if (isLoading) return <LoadingState message="Loading teams..." />;
  if (error) return <ErrorState message="Failed to load teams" onRetry={refetch} />;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Teams</h1>
      
      {/* Search Bar */}
      <div className="mb-6">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            placeholder="Search teams..."
          />
        </div>
      </div>

      {!data || data.data.length === 0 ? (
        <EmptyState 
          icon={<Users />}
          title="No teams found"
          message={search ? "Try a different search term" : "No teams available"}
        />
      ) : (
        <>
          {/* Teams Grid */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.data.map((team) => (
              <div
                key={team.id}
                className="bg-white rounded-lg shadow-sm p-4 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => setSelectedTeam(team)}
              >
                <div className="flex items-center">
                  {team.logo_url ? (
                    <img
                      src={team.logo_url}
                      alt={team.name}
                      className="h-12 w-12 rounded-full object-contain"
                    />
                  ) : (
                    <div className="h-12 w-12 rounded-full bg-gray-200 flex items-center justify-center">
                      <Users className="h-6 w-6 text-gray-400" />
                    </div>
                  )}
                  <div className="ml-4 flex-1">
                    <h3 className="text-lg font-medium text-gray-900">{team.name}</h3>
                    {team.stadium && (
                      <p className="text-sm text-gray-500">{team.stadium}</p>
                    )}
                  </div>
                </div>
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
        </>
      )}

      {/* Team Squad Modal */}
      {selectedTeam && (
        <TeamSquadModal
          team={selectedTeam}
          onClose={() => setSelectedTeam(null)}
        />
      )}
    </div>
  );
}

// Team Squad Modal Component
function TeamSquadModal({ team, onClose }: { team: Team; onClose: () => void }) {
  const { data: squad, isLoading, error } = useQuery({
    queryKey: ['team-squad', team.id],
    queryFn: () => api.getTeamSquad(team.id),
  });

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose} />

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                {team.name} Squad
              </h3>
              <button
                onClick={onClose}
                className="rounded-md text-gray-400 hover:text-gray-500 focus:outline-none"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            {isLoading && <LoadingState message="Loading squad..." />}
            {error && <ErrorState message="Failed to load squad" />}
            
            {squad && squad.length === 0 && (
              <EmptyState 
                title="No squad data available"
                message="Squad information for this team is not available"
              />
            )}

            {squad && squad.length > 0 && (
              <div className="space-y-4">
                {['Goalkeeper', 'Defender', 'Midfielder', 'Forward'].map((position) => {
                  const players = squad.filter(p => p.position === position);
                  if (players.length === 0) return null;
                  
                  return (
                    <div key={position}>
                      <h4 className="font-medium text-gray-900 mb-2">{position}s</h4>
                      <div className="space-y-2">
                        {players.map((player) => (
                          <div key={player.id} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
                            <div className="flex items-center">
                              {player.jersey_number && (
                                <span className="text-sm font-medium text-gray-500 w-8">
                                  {player.jersey_number}
                                </span>
                              )}
                              <span className="text-sm text-gray-900">{player.name}</span>
                            </div>
                            <div className="flex items-center space-x-4 text-sm text-gray-500">
                              {player.age && <span>Age: {player.age}</span>}
                              {player.nationality && <span>{player.nationality}</span>}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}