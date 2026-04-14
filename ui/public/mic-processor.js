/**
 * AudioWorklet 프로세서 — 마이크 PCM을 메인 스레드로 전달한다.
 * AudioWorklet 컨텍스트에서 실행되므로 ES module / import 사용 불가.
 */
class MicProcessor extends AudioWorkletProcessor {
  process(inputs) {
    const channel = inputs[0]?.[0];
    if (channel?.length) {
      // Float32Array 복사본을 메인 스레드로 전송
      this.port.postMessage(channel.slice());
    }
    return true; // 프로세서 유지
  }
}

registerProcessor("mic-processor", MicProcessor);
