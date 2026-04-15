import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { initBridge } from './bridge'
import './index.css'
import App from './App.tsx'

function mount() {
  initBridge()
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}

// pywebview 환경에서는 API 주입 완료 후 마운트
if ((window as any).pywebview) {
  mount()
} else {
  window.addEventListener('pywebviewready', mount, { once: true })
  // pywebviewready 이벤트가 오지 않는 환경(일반 브라우저)은 즉시 마운트
  setTimeout(() => {
    if (!(window as any).pywebview) mount()
  }, 200)
}
