import { useEffect } from "react";

export default function VoiceAssistant({ message, rate = 1, onFinished }) {
  useEffect(() => {
    if (!message) return;
    if (!("speechSynthesis" in window)) {
      onFinished?.();
      return;
    }
    let active = true;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(message);
    utterance.rate = rate;
    utterance.onend = () => active && onFinished?.();
    utterance.onerror = () => active && onFinished?.();
    window.speechSynthesis.speak(utterance);
    return () => {
      active = false;
      window.speechSynthesis.cancel();
    };
  }, [message, rate, onFinished]);
  return <span className="sr-only" aria-live="polite">{message}</span>;
}
