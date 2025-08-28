import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.tsx';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { ErrorBoundary } from 'react-error-boundary';
import { queryClient } from './lib/queryClient';

// Display git commit hash on startup
const gitCommitHash = import.meta.env.VITE_GIT_COMMIT_HASH || 'local';
console.log(`Application started - Git commit: ${gitCommitHash}`);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorBoundary fallback={<p>Something went wrong.</p>}>
      <QueryClientProvider client={queryClient}>
        <App />
        <ReactQueryDevtools initialIsOpen={false} buttonPosition="top-right" />
      </QueryClientProvider>
    </ErrorBoundary>
  </StrictMode>
);
