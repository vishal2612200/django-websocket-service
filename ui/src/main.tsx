import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
// stripped global CSS; using MUI theme styles only
// font removed to avoid build-time dependency; rely on system fonts via MUI theme

const container = document.getElementById('root')!
createRoot(container).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
