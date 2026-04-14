import { Canvas } from "@react-three/fiber";
import { NeuralSphere } from "./components/NeuralSphere";
import { PhonemeText } from "./components/PhonemeText";
import { useAppState } from "./useAppState";
import { useMicCapture } from "./hooks/useMicCapture";
import { useTtsPlayer } from "./hooks/useTtsPlayer";
import "./App.css";

function App() {
  const state = useAppState();
  const { amplitude: micAmplitude } = useMicCapture(state);
  const { displayText, amplitude: ttsAmplitude } = useTtsPlayer();
  const amplitude = state === "SPEAKING" ? ttsAmplitude : micAmplitude;

  return (
    <div
      style={{
        width: "100vw",
        height: "100vh",
        background: "#050505",
        position: "relative",
        overflow: "hidden",
      }}
    >
      <Canvas
        camera={{ position: [0, 0, 5], fov: 50 }}
        gl={{ antialias: true, alpha: true }}
        style={{ background: "transparent" }}
      >
        <NeuralSphere state={state} amplitude={amplitude} />
      </Canvas>

      <PhonemeText text={displayText} />

      <div
        style={{
          position: "absolute",
          bottom: "32px",
          left: 0,
          right: 0,
          textAlign: "center",
          color: "#00e5ff",
          fontSize: "11px",
          fontWeight: 300,
          letterSpacing: "4px",
          opacity: 0.5,
          fontFamily: "sans-serif",
          pointerEvents: "none",
        }}
      >
        {state}
      </div>

      {(window as any).__mockBridge && (
        <DevControls currentState={state} />
      )}
    </div>
  );
}

function DevControls({ currentState }: { currentState: string }) {
  const states = ["IDLE", "LISTENING", "PROCESSING", "SPEAKING", "WAITING"] as const;

  return (
    <div
      style={{
        position: "absolute",
        top: "16px",
        left: "50%",
        transform: "translateX(-50%)",
        display: "flex",
        gap: "6px",
      }}
    >
      {states.map((s) => (
        <button
          key={s}
          onClick={() => (window as any).__mockBridge.simulateStateChange(s)}
          style={{
            padding: "5px 10px",
            background: currentState === s ? "#00e5ff" : "#111",
            color: currentState === s ? "#000" : "#aaa",
            border: "1px solid #222",
            borderRadius: "3px",
            cursor: "pointer",
            fontSize: "10px",
            letterSpacing: "1px",
          }}
        >
          {s}
        </button>
      ))}
    </div>
  );
}

export default App;
