"use client";

import { useRef, useEffect } from "react";

interface LogEntry {
  agent: string;
  message: string;
  level: string;
}

interface TerminalLogProps {
  logs: LogEntry[];
  isRunning: boolean;
}

const LEVEL_STYLES: Record<string, string> = {
  info: "text-sky-600",
  warn: "text-amber-600",
  error: "text-red-600",
  success: "text-emerald-600",
};

const AGENT_ICONS: Record<string, string> = {
  orchestrator: "🎯",
  coder: "👨‍💻",
  reviewer: "🔍",
};

export default function TerminalLog({ logs, isRunning }: TerminalLogProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [logs]);

  return (
    <div className="bg-stone-100 border-t border-stone-200">
      <div className="px-4 py-2 border-b border-stone-200 flex items-center gap-2 bg-stone-50">
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-red-400" />
          <div className="w-3 h-3 rounded-full bg-amber-400" />
          <div className="w-3 h-3 rounded-full bg-emerald-400" />
        </div>
        <span className="text-xs font-mono text-stone-500">智能体日志</span>
        {isRunning && (
          <span className="ml-auto text-xs font-mono text-amber-600 animate-pulse font-medium">● 运行中</span>
        )}
      </div>
      <div ref={scrollRef} className="h-48 overflow-y-auto p-3 font-mono text-xs bg-stone-50">
        {logs.length === 0 && (
          <div className="text-stone-400">等待智能体活动...</div>
        )}
        {logs.map((log, i) => (
          <div key={i} className="flex gap-2 py-1 hover:bg-stone-100 rounded px-1">
            <span className="text-stone-400 shrink-0">[{String(i).padStart(2, "0")}]</span>
            <span className="shrink-0">{AGENT_ICONS[log.agent] || "●"}</span>
            <span className="text-stone-500 shrink-0 font-medium">{log.agent}:</span>
            <span className={LEVEL_STYLES[log.level] || "text-stone-600"}>{log.message}</span>
          </div>
        ))}
        {isRunning && (
          <div className="flex gap-2 py-1 text-stone-500">
            <span>···</span>
            <span className="text-amber-600 animate-pulse">处理中...</span>
          </div>
        )}
      </div>
    </div>
  );
}
