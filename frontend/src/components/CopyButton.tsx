import { useState } from "react";

interface CopyButtonProps {
  content: string;
}

export default function CopyButton({ content }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy text", err);
    }
  };

  return (
    <button
      onClick={handleCopy}
      className={`px-2.5 py-1.5 rounded-lg text-xs font-semibold select-none flex items-center gap-1.5 transition-all cursor-pointer ${
        copied
          ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/35"
          : "bg-bg-primary hover:bg-bg-secondary text-text-secondary border border-border-default/60 hover:text-text-primary"
      }`}
    >
      <span>{copied ? "✓" : "📋"}</span>
      <span>{copied ? "Copied" : "Copy"}</span>
    </button>
  );
}
