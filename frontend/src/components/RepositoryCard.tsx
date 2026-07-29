import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Code2,
  Calendar,
  CheckCircle2,
  Trash2,
  MessageSquareCode,
  FileArchive,
  ArrowRight,
  RefreshCw,
} from "lucide-react";
import api from "@/lib/axios";
import StatusBadge from "./StatusBadge";

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

  const handleDeleteMock = () => {
    alert("Repository deletion is not supported by the current backend API.");
  };

  // Pipeline step matching logic
  const isUploaded = status === "UPLOADED";
  const isExtracted = status === "EXTRACTED";
  const isParsed = status === "PARSED";
  const isChunked = status === "CHUNKED";
  const isIndexed = status === "INDEXED";

  // Determine stage mapping index (0 to 4)
  const getStageIndex = () => {
    if (isIndexed) return 4;
    if (isChunked) return 3;
    if (isParsed) return 2;
    if (isExtracted) return 1;
    return 0;
  };

  const currentStage = getStageIndex();

  const steps = [
    { label: "Upload", val: 0 },
    { label: "Extract", val: 1 },
    { label: "Parse", val: 2 },
    { label: "Chunk", val: 3 },
    { label: "Index", val: 4 },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      transition={{ duration: 0.25 }}
      className="saas-card p-8 flex flex-col justify-between bg-bg-card border border-border-default hover:border-accent/40 rounded-2xl relative select-none font-sans min-h-[360px]"
    >
      <div className="space-y-6">
        {/* Header - name and status badge (24px gap below header) */}
        <div className="flex justify-between items-start gap-4">
          <div className="flex items-center gap-3 truncate">
            <div className="p-2.5 rounded-xl bg-accent/10 text-accent shrink-0 border border-accent/15">
              <FileArchive className="w-5 h-5" />
            </div>
            <h3
              className="font-bold text-base text-text-primary truncate select-text cursor-help"
              title={repo.name}
            >
              {repo.name}
            </h3>
          </div>
          <StatusBadge status={repo.upload_status} />
        </div>

        {/* Metadata info grid */}
        <div className="grid grid-cols-2 gap-4 bg-bg-secondary/40 border border-border-default/50 p-4 rounded-xl text-xs text-text-secondary select-text">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-text-muted shrink-0" />
            <span>{new Date(repo.created_at).toLocaleDateString()}</span>
          </div>
          <div className="flex items-center gap-2 truncate">
            <Code2 className="w-4 h-4 text-text-muted shrink-0" />
            <span className="truncate">{repo.original_filename}</span>
          </div>
        </div>

        {/* Linear Stepper progress pipeline (Generous breathing room) */}
        <div className="space-y-3 select-none pt-2">
          <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider block">
            Pipeline Progress
          </span>
          <div className="flex items-center justify-between relative py-3">
            {/* Background progress track line */}
            <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-border-default/60 -translate-y-1/2 z-0" />
            {/* Active progress fill line */}
            <div
              className="absolute top-1/2 left-0 h-0.5 bg-accent -translate-y-1/2 z-0 transition-all duration-500 ease-out"
              style={{ width: `${(currentStage / 4) * 100}%` }}
            />

            {steps.map((step, idx) => {
              const completed = currentStage > step.val;
              const active = currentStage === step.val;
              return (
                <div key={idx} className="flex flex-col items-center gap-2 relative z-10">
                  <div
                    className={`w-6.5 h-6.5 rounded-full flex items-center justify-center text-[10px] font-bold transition-all duration-300 ${
                      completed
                        ? "bg-success text-white"
                        : active
                        ? "bg-accent text-white ring-4 ring-accent-glow animate-pulse"
                        : "bg-bg-card border border-border-default text-text-muted"
                    }`}
                  >
                    {completed ? <CheckCircle2 className="w-3.5 h-3.5" /> : step.val + 1}
                  </div>
                  <span
                    className={`text-[9px] font-bold tracking-tight uppercase ${
                      active ? "text-accent font-extrabold" : completed ? "text-text-primary" : "text-text-muted"
                    }`}
                  >
                    {step.label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Button controls grid - Minimum height 44px, clean gaps */}
      <div className="space-y-4 pt-6 mt-auto">
        <div className="grid grid-cols-2 gap-3">
          {/* Extract Button */}
          <button
            onClick={() => handleAction("extract")}
            disabled={!isUploaded || !!loadingAction}
            className={`h-11 px-4 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-all select-none border ${
              isUploaded
                ? "bg-accent/10 text-accent border-accent/20 hover:bg-accent/20 hover:border-accent/30 cursor-pointer"
                : isExtracted || isParsed || isChunked || isIndexed
                ? "bg-bg-hover/20 text-text-muted border-border-default/60 opacity-60 cursor-not-allowed"
                : "bg-bg-secondary/40 text-text-muted border-border-default/20 opacity-40 cursor-not-allowed"
            }`}
          >
            {loadingAction === "extract" && (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            )}
            <span>Extract</span>
          </button>

          {/* Parse Button */}
          <button
            onClick={() => handleAction("parse")}
            disabled={!isExtracted || !!loadingAction}
            className={`h-11 px-4 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-all select-none border ${
              isExtracted
                ? "bg-accent/10 text-accent border-accent/20 hover:bg-accent/20 hover:border-accent/30 cursor-pointer"
                : isParsed || isChunked || isIndexed
                ? "bg-bg-hover/20 text-text-muted border-border-default/60 opacity-60 cursor-not-allowed"
                : "bg-bg-secondary/40 text-text-muted border-border-default/20 opacity-40 cursor-not-allowed"
            }`}
          >
            {loadingAction === "parse" && (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            )}
            <span>Parse</span>
          </button>

          {/* Chunk Button */}
          <button
            onClick={() => handleAction("chunk")}
            disabled={!isParsed || !!loadingAction}
            className={`h-11 px-4 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-all select-none border ${
              isParsed
                ? "bg-accent/10 text-accent border-accent/20 hover:bg-accent/20 hover:border-accent/30 cursor-pointer"
                : isChunked || isIndexed
                ? "bg-bg-hover/20 text-text-muted border-border-default/60 opacity-60 cursor-not-allowed"
                : "bg-bg-secondary/40 text-text-muted border-border-default/20 opacity-40 cursor-not-allowed"
            }`}
          >
            {loadingAction === "chunk" && (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            )}
            <span>Chunk</span>
          </button>

          {/* Index Button */}
          <button
            onClick={() => handleAction("index")}
            disabled={!isChunked || !!loadingAction}
            className={`h-11 px-4 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-all select-none border ${
              isChunked
                ? "bg-accent/10 text-accent border-accent/20 hover:bg-accent/20 hover:border-accent/30 cursor-pointer"
                : isIndexed
                ? "bg-success/10 text-success border-success/20 opacity-80 cursor-not-allowed"
                : "bg-bg-secondary/40 text-text-muted border-border-default/20 opacity-40 cursor-not-allowed"
            }`}
          >
            {loadingAction === "index" && (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            )}
            <span>Index</span>
          </button>
        </div>

        {/* Primary Row - Open Chat / Delete */}
        <div className="grid grid-cols-12 gap-3 pt-2 border-t border-border-default/40">
          <button
            onClick={handleDeleteMock}
            className="col-span-3 h-11 border border-border-default/70 hover:border-error hover:text-error hover:bg-error/5 text-text-secondary rounded-xl flex items-center justify-center transition-all cursor-pointer"
            title="Delete Repository Workspace"
          >
            <Trash2 className="w-4 h-4" />
          </button>

          <button
            disabled={!isIndexed}
            onClick={() => navigate(`/repository/${repo.id}/chat`)}
            className={`col-span-9 h-11 px-4 rounded-xl text-xs font-bold flex items-center justify-center gap-2.5 transition-all select-none border ${
              isIndexed
                ? "bg-accent text-white border-accent-secondary hover:bg-accent-hover hover:shadow-lg hover:shadow-accent/15 cursor-pointer"
                : "bg-bg-secondary/50 text-text-muted border-border-default/30 cursor-not-allowed opacity-50"
            }`}
          >
            <MessageSquareCode className="w-4 h-4 shrink-0" />
            <span>Open Chat</span>
            <ArrowRight className="w-3.5 h-3.5 shrink-0" />
          </button>
        </div>

        {error && (
          <div className="text-[10px] text-error bg-error/5 border border-error/15 p-3 rounded-xl flex items-start gap-2 leading-relaxed">
            <span className="shrink-0">⚠️</span>
            <span>{error}</span>
          </div>
        )}
      </div>
    </motion.div>
  );
}
