import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { initBridge } from './bridge'
import './index.css'
import App from './App.tsx'

initBridge()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
