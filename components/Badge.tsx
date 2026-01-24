export function Badge({ tone, children }: { tone: "success"|"warning"|"danger"|"primary"|"purple"|"muted"; children: React.ReactNode }) {
  const map: Record<string,string> = {
    success: "bg-cyber-success/20 text-cyber-success border-cyber-success shadow-glow-green",
    warning: "bg-cyber-warning/20 text-cyber-warning border-cyber-warning",
    danger: "bg-cyber-danger/20 text-cyber-danger border-cyber-danger",
    primary: "bg-cyber-primary/10 text-cyber-primary border-cyber-primary shadow-glow-cyan",
    purple: "bg-cyber-purple/10 text-cyber-purple border-cyber-purple shadow-glow-purple",
    muted: "bg-[#222] text-gray-400 border-[#333]"
  };
  return (
    <span className={`inline-block px-2 py-1 text-[10px] font-bold rounded border ${map[tone]}`}>
      {children}
    </span>
  );
}
