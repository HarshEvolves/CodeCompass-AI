interface StatusBadgeProps {
  status: string;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const normStatus = status.toUpperCase();

  const colorMap: Record<string, string> = {
    UPLOADED: "bg-blue-500/10 text-blue-400 border-blue-500/25",
    EXTRACTED: "bg-amber-500/10 text-amber-400 border-amber-500/25",
    PARSED: "bg-indigo-500/10 text-indigo-400 border-indigo-500/25",
    CHUNKED: "bg-purple-500/10 text-purple-400 border-purple-500/25",
    INDEXED: "bg-emerald-500/10 text-emerald-400 border-emerald-500/25",
    FAILED: "bg-red-500/10 text-red-400 border-red-500/25",
  };

  const currentStyle = colorMap[normStatus] || "bg-text-secondary/10 text-text-secondary border-text-secondary/25";

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${currentStyle}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current mr-1.5 animate-pulse" />
      {normStatus}
    </span>
  );
}
