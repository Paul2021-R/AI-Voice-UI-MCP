/**
 * Float32Array PCM → 16-bit mono WAV ArrayBuffer 인코더
 * Whisper.cpp 입력 요건: 16kHz, mono, int16 PCM
 */

function writeString(view: DataView, offset: number, str: string): void {
  for (let i = 0; i < str.length; i++) {
    view.setUint8(offset + i, str.charCodeAt(i));
  }
}

export function encodeWav(samples: Float32Array, sampleRate: number): ArrayBuffer {
  const bitsPerSample = 16;
  const numChannels = 1;
  const blockAlign = numChannels * (bitsPerSample / 8);
  const byteRate = sampleRate * blockAlign;
  const dataSize = samples.length * (bitsPerSample / 8);

  const buffer = new ArrayBuffer(44 + dataSize);
  const view = new DataView(buffer);

  writeString(view, 0, "RIFF");
  view.setUint32(4, 36 + dataSize, true);
  writeString(view, 8, "WAVE");
  writeString(view, 12, "fmt ");
  view.setUint32(16, 16, true);       // fmt chunk size
  view.setUint16(20, 1, true);        // PCM
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, byteRate, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, bitsPerSample, true);
  writeString(view, 36, "data");
  view.setUint32(40, dataSize, true);

  // float32 → int16 변환
  let offset = 44;
  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    offset += 2;
  }

  return buffer;
}

/** OfflineAudioContext를 이용해 네이티브 샘플레이트 → 16kHz 리샘플링 */
export async function resampleTo16kHz(
  samples: Float32Array,
  fromRate: number
): Promise<Float32Array> {
  const targetRate = 16000;
  if (fromRate === targetRate) return samples;

  const outLength = Math.ceil((samples.length * targetRate) / fromRate);
  const offline = new OfflineAudioContext(1, outLength, targetRate);
  const buf = offline.createBuffer(1, samples.length, fromRate);
  buf.getChannelData(0).set(samples);

  const src = offline.createBufferSource();
  src.buffer = buf;
  src.connect(offline.destination);
  src.start();

  const rendered = await offline.startRendering();
  return rendered.getChannelData(0);
}

/** ArrayBuffer → base64 문자열 */
export function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}
