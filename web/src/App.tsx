import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';

import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { Pipelines } from './pages/Pipelines';
import { PipelineDetail } from './pages/PipelineDetail';
import { AIInsights } from './pages/AIInsights';
import { Analytics } from './pages/Analytics';
import { Models } from './pages/Models';
import { Settings } from './pages/Settings';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { WebSocketProvider } from './contexts/WebSocketContext';

import './index.css';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <WebSocketProvider>
            <Router>
              <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
                <Layout>
                  <Routes>
                    <Route path="/" element={<Navigate to="/dashboard" replace />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/pipelines" element={<Pipelines />} />
                    <Route path="/pipelines/:id" element={<PipelineDetail />} />
                    <Route path="/ai-insights" element={<AIInsights />} />
                    <Route path="/analytics" element={<Analytics />} />
                    <Route path="/models" element={<Models />} />
                    <Route path="/settings" element={<Settings />} />
                  </Routes>
                </Layout>
                <Toaster
                  position="top-right"
                  toastOptions={{
                    duration: 4000,
                    style: {
                      background: '#363636',
                      color: '#fff',
                    },
                    success: {
                      duration: 3000,
                      style: {
                        background: '#10B981',
                      },
                    },
                    error: {
                      duration: 5000,
                      style: {
                        background: '#EF4444',
                      },
                    },
                  }}
                />
              </div>
            </Router>
          </WebSocketProvider>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;