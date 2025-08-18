import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Calendar, TrendingUp, Users, Activity } from 'lucide-react';
import { api } from '../lib/api';

export function Home() {
  const { data: version } = useQuery<{
    version: string;
    git_commit: string;
    deployment_time: string;
    environment: string;
    features: Record<string, boolean>;
  }>({
    queryKey: ['version'],
    queryFn: api.getVersion,
  });

  const features = [
    {
      name: 'Upcoming Fixtures',
      description: 'View upcoming matches across all major leagues',
      icon: Calendar,
      href: '/fixtures',
      color: 'bg-blue-500',
    },
    {
      name: 'Match Predictions',
      description: 'AI-powered predictions with confidence scores',
      icon: TrendingUp,
      href: '/predictions',
      color: 'bg-green-500',
    },
    {
      name: 'Team Squads',
      description: 'Browse team rosters and player information',
      icon: Users,
      href: '/teams',
      color: 'bg-purple-500',
    },
  ];

  return (
    <div>
      {/* Hero Section */}
      <div className="bg-white rounded-lg shadow-sm p-8 mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome to Football Predictor
        </h1>
        <p className="mt-2 text-lg text-gray-600">
          Get AI-powered match predictions and comprehensive football data
        </p>
        
        {version && (
          <div className="mt-4 flex items-center text-sm text-gray-500">
            <Activity className="w-4 h-4 mr-2" />
            <span>
              Version {version.version} • Environment: {version.environment}
            </span>
          </div>
        )}
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {features.map((feature) => {
          const Icon = feature.icon;
          return (
            <Link
              key={feature.name}
              to={feature.href}
              className="group relative rounded-lg p-6 bg-white hover:shadow-lg transition-shadow"
            >
              <div>
                <span
                  className={`rounded-lg inline-flex p-3 ${feature.color} text-white`}
                >
                  <Icon className="h-6 w-6" aria-hidden="true" />
                </span>
              </div>
              <div className="mt-8">
                <h3 className="text-lg font-medium text-gray-900">
                  {feature.name}
                </h3>
                <p className="mt-2 text-sm text-gray-500">
                  {feature.description}
                </p>
              </div>
              <span
                className="pointer-events-none absolute top-6 right-6 text-gray-300 group-hover:text-gray-400"
                aria-hidden="true"
              >
                <svg
                  className="h-6 w-6"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M20 4h1a1 1 0 00-1-1v1zm-1 12a1 1 0 102 0h-2zM8 3a1 1 0 000 2V3zM3.293 19.293a1 1 0 101.414 1.414l-1.414-1.414zM19 4v12h2V4h-2zm1-1H8v2h12V3zm-.707.293l-16 16 1.414 1.414 16-16-1.414-1.414z" />
                </svg>
              </span>
            </Link>
          );
        })}
      </div>

      {/* System Status */}
      {version && (
        <div className="mt-8 bg-gray-50 rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            System Status
          </h2>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
            {Object.entries(version.features).map(([feature, enabled]) => (
              <div key={feature} className="flex items-center">
                <div
                  className={`h-2 w-2 rounded-full mr-2 ${
                    enabled ? 'bg-green-400' : 'bg-gray-300'
                  }`}
                />
                <span className="text-sm text-gray-600 capitalize">
                  {feature}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}