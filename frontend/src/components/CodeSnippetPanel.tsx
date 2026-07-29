import { useState } from "react";
import { useParams } from "react-router-dom";
import FileHeader from "./FileHeader";
import CodeViewer from "./CodeViewer";

interface Citation {
  file_path: string;
  start_line: number;
  end_line: number;
}

interface CodeSnippetPanelProps {
  files: string[];
  snippets: string[];
  citations?: Citation[];
}

export default function CodeSnippetPanel({ files, snippets, citations }: CodeSnippetPanelProps) {
  const { repositoryId } = useParams<{ repositoryId: string }>();
  const [isOpen, setIsOpen] = useState(false);

  if (!snippets || snippets.length === 0 || !repositoryId) return null;

  return (
    <div className="mt-4 border border-border-default/40 rounded-xl overflow-hidden bg-bg-secondary/20 select-none">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2.5 flex items-center justify-between text-xs font-semibold text-text-secondary hover:text-text-primary hover:bg-bg-secondary/40 transition-colors cursor-pointer"
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
        <div className="border-t border-border-default/30 p-4 space-y-6 max-h-[450px] overflow-y-auto bg-bg-primary/20">
          {snippets.map((snippet, idx) => {
            const correspondingFile = files[idx] || "Context Segment";
            const citation = citations?.[idx];
            const startLine = citation?.start_line ?? 1;
            const endLine = citation?.end_line ?? startLine;

            // Guess language from extension
            const ext = correspondingFile.split(".").pop() || "";

            return (
              <div key={idx} className="space-y-2 select-text">
                <FileHeader
                  repositoryId={repositoryId}
                  filePath={correspondingFile}
                  language={ext.toUpperCase() || "CODE"}
                  startLine={citation?.start_line}
                  endLine={citation?.end_line}
                  codeContent={snippet}
                />
                <CodeViewer
                  code={snippet}
                  language={ext}
                  startLine={startLine}
                  highlightStart={startLine}
                  highlightEnd={endLine}
                />
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
