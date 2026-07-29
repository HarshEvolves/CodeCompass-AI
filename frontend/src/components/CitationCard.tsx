interface CitationProps {
  filePath: string;
  startLine: number;
  endLine: number;
}

export default function CitationCard({ filePath, startLine, endLine }: CitationProps) {
  // Extract filename for friendly visual display
  const fileName = filePath.split("/").pop() || filePath;

  return (
    <div
      className="inline-flex items-center gap-1.5 px-3 py-1 bg-accent/10 border border-accent/20 rounded-lg text-xs text-accent select-none hover:bg-accent/25 hover:border-accent/35 transition-colors cursor-help"
      title={`Cited from ${filePath} (lines ${startLine} to ${endLine})`}
    >
      <span className="text-[10px]">📄</span>
      <span className="font-medium max-w-[120px] truncate">{fileName}</span>
      <span className="opacity-65 font-mono">
        L{startLine === endLine ? startLine : `${startLine}-${endLine}`}
      </span>
    </div>
  );
}
