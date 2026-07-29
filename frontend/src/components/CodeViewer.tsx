import { useState } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import ExpandCollapseButton from "./ExpandCollapseButton";

interface CodeViewerProps {
  code: string;
  language: string;
  startLine?: number;
  highlightStart?: number;
  highlightEnd?: number;
  maxLinesBeforeCollapse?: number;
}

export default function CodeViewer({
  code,
  language,
  startLine = 1,
  highlightStart,
  highlightEnd,
  maxLinesBeforeCollapse = 15,
}: CodeViewerProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Compute number of lines in code content
  const totalLines = code.split("\n").length;
  const isCollapsible = totalLines > maxLinesBeforeCollapse;

  // Map backend language keys to Prism-supported aliases
  const getPrismLanguage = (lang: string) => {
    const l = lang.toLowerCase();
    if (l === "py") return "python";
    if (l === "js") return "javascript";
    if (l === "ts") return "typescript";
    if (l === "tsx") return "tsx";
    if (l === "cpp" || l === "c++") return "cpp";
    if (l === "java") return "java";
    return l;
  };

  const currentLanguage = getPrismLanguage(language);

  return (
    <div className="relative border border-border-default/40 rounded-xl overflow-hidden bg-bg-primary text-left">
      <div
        className={`transition-all duration-300 ${
          isCollapsible && !isExpanded ? "max-h-[280px] overflow-hidden" : ""
        }`}
      >
        <SyntaxHighlighter
          language={currentLanguage}
          style={vscDarkPlus}
          showLineNumbers={true}
          startingLineNumber={startLine}
          wrapLines={true}
          customStyle={{
            margin: 0,
            padding: "16px 8px 16px 0",
            backgroundColor: "transparent",
            fontSize: "12px",
            lineHeight: "1.6",
          }}
          lineProps={(lineNumber) => {
            const isHighlighted =
              highlightStart !== undefined &&
              highlightEnd !== undefined &&
              lineNumber >= highlightStart &&
              lineNumber <= highlightEnd;
            return isHighlighted
              ? ({
                  style: {
                    backgroundColor: "rgba(59, 130, 246, 0.12)",
                    display: "block",
                    width: "100%",
                    borderLeft: "3px solid #3b82f6",
                    paddingLeft: "4px",
                  },
                } as any)
              : {};
          }}
        >
          {code}
        </SyntaxHighlighter>

        {/* Collapsed fading overlay */}
        {isCollapsible && !isExpanded && (
          <div className="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-bg-primary to-transparent pointer-events-none" />
        )}
      </div>

      {/* Expand/Collapse footer controls */}
      {isCollapsible && (
        <div className="flex items-center justify-end px-4 py-2 border-t border-border-default/30 bg-bg-secondary/20">
          <ExpandCollapseButton
            isExpanded={isExpanded}
            onClick={() => setIsExpanded(!isExpanded)}
          />
        </div>
      )}
    </div>
  );
}
