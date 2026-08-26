import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
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
          <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
            {message.text}
          </ReactMarkdown>
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

const markdownComponents = {
  h1: ({ children }: any) => (
    <h1 className="text-lg font-bold mt-5 mb-2.5 text-text-primary">{children}</h1>
  ),
  h2: ({ children }: any) => (
    <h2 className="text-base font-bold mt-4 mb-2 text-text-primary">{children}</h2>
  ),
  h3: ({ children }: any) => (
    <h3 className="text-sm font-bold mt-4 mb-2 text-text-primary">{children}</h3>
  ),
  p: ({ children }: any) => (
    <p className="text-sm text-text-primary leading-relaxed">{children}</p>
  ),
  strong: ({ children }: any) => (
    <strong className="font-bold text-text-primary">{children}</strong>
  ),
  ul: ({ children }: any) => (
    <ul className="list-disc ml-4 text-sm text-text-primary leading-relaxed mt-1 space-y-1">
      {children}
    </ul>
  ),
  ol: ({ children }: any) => (
    <ol className="list-decimal ml-4 text-sm text-text-primary leading-relaxed mt-1 space-y-1">
      {children}
    </ol>
  ),
  li: ({ children }: any) => <li>{children}</li>,
  pre: ({ children }: any) => <>{children}</>,
  code({ className, children, ...props }: any) {
    const match = /language-(\w+)/.exec(className || "");
    if (match) {
      return (
        <SyntaxHighlighter
          language={match[1]}
          style={vscDarkPlus}
          customStyle={{
            margin: "8px 0",
            borderRadius: "8px",
            fontSize: "12px",
            lineHeight: "1.6",
          }}
        >
          {String(children).replace(/\n$/, "")}
        </SyntaxHighlighter>
      );
    }
    return (
      <code
        className="bg-bg-primary border border-border-default/45 px-1.5 py-0.5 rounded text-accent font-mono text-xs"
        {...props}
      >
        {children}
      </code>
    );
  },
};

