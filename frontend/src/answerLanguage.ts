import type { AnswerLanguage } from "./api";

export const ANSWER_LANGUAGES: { value: AnswerLanguage; label: string }[] = [
  { value: "auto", label: "Auto (match question)" },
  { value: "en", label: "English" },
  { value: "tr", label: "Türkçe" },
  { value: "de", label: "Deutsch" },
  { value: "es", label: "Español" },
  { value: "fr", label: "Français" },
];

const STORAGE_KEY = "documind.answerLanguage";

export function loadAnswerLanguage(): AnswerLanguage {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (ANSWER_LANGUAGES.some((option) => option.value === saved)) {
      return saved as AnswerLanguage;
    }
  } catch {
    // localStorage kapalı olabilir; varsayılana dön.
  }
  return "auto";
}

export function saveAnswerLanguage(value: AnswerLanguage): void {
  try {
    localStorage.setItem(STORAGE_KEY, value);
  } catch {
    // Kaydedilemese de seçim bu oturumda geçerli kalır.
  }
}
