import { useState, useRef } from "react";
import type { DragEvent, ChangeEvent } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { UploadCloud, CheckCircle2, AlertCircle } from "lucide-react";
import api from "@/lib/axios";

interface UploadZoneProps {
  onUploadSuccess: () => void;
}

export default function UploadZone({ onUploadSuccess }: UploadZoneProps) {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [fileSize, setFileSize] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const handleDrag = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const processFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".zip")) {
      setError("Only ZIP archives are allowed.");
      setSuccess(null);
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      setError("File exceeds maximum allowed upload size of 50MB.");
      setSuccess(null);
      return;
    }

    setUploading(true);
    setProgress(0);
    setError(null);
    setSuccess(null);
    setFileName(file.name);
    setFileSize(formatBytes(file.size));

    const formData = new FormData();
    formData.append("file", file);

    try {
      await api.post("/repositories/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / (progressEvent.total || file.size)
          );
          setProgress(percentCompleted);
        },
      });

      setSuccess(`Successfully uploaded ${file.name}`);
      onUploadSuccess();
    } catch (err: any) {
      const errMsg = err.response?.data?.detail || "Upload failed. Please try again.";
      setError(errMsg);
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  const handleDrop = async (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await processFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = async (e: ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      await processFile(e.target.files[0]);
    }
  };

  const onButtonClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="w-full font-sans select-none">
      <motion.div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={onButtonClick}
        whileHover={{ scale: uploading ? 1 : 1.015 }}
        whileTap={{ scale: uploading ? 1 : 0.995 }}
        className={`w-full py-10 px-5 border border-dashed rounded-2xl flex flex-col justify-center items-center gap-3 transition-all duration-200 cursor-pointer ${
          dragActive
            ? "border-accent bg-accent/5 ring-3 ring-accent-glow"
            : "border-border-default hover:border-accent hover:bg-bg-hover/30"
        } ${uploading ? "pointer-events-none opacity-80" : ""}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".zip"
          onChange={handleChange}
          className="hidden"
          disabled={uploading}
        />

        <div className={`p-4 rounded-full ${dragActive ? "bg-accent/20" : "bg-bg-hover"} transition-colors`}>
          <UploadCloud className={`w-8 h-8 ${dragActive ? "text-accent" : "text-text-secondary"}`} />
        </div>

        <div className="space-y-1 text-center">
          <h4 className="font-semibold text-sm text-text-primary">
            {uploading ? "Uploading Repository..." : "Drag and drop your ZIP file here"}
          </h4>
          <p className="text-xs text-text-secondary">
            {uploading
              ? `${fileName} (${fileSize})`
              : "Or click to select a file from your computer (Max 50MB)"}
          </p>
        </div>

        {uploading && (
          <div className="w-full max-w-xs mt-2 space-y-1.5 text-center">
            <div className="w-full bg-bg-primary rounded-full h-1.5 overflow-hidden border border-border-default/40">
              <motion.div
                className="bg-accent h-1.5 rounded-full"
                initial={{ width: "0%" }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.1 }}
              />
            </div>
            <span className="text-[10px] font-semibold text-text-secondary">
              {progress}% Uploaded
            </span>
          </div>
        )}
      </motion.div>

      {/* Notifications list */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mt-4 p-4 flex items-start gap-3 bg-error/10 border border-error/20 rounded-2xl text-xs text-error font-medium leading-relaxed"
          >
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </motion.div>
        )}

        {success && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mt-4 p-4 flex items-start gap-3 bg-success/10 border border-success/20 rounded-2xl text-xs text-success font-medium leading-relaxed"
          >
            <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{success}</span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
