import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './styles/theme.css'
import './index.css'
import App from './App.jsx'

// Set dark theme immediately to avoid flash of unstyled content
document.documentElement.setAttribute('data-theme', 'dark')
document.documentElement.style.colorScheme = 'dark'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
