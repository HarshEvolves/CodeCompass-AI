export default function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5 px-4 py-3 bg-bg-secondary/40 border border-border-default/60 rounded-2xl w-fit">
      <span className="text-xs text-text-secondary mr-1.5 font-medium">AI is scanning codebase</span>
      <div className="w-1.5 h-1.5 bg-accent rounded-full animate-bounce [animation-delay:-0.3s]" />
      <div className="w-1.5 h-1.5 bg-accent rounded-full animate-bounce [animation-delay:-0.15s]" />
      <div className="w-1.5 h-1.5 bg-accent rounded-full animate-bounce" />
    </div>
  );
}
