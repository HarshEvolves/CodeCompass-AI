import { useState } from "react";
import type { KeyboardEvent, ChangeEvent } from "react";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled: boolean;
}

export default function ChatInput({ onSendMessage, disabled }: ChatInputProps) {
  const [text, setText] = useState("");

  const handleSend = () => {
    if (!text.trim() || disabled) return;
    onSendMessage(text.trim());
    setText("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex gap-2.5 p-4 border-t border-border-default bg-bg-secondary/40 backdrop-blur-md items-end">
      <textarea
        value={text}
        onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={disabled ? "Please wait for AI response..." : "Ask a question about the repository (Press Enter to send)..."}
        disabled={disabled}
        rows={1}
        className="flex-1 bg-bg-primary border border-border-default/80 focus:border-accent text-text-primary rounded-xl px-4 py-3 text-sm focus:outline-none resize-none max-h-32 min-h-[46px] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
      />
      <button
        onClick={handleSend}
        disabled={disabled || !text.trim()}
        className="px-4.5 py-3 rounded-xl bg-accent text-white font-semibold text-sm hover:bg-accent-hover cursor-pointer disabled:bg-bg-secondary disabled:text-text-muted disabled:cursor-not-allowed transition-all flex items-center justify-center min-h-[46px]"
      >
        <span>Send</span>
      </button>
    </div>
  );
}
