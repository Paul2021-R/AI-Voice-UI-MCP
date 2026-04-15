import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { initBridge } from './bridge'
import './index.css'
import App from './App.tsx'

/** WKWebView autoplay 정책 우회 — 페이지 로드 시 AudioContext를 unlock한다. */
function unlockAudioContext() {
  const ctx = new AudioContext()
  const buf = ctx.createBuffer(1, 1, 22050)
  const src = ctx.createBufferSource()
  src.buffer = buf
  src.connect(ctx.destination)
  src.start(0)
  ctx.resume().then(() => ctx.close())
}

function mount() {
  unlockAudioContext()
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
