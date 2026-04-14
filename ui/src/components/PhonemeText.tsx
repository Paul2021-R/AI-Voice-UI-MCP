/**
 * 음소 싱크 자막 오버레이
 * fade-in/out 0.15s, weight 300 sans-serif, 흰색, Sphere 중앙
 */

import { useEffect, useRef } from "react";

interface Props {
  text: string | null;
}

export function PhonemeText({ text }: Props) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (text) {
      el.style.opacity = "1";
    } else {
      el.style.opacity = "0";
    }
  }, [text]);

  return (
    <div
      ref={ref}
      style={{
        position: "absolute",
        bottom: "calc(50% - 60px)",
        left: 0,
        right: 0,
        textAlign: "center",
        color: "#ffffff",
        fontSize: "22px",
        fontWeight: 300,
        fontFamily: "sans-serif",
        letterSpacing: "1px",
        opacity: 0,
        transition: "opacity 0.15s ease",
        pointerEvents: "none",
        userSelect: "none",
      }}
    >
      {text}
    </div>
  );
}
