import { useEffect, useState } from "react";
import { useParams, useSearchParams, useNavigate } from "react-router-dom";
import api from "@/lib/axios";
import LoadingSpinner from "@/components/LoadingSpinner";
import CodeViewer from "@/components/CodeViewer";
import CopyButton from "@/components/CopyButton";

interface FileContentResponse {
  content: string;
  relative_path: string;
}

export default function ViewFullFile() {
  const { repositoryId } = useParams<{ repositoryId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const filePath = searchParams.get("path") || "";
  const startLine = parseInt(searchParams.get("start") || "0");
  const endLine = parseInt(searchParams.get("end") || "0");

  const [content, setContent] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const fetchFileContent = async () => {
      if (!repositoryId || !filePath) {
        setErrorMsg("Missing repository or file parameters.");
        setLoading(false);
        return;
      }
      try {
        setLoading(true);
        setErrorMsg(null);
        const response = await api.get<FileContentResponse>(
          `/repositories/${repositoryId}/file`,
          { params: { file_path: filePath } }
        );
        setContent(response.data.content);
      } catch (err: any) {
        const msg = err.response?.data?.detail || "Could not retrieve the requested file content.";
        setErrorMsg(msg);
      } finally {
        setLoading(false);
      }
    };

    fetchFileContent();
  }, [repositoryId, filePath]);

  const ext = filePath.split(".").pop() || "";

  if (loading) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <LoadingSpinner message={`Loading contents of ${filePath.split("/").pop()}...`} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-primary text-text-primary flex flex-col h-screen select-text">
      {/* Header Bar */}
      <header className="border-b border-border-default bg-bg-secondary/50 backdrop-blur-md shrink-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate(-1)}
              className="px-3 py-1.5 border border-border-default hover:border-accent rounded-lg text-xs font-semibold transition-colors cursor-pointer select-none"
            >
              ← Back to Chat
            </button>
            <span className="text-border-default select-none">|</span>
            <span className="text-xl select-none">📄</span>
            <h2 className="font-bold tracking-tight text-md select-all">
              File: <span className="gradient-text font-mono">{filePath.split("/").pop()}</span>
            </h2>
          </div>

          <div className="flex items-center gap-2">
            <CopyButton content={content} />
          </div>
        </div>
      </header>

      {/* Main Container */}
      <div className="flex-1 overflow-y-auto max-w-7xl w-full mx-auto px-6 py-8 space-y-6 flex flex-col">
        {errorMsg ? (
          <div className="glass-card p-6 text-center max-w-md mx-auto my-12 border border-red-500/20 bg-red-500/5 select-none">
            <span className="text-4xl block mb-2">⚠️</span>
            <h4 className="font-bold text-red-400 mb-1">Retrieval Error</h4>
            <p className="text-sm text-text-secondary mb-4">{errorMsg}</p>
            <button
              onClick={() => navigate(-1)}
              className="px-4 py-2 bg-accent text-white font-semibold text-xs rounded-lg hover:bg-accent-hover cursor-pointer"
            >
              Go Back
            </button>
          </div>
        ) : (
          <div className="space-y-4 flex-1 flex flex-col">
            {/* Meta Info details bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 bg-bg-secondary/40 border border-border-default/45 p-4 rounded-xl text-xs font-mono select-none">
              <div className="flex items-center gap-2">
                <span className="text-text-muted">Relative Path:</span>
                <span className="text-text-primary font-semibold select-all">{filePath}</span>
              </div>
              <div className="flex items-center gap-4">
                <div>
                  <span className="text-text-muted mr-1.5">Language:</span>
                  <span className="bg-bg-secondary px-2 py-0.5 rounded text-accent font-semibold">
                    {ext.toUpperCase()}
                  </span>
                </div>
                <div>
                  <span className="text-text-muted mr-1.5">Total Lines:</span>
                  <span className="text-text-primary font-semibold">{content.split("\n").length}</span>
                </div>
              </div>
            </div>

            {/* Range highlight alert banner */}
            {startLine > 0 && endLine > 0 && (
              <div className="flex items-center gap-2.5 px-4 py-3 bg-accent/10 border border-accent/20 rounded-xl text-xs text-accent select-none font-medium">
                <span>💡</span>
                <span>
                  Highlighting lines <strong>L{startLine} - L{endLine}</strong> cited in the chat session.
                </span>
              </div>
            )}

            {/* Complete File CodeViewer */}
            <div className="flex-1 min-h-0">
              <CodeViewer
                code={content}
                language={ext}
                startLine={1}
                highlightStart={startLine > 0 ? startLine : undefined}
                highlightEnd={endLine > 0 ? endLine : undefined}
                maxLinesBeforeCollapse={999999} // Never collapse in the full view page
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
