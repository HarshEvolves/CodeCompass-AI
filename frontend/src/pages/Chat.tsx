import { useEffect, useState, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import api from "@/lib/axios";
import LoadingSpinner from "@/components/LoadingSpinner";
import MessageBubble from "@/components/MessageBubble";
import ChatInput from "@/components/ChatInput";
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
}

interface ChatPayload {
  query: string;
  top_k?: number;
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
  const messageEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll to bottom
  const scrollToBottom = () => {
    messageEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load repository info
  useEffect(() => {
    const fetchRepo = async () => {
      try {
        const response = await api.get<Repository[]>("/repositories");
        const found = response.data.find((r) => r.id === repositoryId);
        if (!found) {
          setErrorMsg("Repository not found or access denied.");
        } else if (found.upload_status.toUpperCase() !== "INDEXED") {
          setErrorMsg("Repository is not indexed yet. Please go to dashboard and index it.");
          setRepo(found);
        } else {
          setRepo(found);
          // Initial greeting
          setMessages([
            {
              sender: "ai",
              text: `Hello! I have analyzed the repository "${found.name}". Ask me anything about the codebase.`,
            },
          ]);
        }
      } catch (err: any) {
        setErrorMsg("Failed to load workspace repositories.");
      } finally {
        setLoadingRepo(false);
      }
    };

    if (repositoryId) {
      fetchRepo();
    }
  }, [repositoryId]);

  // React Query Mutation for Chat API call
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
      const errMsg = err.response?.data?.detail || "Connection to LLM server failed.";
      setMessages((prev) => [
        ...prev,
        {
          sender: "ai",
          text: `⚠️ Error: ${errMsg}`,
        },
      ]);
    },
  });

  const handleSendMessage = (text: string) => {
    // 1. Add user message to display
    setMessages((prev) => [...prev, { sender: "user", text }]);

    // 2. Trigger API call
    chatMutation.mutate({ query: text, top_k: 5 });
  };

  if (loadingRepo) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <LoadingSpinner message="Retrieving code repository details..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-primary text-text-primary flex flex-col h-screen">
      {/* Header bar */}
      <header className="border-b border-border-default bg-bg-secondary/50 backdrop-blur-md z-10 shrink-0">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate("/dashboard")}
              className="px-3 py-1.5 border border-border-default hover:border-accent rounded-lg text-xs font-semibold transition-colors cursor-pointer select-none"
            >
              ← Back to Dashboard
            </button>
            <span className="text-border-default">|</span>
            <span className="text-xl">🧭</span>
            <h2 className="font-bold tracking-tight text-md">
              Chat: <span className="gradient-text font-bold">{repo?.name || "Codebase"}</span>
            </h2>
          </div>
        </div>
      </header>

      {/* Main chat viewport */}
      <div className="flex-1 overflow-y-auto max-w-5xl w-full mx-auto px-6 py-8 space-y-6 select-text flex flex-col justify-between">
        <div className="space-y-6 flex-1">
          {errorMsg ? (
            <div className="glass-card p-6 text-center max-w-md mx-auto my-12 border border-red-500/20 bg-red-500/5">
              <span className="text-4xl block mb-2">⚠️</span>
              <h4 className="font-bold text-red-400 mb-1">Access Restrained</h4>
              <p className="text-sm text-text-secondary mb-4">{errorMsg}</p>
              <button
                onClick={() => navigate("/dashboard")}
                className="px-4 py-2 bg-accent text-white font-semibold text-xs rounded-lg hover:bg-accent-hover cursor-pointer"
              >
                Go to Dashboard
              </button>
            </div>
          ) : (
            <>
              {messages.map((msg, idx) => (
                <MessageBubble key={idx} message={msg} />
              ))}
              {chatMutation.isPending && <TypingIndicator />}
              <div ref={messageEndRef} />
            </>
          )}
        </div>
      </div>

      {/* Input container */}
      {!errorMsg && (
        <div className="max-w-5xl w-full mx-auto shrink-0">
          <ChatInput
            onSendMessage={handleSendMessage}
            disabled={chatMutation.isPending}
          />
        </div>
      )}
    </div>
  );
}
