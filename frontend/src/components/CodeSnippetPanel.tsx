import { useState } from "react";

interface CodeSnippetPanelProps {
  files: string[];
  snippets: string[];
}

export default function CodeSnippetPanel({ files, snippets }: CodeSnippetPanelProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (!snippets || snippets.length === 0) return null;

  return (
    <div className="mt-4 border border-border-default/40 rounded-xl overflow-hidden bg-bg-secondary/20">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2.5 flex items-center justify-between text-xs font-semibold text-text-secondary hover:text-text-primary hover:bg-bg-secondary/40 transition-colors cursor-pointer select-none"
      >
        <div className="flex items-center gap-2">
          <span>🔍</span>
          <span>
            {isOpen ? "Hide" : "View"} Code Context Source Snippets ({snippets.length})
          </span>
        </div>
        <span>{isOpen ? "▲" : "▼"}</span>
      </button>

      {isOpen && (
        <div className="border-t border-border-default/30 p-4 space-y-4 max-h-[300px] overflow-y-auto">
          {snippets.map((snippet, idx) => {
            const correspondingFile = files[idx] || "Context Segment";
            return (
              <div key={idx} className="space-y-1.5 text-left">
                <div className="text-[10px] font-mono text-text-secondary tracking-wide select-all bg-bg-secondary px-2 py-0.5 rounded w-fit">
                  {correspondingFile}
                </div>
                <pre className="text-xs p-3 font-mono text-text-primary bg-bg-primary rounded-lg border border-border-default/20 overflow-x-auto whitespace-pre select-text">
                  {snippet}
                </pre>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
