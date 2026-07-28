/**
 * CodeCompass — Root App Component
 *
 * Sets up the provider hierarchy:
 *   QueryClientProvider → BrowserRouter → Routes
 *
 * For Phase 1 we only have the LandingPage.
 * More routes (login, dashboard, chat) will be added in later phases.
 */

import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import LandingPage from "@/pages/LandingPage";

// Create the TanStack Query client with sensible defaults
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,       // Data stays fresh for 5 minutes
      gcTime: 10 * 60 * 1000,         // Unused cache kept for 10 minutes
      retry: 1,                        // Retry failed requests once
      refetchOnWindowFocus: false,     // Don't refetch when tab is focused
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          {/* Future routes (Phase 3+):
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/chat/:repoId" element={<ChatPage />} />
          */}
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
