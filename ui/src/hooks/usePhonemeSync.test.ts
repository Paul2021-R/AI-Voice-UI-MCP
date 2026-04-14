import { describe, expect, it } from "vitest";
import { groupPhememesToWords, type Phoneme } from "./usePhonemeSync";

describe("groupPhememesToWords", () => {
  it("공백 없는 음소를 하나의 단어로 묶는다", () => {
    const phonemes: Phoneme[] = [
      { text: "안", start_time: 0.0, end_time: 0.2 },
      { text: "녕", start_time: 0.2, end_time: 0.4 },
    ];
    const words = groupPhememesToWords(phonemes);
    expect(words).toHaveLength(1);
    expect(words[0].text).toBe("안녕");
    expect(words[0].start_time).toBe(0.0);
    expect(words[0].end_time).toBe(0.4);
  });

  it("공백 음소를 기준으로 두 단어로 분리한다", () => {
    const phonemes: Phoneme[] = [
      { text: "안", start_time: 0.0, end_time: 0.2 },
      { text: "녕", start_time: 0.2, end_time: 0.4 },
      { text: " ", start_time: 0.4, end_time: 0.5 },
      { text: "하", start_time: 0.5, end_time: 0.7 },
      { text: "세", start_time: 0.7, end_time: 0.9 },
      { text: "요", start_time: 0.9, end_time: 1.1 },
    ];
    const words = groupPhememesToWords(phonemes);
    expect(words).toHaveLength(2);
    expect(words[0].text).toBe("안녕");
    expect(words[1].text).toBe("하세요");
    expect(words[1].start_time).toBe(0.5);
    expect(words[1].end_time).toBe(1.1);
  });

  it("빈 phoneme 배열은 빈 word 배열을 반환한다", () => {
    expect(groupPhememesToWords([])).toHaveLength(0);
  });

  it("연속 공백을 올바르게 처리한다", () => {
    const phonemes: Phoneme[] = [
      { text: "A", start_time: 0.0, end_time: 0.1 },
      { text: " ", start_time: 0.1, end_time: 0.2 },
      { text: " ", start_time: 0.2, end_time: 0.3 },
      { text: "B", start_time: 0.3, end_time: 0.4 },
    ];
    const words = groupPhememesToWords(phonemes);
    expect(words).toHaveLength(2);
    expect(words[0].text).toBe("A");
    expect(words[1].text).toBe("B");
  });
});
