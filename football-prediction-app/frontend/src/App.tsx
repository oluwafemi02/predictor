import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Home } from './pages/Home';
import { Fixtures } from './pages/Fixtures';
import { Predictions } from './pages/Predictions';
import { Teams } from './pages/Teams';
import { MatchDetail } from './pages/MatchDetail';
import { Layout } from './components/Layout';

// Create a query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000, // 1 minute
      cacheTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Home />} />
            <Route path="fixtures" element={<Fixtures />} />
            <Route path="predictions" element={<Predictions />} />
            <Route path="teams" element={<Teams />} />
            <Route path="match/:id" element={<MatchDetail />} />
          </Route>
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
