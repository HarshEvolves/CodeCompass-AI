interface ExpandCollapseButtonProps {
  isExpanded: boolean;
  onClick: () => void;
}

export default function ExpandCollapseButton({ isExpanded, onClick }: ExpandCollapseButtonProps) {
  return (
    <button
      onClick={onClick}
      className="px-2.5 py-1.5 rounded-lg text-xs font-semibold select-none flex items-center gap-1.5 transition-all bg-bg-primary hover:bg-bg-secondary text-text-secondary border border-border-default/60 hover:text-text-primary cursor-pointer"
    >
      <span>{isExpanded ? "▲" : "▼"}</span>
      <span>{isExpanded ? "Collapse" : "Expand"}</span>
    </button>
  );
}
