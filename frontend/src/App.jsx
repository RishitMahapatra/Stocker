import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Signals from './pages/Signals';
import Portfolio from './pages/Portfolio';
import TickerDetail from './pages/TickerDetail';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 15000,
      retry: 1,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Navbar />
        <Routes>
          <Route path="/"                element={<Dashboard />} />
          <Route path="/signals"         element={<Signals />} />
          <Route path="/portfolio"       element={<Portfolio />} />
          <Route path="/ticker/:ticker"  element={<TickerDetail />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
