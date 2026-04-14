/**
 * Neural Sphere — Three.js 기반 상태별 애니메이션
 *
 * 노드(Points) + 엣지(LineSegments) 구조
 * 색상: 노드 #00e5ff / 엣지 rgba(0,229,255,0.2) / 활성 glow
 *
 * 상태별 동작:
 * IDLE       — 천천히 자전, dim (opacity 0.4)
 * LISTENING  — 팽창 ~1.3x + 마이크 amplitude 진동
 * PROCESSING — 빠른 pulse (sin 기반 scale)
 * SPEAKING   — TTS amplitude 연동 팽창/수축
 * WAITING    — 토네이도 (나선형 고속 y축 회전)
 */

import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { type AppState } from "../bridge";

const NODE_COUNT = 180;
const BASE_RADIUS = 1.4;
const EDGE_THRESHOLD = 0.72;
const NODE_COLOR = new THREE.Color("#00e5ff");
const EDGE_COLOR = new THREE.Color("#00e5ff");

// ------------------------------------------------------------------ //
// 피보나치 구 배치 — 균일 분포
// ------------------------------------------------------------------ //
function fibonacciSphere(count: number, radius: number): Float32Array {
  const pos = new Float32Array(count * 3);
  const golden = (1 + Math.sqrt(5)) / 2;
  for (let i = 0; i < count; i++) {
    const theta = Math.acos(1 - (2 * i + 1) / count);
    const phi = (2 * Math.PI * i) / golden;
    pos[i * 3] = radius * Math.sin(theta) * Math.cos(phi);
    pos[i * 3 + 1] = radius * Math.sin(theta) * Math.sin(phi);
    pos[i * 3 + 2] = radius * Math.cos(theta);
  }
  return pos;
}

// ------------------------------------------------------------------ //
// 엣지 생성 — threshold 거리 이내 노드 연결
// ------------------------------------------------------------------ //
function buildEdges(positions: Float32Array, threshold: number): Float32Array {
  const lines: number[] = [];
  const n = positions.length / 3;
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      const dx = positions[i * 3] - positions[j * 3];
      const dy = positions[i * 3 + 1] - positions[j * 3 + 1];
      const dz = positions[i * 3 + 2] - positions[j * 3 + 2];
      if (Math.sqrt(dx * dx + dy * dy + dz * dz) < threshold) {
        lines.push(
          positions[i * 3], positions[i * 3 + 1], positions[i * 3 + 2],
          positions[j * 3], positions[j * 3 + 1], positions[j * 3 + 2]
        );
      }
    }
  }
  return new Float32Array(lines);
}

// ------------------------------------------------------------------ //
// 컴포넌트
// ------------------------------------------------------------------ //
interface Props {
  state: AppState;
  amplitude: number;
}

export function NeuralSphere({ state, amplitude }: Props) {
  const groupRef = useRef<THREE.Group>(null);
  const nodeMatRef = useRef<THREE.PointsMaterial>(null);
  const edgeMatRef = useRef<THREE.LineBasicMaterial>(null);

  const { nodePositions, edgePositions } = useMemo(() => {
    const nodePositions = fibonacciSphere(NODE_COUNT, BASE_RADIUS);
    const edgePositions = buildEdges(nodePositions, EDGE_THRESHOLD);
    return { nodePositions, edgePositions };
  }, []);

  const nodeGeo = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(nodePositions.slice(), 3));
    return geo;
  }, [nodePositions]);

  const edgeGeo = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(edgePositions, 3));
    return geo;
  }, [edgePositions]);

  useFrame((_, delta) => {
    const group = groupRef.current;
    const nodeMat = nodeMatRef.current;
    const edgeMat = edgeMatRef.current;
    if (!group || !nodeMat || !edgeMat) return;

    const amp = amplitude;

    switch (state) {
      case "IDLE": {
        group.rotation.y += delta * 0.15;
        group.rotation.x += delta * 0.04;
        const targetScale = 1.0;
        group.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), 0.05);
        nodeMat.opacity = THREE.MathUtils.lerp(nodeMat.opacity, 0.4, 0.05);
        edgeMat.opacity = THREE.MathUtils.lerp(edgeMat.opacity, 0.12, 0.05);
        break;
      }
      case "LISTENING": {
        group.rotation.y += delta * 0.3;
        const listenScale = 1.3 + amp * 0.25;
        group.scale.lerp(new THREE.Vector3(listenScale, listenScale, listenScale), 0.1);
        nodeMat.opacity = THREE.MathUtils.lerp(nodeMat.opacity, 0.9, 0.08);
        edgeMat.opacity = THREE.MathUtils.lerp(edgeMat.opacity, 0.25, 0.08);
        break;
      }
      case "PROCESSING": {
        const pulse = 1.0 + Math.sin(Date.now() * 0.008) * 0.15;
        group.rotation.y += delta * 0.6;
        group.scale.set(pulse, pulse, pulse);
        nodeMat.opacity = 0.75 + Math.sin(Date.now() * 0.01) * 0.2;
        edgeMat.opacity = 0.2;
        break;
      }
      case "SPEAKING": {
        group.rotation.y += delta * 0.25;
        const speakScale = 1.0 + amp * 0.4;
        group.scale.lerp(new THREE.Vector3(speakScale, speakScale, speakScale), 0.15);
        nodeMat.opacity = THREE.MathUtils.lerp(nodeMat.opacity, 0.7 + amp * 0.3, 0.1);
        edgeMat.opacity = THREE.MathUtils.lerp(edgeMat.opacity, 0.15 + amp * 0.2, 0.1);
        break;
      }
      case "WAITING": {
        // 토네이도 — 빠른 y축 회전 + 느린 x축 나선
        group.rotation.y += delta * 1.8;
        group.rotation.x += delta * 0.12;
        const waitScale = 1.05 + Math.sin(Date.now() * 0.003) * 0.08;
        group.scale.lerp(new THREE.Vector3(waitScale, waitScale, waitScale), 0.06);
        nodeMat.opacity = THREE.MathUtils.lerp(nodeMat.opacity, 0.55, 0.05);
        edgeMat.opacity = THREE.MathUtils.lerp(edgeMat.opacity, 0.18, 0.05);
        break;
      }
    }
  });

  return (
    <group ref={groupRef}>
      <points geometry={nodeGeo}>
        <pointsMaterial
          ref={nodeMatRef}
          color={NODE_COLOR}
          size={0.045}
          transparent
          opacity={0.4}
          sizeAttenuation
        />
      </points>
      <lineSegments geometry={edgeGeo}>
        <lineBasicMaterial
          ref={edgeMatRef}
          color={EDGE_COLOR}
          transparent
          opacity={0.12}
        />
      </lineSegments>
    </group>
  );
}
