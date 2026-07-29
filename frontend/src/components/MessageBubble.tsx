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
        <p className="text-sm leading-relaxed whitespace-pre-wrap select-text">
          {message.text}
        </p>

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
