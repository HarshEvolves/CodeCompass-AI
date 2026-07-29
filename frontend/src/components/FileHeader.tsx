import { Link } from "react-router-dom";
import CopyButton from "./CopyButton";

interface FileHeaderProps {
  repositoryId: string;
  filePath: string;
  language: string;
  startLine?: number;
  endLine?: number;
  codeContent: string;
}

export default function FileHeader({
  repositoryId,
  filePath,
  language,
  startLine,
  endLine,
  codeContent,
}: FileHeaderProps) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 bg-bg-secondary border-b border-border-default/60">
      {/* Left panel - meta info */}
      <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
        <span className="bg-bg-primary px-2.5 py-1 rounded text-accent font-semibold tracking-wide select-all">
          {language}
        </span>
        <span className="text-text-primary font-medium select-all truncate max-w-[280px] sm:max-w-md" title={filePath}>
          {filePath}
        </span>
        {startLine !== undefined && endLine !== undefined && (
          <span className="text-text-muted select-none">
            ({startLine === endLine ? `Line ${startLine}` : `Lines ${startLine} - ${endLine}`})
          </span>
        )}
      </div>

      {/* Right panel - actions */}
      <div className="flex items-center gap-2 select-none">
        <CopyButton content={codeContent} />
        <Link
          to={`/repository/${repositoryId}/file?path=${encodeURIComponent(filePath)}${
            startLine ? `&start=${startLine}` : ""
          }${endLine ? `&end=${endLine}` : ""}`}
          className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-accent/15 text-accent border border-accent/20 hover:bg-accent/25 transition-all flex items-center gap-1 cursor-pointer"
        >
          <span>📄</span>
          <span>View Full File</span>
        </Link>
      </div>
    </div>
  );
}
