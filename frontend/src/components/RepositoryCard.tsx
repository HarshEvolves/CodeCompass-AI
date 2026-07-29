import { useState } from "react";
import { useNavigate } from "react-router-dom";
import StatusBadge from "./StatusBadge";
import api from "@/lib/axios";

interface Repository {
  id: string;
  name: string;
  original_filename: string;
  upload_status: string;
  created_at: string;
}

interface RepositoryCardProps {
  repo: Repository;
  onActionSuccess: () => void;
}

export default function RepositoryCard({ repo, onActionSuccess }: RepositoryCardProps) {
  const navigate = useNavigate();
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const status = repo.upload_status.toUpperCase();

  const handleAction = async (action: "extract" | "parse" | "chunk" | "index") => {
    setLoadingAction(action);
    setError(null);

    try {
      await api.post(`/repositories/${repo.id}/${action}`);
      onActionSuccess();
    } catch (err: any) {
      const errMsg = err.response?.data?.detail || `Failed to ${action} repository.`;
      setError(errMsg);
    } finally {
      setLoadingAction(null);
    }
  };

  // Step-by-step logic
  const isUploaded = status === "UPLOADED";
  const isExtracted = status === "EXTRACTED";
  const isParsed = status === "PARSED";
  const isChunked = status === "CHUNKED";
  const isIndexed = status === "INDEXED";

  return (
    <div className="glass-card p-6 flex flex-col justify-between text-left relative overflow-hidden transition-all duration-200 border border-border-default/60 hover:border-accent/40">
      <div>
        <div className="flex justify-between items-start mb-2 gap-4">
          <h3 className="font-bold text-lg text-text-primary truncate" title={repo.name}>
            {repo.name}
          </h3>
          <StatusBadge status={repo.upload_status} />
        </div>
        
        <div className="space-y-1.5 mb-6 text-sm text-text-secondary">
          <div className="flex justify-between">
            <span>File:</span>
            <span className="font-mono text-xs truncate max-w-[200px]" title={repo.original_filename}>
              {repo.original_filename}
            </span>
          </div>
          <div className="flex justify-between">
            <span>Uploaded:</span>
            <span>{new Date(repo.created_at).toLocaleDateString()}</span>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        {/* Pipeline Progress Indicator */}
        <div className="flex items-center justify-between gap-1 text-[10px] text-text-secondary mb-1">
          <span className={isUploaded || isExtracted || isParsed || isChunked || isIndexed ? "text-accent font-semibold" : ""}>Uploaded</span>
          <span className="text-border-default">➔</span>
          <span className={isExtracted || isParsed || isChunked || isIndexed ? "text-accent font-semibold" : ""}>Extracted</span>
          <span className="text-border-default">➔</span>
          <span className={isParsed || isChunked || isIndexed ? "text-accent font-semibold" : ""}>Parsed</span>
          <span className="text-border-default">➔</span>
          <span className={isChunked || isIndexed ? "text-accent font-semibold" : ""}>Chunked</span>
          <span className="text-border-default">➔</span>
          <span className={isIndexed ? "text-emerald-400 font-semibold" : ""}>Indexed</span>
        </div>

        {/* Action Buttons */}
        <div className="grid grid-cols-2 gap-2.5">
          <button
            onClick={() => handleAction("extract")}
            disabled={!isUploaded || !!loadingAction}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-1 transition-all ${
              isUploaded
                ? "bg-accent text-white hover:bg-accent-hover cursor-pointer"
                : isExtracted || isParsed || isChunked || isIndexed
                ? "bg-bg-secondary text-text-secondary opacity-60 cursor-not-allowed border border-border-default"
                : "bg-bg-primary text-text-muted opacity-40 cursor-not-allowed"
            }`}
          >
            {loadingAction === "extract" && (
              <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            )}
            Extract
          </button>

          <button
            onClick={() => handleAction("parse")}
            disabled={!isExtracted || !!loadingAction}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-1 transition-all ${
              isExtracted
                ? "bg-accent text-white hover:bg-accent-hover cursor-pointer"
                : isParsed || isChunked || isIndexed
                ? "bg-bg-secondary text-text-secondary opacity-60 cursor-not-allowed border border-border-default"
                : "bg-bg-primary text-text-muted opacity-40 cursor-not-allowed"
            }`}
          >
            {loadingAction === "parse" && (
              <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            )}
            Parse
          </button>

          <button
            onClick={() => handleAction("chunk")}
            disabled={!isParsed || !!loadingAction}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-1 transition-all ${
              isParsed
                ? "bg-accent text-white hover:bg-accent-hover cursor-pointer"
                : isChunked || isIndexed
                ? "bg-bg-secondary text-text-secondary opacity-60 cursor-not-allowed border border-border-default"
                : "bg-bg-primary text-text-muted opacity-40 cursor-not-allowed"
            }`}
          >
            {loadingAction === "chunk" && (
              <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            )}
            Chunk
          </button>

          {isIndexed ? (
            <button
              onClick={() => navigate(`/repository/${repo.id}/chat`)}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500 hover:bg-emerald-600 text-white cursor-pointer flex items-center justify-center gap-1 transition-all"
            >
              Chat 💬
            </button>
          ) : (
            <button
              onClick={() => handleAction("index")}
              disabled={!isChunked || !!loadingAction}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-1 transition-all ${
                isChunked
                  ? "bg-accent text-white hover:bg-accent-hover cursor-pointer"
                  : "bg-bg-primary text-text-muted opacity-40 cursor-not-allowed"
              }`}
            >
              {loadingAction === "index" && (
                <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              )}
              Index
            </button>
          )}
        </div>

        {error && (
          <div className="mt-2 text-xs text-red-400 bg-red-500/5 p-2 rounded border border-red-500/10">
            ⚠️ {error}
          </div>
        )}
      </div>
    </div>
  );
}
