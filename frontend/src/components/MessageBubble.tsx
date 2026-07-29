import CitationCard from "./CitationCard";
import CodeSnippetPanel from "./CodeSnippetPanel";

interface Citation {
  file_path: string;
  start_line: number;
  end_line: number;
}

interface Message {
  sender: "user" | "ai";
  text: string;
  retrieved_files?: string[];
  retrieved_code_snippets?: string[];
  citations?: Citation[];
}

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.sender === "user";

  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl p-4.5 text-left border ${
          isUser
            ? "bg-accent/10 border-accent/20 text-text-primary rounded-tr-none"
            : "bg-bg-secondary/45 border-border-default/50 text-text-primary rounded-tl-none"
        }`}
      >
        <span className="text-[10px] font-bold text-text-secondary uppercase tracking-wider block mb-1">
          {isUser ? "You" : "AI Assistant"}
        </span>

        {/* Text body */}
        <div className="space-y-1.5 select-text">
          {renderMarkdown(message.text)}
        </div>

        {/* Citations section */}
        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="mt-4 pt-3 border-t border-border-default/20">
            <span className="text-[10px] font-bold text-text-secondary uppercase tracking-wider block mb-2">
              Sources Referenced ({message.citations.length})
            </span>
            <div className="flex flex-wrap gap-2">
              {message.citations.map((cit, idx) => (
                <CitationCard
                  key={idx}
                  filePath={cit.file_path}
                  startLine={cit.start_line}
                  endLine={cit.end_line}
                />
              ))}
            </div>
          </div>
        )}

        {/* Collapsible raw snippets panel */}
        {!isUser &&
          message.retrieved_files &&
          message.retrieved_code_snippets &&
          message.retrieved_code_snippets.length > 0 && (
            <CodeSnippetPanel
              files={message.retrieved_files}
              snippets={message.retrieved_code_snippets}
              citations={message.citations}
            />
          )}
      </div>
    </div>
  );
}

function renderInlineInside(text: string): React.ReactNode {
  const parts = text.split(/(`.*?`)/g);
  return (
    <>
      {parts.map((part, index) => {
        if (part.startsWith("`") && part.endsWith("`")) {
          return (
            <code
              key={index}
              className="bg-bg-primary border border-border-default/45 px-1.5 py-0.5 rounded text-accent font-mono text-xs"
            >
              {part.slice(1, -1)}
            </code>
          );
        }
        return part;
      })}
    </>
  );
}

function renderInline(text: string): React.ReactNode {
  const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);
  return (
    <>
      {parts.map((part, index) => {
        if (part.startsWith("**") && part.endsWith("**")) {
          return (
            <strong key={index} className="font-bold text-text-primary">
              {renderInlineInside(part.slice(2, -2))}
            </strong>
          );
        }
        if (part.startsWith("`") && part.endsWith("`")) {
          return (
            <code
              key={index}
              className="bg-bg-primary border border-border-default/45 px-1.5 py-0.5 rounded text-accent font-mono text-xs"
            >
              {part.slice(1, -1)}
            </code>
          );
        }
        return part;
      })}
    </>
  );
}

function renderMarkdown(text: string) {
  const lines = text.split("\n");
  return lines.map((line, idx) => {
    // 1. Headers
    if (line.startsWith("### ")) {
      return (
        <h3 key={idx} className="text-sm font-bold mt-4 mb-2 text-text-primary">
          {renderInline(line.slice(4))}
        </h3>
      );
    }
    if (line.startsWith("## ")) {
      return (
        <h2 key={idx} className="text-base font-bold mt-4 mb-2 text-text-primary">
          {renderInline(line.slice(3))}
        </h2>
      );
    }
    if (line.startsWith("# ")) {
      return (
        <h1 key={idx} className="text-lg font-bold mt-5 mb-2.5 text-text-primary">
          {renderInline(line.slice(2))}
        </h1>
      );
    }

    // 2. Lists
    if (line.startsWith("* ") || line.startsWith("- ")) {
      return (
        <li key={idx} className="ml-4 list-disc text-sm text-text-primary leading-relaxed mt-1">
          {renderInline(line.slice(2))}
        </li>
      );
    }

    // 3. Empty Line
    if (line.trim() === "") {
      return <div key={idx} className="h-2" />;
    }

    // 4. Normal text
    return (
      <p key={idx} className="text-sm text-text-primary leading-relaxed">
        {renderInline(line)}
      </p>
    );
  });
}

