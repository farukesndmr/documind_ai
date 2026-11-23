import type { AnswerLanguage } from "../api";
import { ANSWER_LANGUAGES } from "../answerLanguage";

type LanguageSelectProps = {
  value: AnswerLanguage;
  onChange: (value: AnswerLanguage) => void;
  disabled?: boolean;
};

export function LanguageSelect({ value, onChange, disabled }: LanguageSelectProps) {
  return (
    <label className="language-select">
      <span>Answer in</span>
      <select
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value as AnswerLanguage)}
      >
        {ANSWER_LANGUAGES.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
