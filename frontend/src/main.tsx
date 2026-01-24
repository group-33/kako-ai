import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './i18n'
import App from './App.tsx'

// Workaround for Supabase AbortError in React StrictMode (navigator.locks issue)
if (typeof navigator !== 'undefined' && 'locks' in navigator) {
  navigator.locks.request = async (name: string, ...args: unknown[]) => {
    const callback = args[args.length - 1];
    if (typeof callback === 'function') {
      return callback({ name });
    }
  };
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
