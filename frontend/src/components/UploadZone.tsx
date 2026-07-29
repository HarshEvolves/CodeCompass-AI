import { useState, useRef } from "react";
import type { DragEvent, ChangeEvent } from "react";
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
  const fileInputRef = useRef<HTMLInputElement>(null);

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
    <div className="w-full">
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={onButtonClick}
        className={`w-full py-12 px-6 border-2 border-dashed rounded-xl flex flex-col justify-center items-center gap-3 transition-all duration-200 cursor-pointer ${
          dragActive
            ? "border-accent bg-accent/5"
            : "border-border-default/80 hover:border-accent hover:bg-bg-secondary/40"
        } ${uploading ? "pointer-events-none opacity-70" : ""}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".zip"
          onChange={handleChange}
          className="hidden"
          disabled={uploading}
        />
        
        <span className="text-4xl">📁</span>
        <h4 className="font-semibold text-text-primary">
          {uploading ? "Uploading Repository..." : "Drag and drop your ZIP file here"}
        </h4>
        <p className="text-xs text-text-secondary">
          {uploading ? "Please wait while files transfer." : "Or click to select a file from your computer (Max 50MB)"}
        </p>

        {uploading && (
          <div className="w-full max-w-md bg-bg-primary rounded-full h-2.5 mt-3 overflow-hidden border border-border-default/50">
            <div
              className="bg-accent h-2.5 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${progress}%` }}
            />
            <span className="text-xs text-text-secondary mt-1 block text-center">
              {progress}% Uploaded
            </span>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 p-3 bg-red-500/10 border border-red-500/25 rounded-lg text-sm text-red-400">
          ⚠️ {error}
        </div>
      )}

      {success && (
        <div className="mt-4 p-3 bg-emerald-500/10 border border-emerald-500/25 rounded-lg text-sm text-emerald-400">
          ✅ {success}
        </div>
      )}
    </div>
  );
}
