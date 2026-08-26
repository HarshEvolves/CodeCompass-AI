import { useEffect, useState, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  Compass,
  ArrowLeft,
  Trash2,
  RefreshCw,
  Send,
  Code2,
  Database,
  FileCode,
  Sparkles,
} from "lucide-react";
import api from "@/lib/axios";
import MessageBubble from "@/components/MessageBubble";
import TypingIndicator from "@/components/TypingIndicator";

interface Message {
  sender: "user" | "ai";
  text: string;
  retrieved_files?: string[];
  retrieved_code_snippets?: string[];
  citations?: {
    file_path: string;
    start_line: number;
    end_line: number;
  }[];
}

interface Repository {
  id: string;
  name: string;
  upload_status: string;
  original_filename: string;
  created_at: string;
}

interface ChatPayload {
  query: string;
  top_k?: number;
  conversation_history?: { role: "user" | "assistant"; content: string }[];
}

interface ChatApiResponse {
  answer: string;
  retrieved_files: string[];
  retrieved_code_snippets: string[];
  citations: {
    file_path: string;
    start_line: number;
    end_line: number;
  }[];
}

export default function Chat() {
  const { repositoryId } = useParams<{ repositoryId: string }>();
  const navigate = useNavigate();
  const [repo, setRepo] = useState<Repository | null>(null);
  const [loadingRepo, setLoadingRepo] = useState(true);
  const [messages, setMessages] = useState<Message[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [inputText, setInputText] = useState("");
  const messageEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messageEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch repository details
  const fetchRepositoryDetails = async () => {
    try {
      setLoadingRepo(true);
      const response = await api.get<Repository[]>("/repositories");
      const found = response.data.find((r) => r.id === repositoryId);
      if (!found) {
        setErrorMsg("Repository not found or access denied.");
      } else if (found.upload_status.toUpperCase() !== "INDEXED") {
        setErrorMsg("Repository must be indexed before chatting.");
        setRepo(found);
      } else {
        setRepo(found);
        // Initial greeting
        setMessages([
          {
            sender: "ai",
            text: `Hello! I have fully indexed the codebase for **${found.name}**. Ask me any questions about the logic, structure, or implementation.`,
          },
        ]);
      }
    } catch (err: any) {
      setErrorMsg("Failed to retrieve repository details.");
    } finally {
      setLoadingRepo(false);
    }
  };

  useEffect(() => {
    if (repositoryId) {
      fetchRepositoryDetails();
    }
  }, [repositoryId]);

  // Chat request mutation
  const chatMutation = useMutation<ChatApiResponse, Error, ChatPayload>({
    mutationFn: async (payload) => {
      const response = await api.post<ChatApiResponse>(
        `/repositories/${repositoryId}/chat`,
        payload
      );
      return response.data;
    },
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        {
          sender: "ai",
          text: data.answer,
          retrieved_files: data.retrieved_files,
          retrieved_code_snippets: data.retrieved_code_snippets,
          citations: data.citations,
        },
      ]);
    },
    onError: (err: any) => {
      const errMsg = err.response?.data?.detail || "LLM request completion failed.";
      setMessages((prev) => [
        ...prev,
        {
          sender: "ai",
          text: `⚠️ Error: ${errMsg}`,
        },
      ]);
    },
  });

  // Builds the last 2 exchanges (4 messages) from current chat state to send
  // as conversation_history, so the backend can resolve references like "it"
  // or "that" — skips error bubbles, which aren't real completed exchanges.
  const buildConversationHistory = (): { role: "user" | "assistant"; content: string }[] => {
    return messages
      .filter((msg) => !msg.text.startsWith("⚠️ Error:"))
      .slice(-4)
      .map((msg) => ({
        role: msg.sender === "user" ? ("user" as const) : ("assistant" as const),
        content: msg.text,
      }));
  };

  const handleSendMessage = (textToSend: string) => {
    const trimmed = textToSend.trim();
    if (!trimmed || chatMutation.isPending) return;

    const conversation_history = buildConversationHistory();
    setMessages((prev) => [...prev, { sender: "user", text: trimmed }]);
    setInputText("");
    chatMutation.mutate({ query: trimmed, top_k: 5, conversation_history });
  };

  const handleResetChat = () => {
    if (repo) {
      setMessages([
        {
          sender: "ai",
          text: `Hello! I have fully indexed the codebase for **${repo.name}**. Ask me any questions about the logic, structure, or implementation.`,
        },
      ]);
    }
  };

  const handleDeleteMock = () => {
    alert("Repository deletion is not supported by the current backend API.");
  };

  // Get unique referenced files list in active session
  const getUniqueFilesReferenced = () => {
    const files = new Set<string>();
    messages.forEach((msg) => {
      msg.citations?.forEach((cit) => files.add(cit.file_path.split("/").pop() || cit.file_path));
    });
    return Array.from(files);
  };

  const referencedFiles = getUniqueFilesReferenced();
  const ext = repo?.original_filename.split(".").pop() || "";

  if (loadingRepo) {
    return (
      <div className="min-h-screen bg-bg-primary flex flex-col items-center justify-center gap-4">
        <div className="w-8 h-8 border-3 border-accent border-t-transparent rounded-full animate-spin" />
        <span className="text-xs font-semibold text-text-secondary">Loading code workspace...</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-primary text-text-primary flex font-sans h-screen overflow-hidden select-text">
      
      {/* LEFT SIDEBAR (Repository name, statistics, controls) */}
      <div className="hidden lg:flex flex-col w-[320px] bg-[#0C0C0E] border-r border-border-default shrink-0 justify-between select-none">
        <div className="p-6 space-y-8">
          {/* Header controls (Back button & Branding) */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate("/dashboard")}
              className="p-2.5 border border-border-default hover:bg-bg-hover hover:border-accent rounded-xl transition-all cursor-pointer"
              title="Back to Dashboard"
            >
              <ArrowLeft className="w-4 h-4 text-text-secondary" />
            </button>
            <div className="flex items-center gap-2">
              <Compass className="w-5.5 h-5.5 text-accent" />
              <span className="font-bold text-xs tracking-wider uppercase text-text-secondary">
                Workspace AI
              </span>
            </div>
          </div>

          {/* Active Repo Details */}
          {repo && (
            <div className="space-y-6 pt-6 border-t border-border-default/60">
              <div>
                <h4 className="text-sm font-bold text-text-primary truncate" title={repo.name}>
                  {repo.name}
                </h4>
                <p className="text-[10px] text-text-muted mt-1 truncate font-mono select-all">
                  ID: {repo.id}
                </p>
              </div>

              {/* Stats badges */}
              <div className="space-y-3 pt-4 border-t border-border-default/40 text-xs text-text-secondary">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-2 text-text-muted">
                    <Database className="w-4 h-4 shrink-0" /> Index Status:
                  </span>
                  <span className="px-2 py-0.5 rounded-full bg-success/15 border border-success/20 text-success text-[10px] font-bold">
                    Indexed
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-2 text-text-muted">
                    <Code2 className="w-4 h-4 shrink-0" /> Language:
                  </span>
                  <span className="px-2 py-0.5 rounded bg-bg-hover text-accent font-semibold text-[10px] uppercase">
                    {ext || "CODE"}
                  </span>
                </div>
              </div>

              {/* Unique referenced files sidebar */}
              {referencedFiles.length > 0 && (
                <div className="space-y-2 pt-6 border-t border-border-default/40 select-text">
                  <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider block">
                    Session Citations ({referencedFiles.length})
                  </span>
                  <div className="max-h-[220px] overflow-y-auto space-y-2 scrollbar-thin">
                    {referencedFiles.map((file, idx) => (
                      <div
                        key={idx}
                        className="flex items-center gap-2 px-3 py-2 bg-bg-primary border border-border-default/60 rounded-xl text-[11px] font-mono text-text-primary"
                      >
                        <FileCode className="w-4 h-4 text-accent shrink-0" />
                        <span className="truncate">{file}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Sidebar Controls Footer */}
        <div className="p-6 border-t border-border-default/60 space-y-3">
          <button
            onClick={handleResetChat}
            className="w-full h-11 px-4 rounded-xl text-xs font-semibold border border-border-default/70 hover:border-accent hover:bg-bg-hover text-text-secondary flex items-center justify-center gap-2 transition-all cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Reset Thread</span>
          </button>
          <button
            onClick={handleDeleteMock}
            className="w-full h-11 px-4 rounded-xl text-xs font-semibold border border-border-default/70 hover:border-error hover:bg-error/5 hover:text-error text-text-secondary flex items-center justify-center gap-2 transition-all cursor-pointer"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Delete Index</span>
          </button>
        </div>
      </div>

      {/* RIGHT CHAT WINDOW (Centered conversation, Sticky bottom input) */}
      <div className="flex-1 flex flex-col h-full bg-bg-primary overflow-hidden relative">
        {/* Mobile Header bar */}
        <header className="lg:hidden shrink-0 border-b border-border-default bg-[#09090B]/60 backdrop-blur-md z-10 py-4 px-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate("/dashboard")}
              className="p-2 border border-border-default rounded-xl hover:border-accent"
            >
              <ArrowLeft className="w-4 h-4 text-text-secondary" />
            </button>
            <span className="font-bold text-sm text-text-primary truncate max-w-[150px]">
              {repo?.name}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleResetChat}
              className="p-2 border border-border-default rounded-xl"
              title="Reset Chat"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        </header>

        {/* Messages list (centered max-w-3xl ~ 800px, 24px vertical spacing between messages) */}
        <div className="flex-1 overflow-y-auto px-6 py-8 md:px-8">
          <div className="max-w-3xl w-full mx-auto space-y-6 flex flex-col justify-start">
            <AnimatePresence initial={false}>
              {errorMsg ? (
                <div className="saas-card p-8 text-center max-w-md mx-auto my-12 border border-error/20 bg-error/5 select-none">
                  <span className="text-4xl block mb-2">⚠️</span>
                  <h4 className="font-bold text-error mb-1">Access Restrained</h4>
                  <p className="text-sm text-text-secondary mb-4">{errorMsg}</p>
                  <button
                    onClick={() => navigate("/dashboard")}
                    className="px-4 py-2 bg-accent text-white font-semibold text-xs rounded-xl hover:bg-accent-hover cursor-pointer"
                  >
                    Go to Dashboard
                  </button>
                </div>
              ) : (
                <>
                  {messages.map((msg, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.25 }}
                    >
                      <MessageBubble message={msg} />
                    </motion.div>
                  ))}
                  {chatMutation.isPending && <TypingIndicator />}
                  <div ref={messageEndRef} />
                </>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Suggestion Chips & Sticky Bottom Input Area */}
        {!errorMsg && (
          <div className="w-full border-t border-border-default/60 bg-[#09090B]/60 backdrop-blur-md shrink-0 select-none py-6">
            <div className="max-w-3xl w-full mx-auto px-6 md:px-8 space-y-4">
              {/* Suggestion Chips */}
              {messages.length === 1 && (
                <div className="flex flex-wrap gap-2.5 justify-start">
                  {[
                    "Explain the core classes",
                    "How are API routes registered?",
                    "Where is database connection defined?",
                  ].map((chip, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSendMessage(chip)}
                      className="px-3.5 py-2.5 bg-bg-card hover:bg-bg-hover text-text-secondary hover:text-text-primary text-[11px] font-semibold rounded-xl border border-border-default transition-all cursor-pointer flex items-center gap-2"
                    >
                      <Sparkles className="w-3.5 h-3.5 text-accent" />
                      <span>{chip}</span>
                    </button>
                  ))}
                </div>
              )}

              {/* Text Input area (Min height 44px for send button, rounded 16px) */}
              <div className="flex gap-2.5 items-end bg-bg-card border border-border-default rounded-2xl p-2.5 focus-within:border-accent focus-within:ring-3 focus-within:ring-accent-glow transition-all">
                <textarea
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage(inputText);
                    }
                  }}
                  placeholder="Ask a question about the codebase (Press Enter)..."
                  disabled={chatMutation.isPending}
                  rows={1}
                  className="flex-1 bg-transparent text-text-primary placeholder:text-text-muted text-sm px-4 py-3 focus:outline-none resize-none max-h-32 min-h-[44px] scrollbar-none"
                />
                <button
                  onClick={() => handleSendMessage(inputText)}
                  disabled={chatMutation.isPending || !inputText.trim()}
                  className="w-11 h-11 shrink-0 bg-accent text-white hover:bg-accent-hover disabled:bg-bg-secondary disabled:text-text-muted disabled:cursor-not-allowed rounded-xl transition-all flex items-center justify-center cursor-pointer hover:shadow-lg hover:shadow-accent/15"
                >
                  <Send className="w-4.5 h-4.5" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
