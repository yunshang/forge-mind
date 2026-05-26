"use client";

import { useState, useRef, useEffect } from "react";
import type { SessionSummary, SessionMessage } from "@/lib/api";

interface ChatPanelProps {
  onGenerate: (prompt: string) => void;
  isGenerating: boolean;
  messages: SessionMessage[];
  sessions: SessionSummary[];
  currentSessionId: string | null;
  onNewSession: () => void;
  onSwitchSession: (id: string) => void;
  onDeleteSession: (id: string) => void;
}

export default function ChatPanel({
  onGenerate,
  isGenerating,
  messages,
  sessions,
  currentSessionId,
  onNewSession,
  onSwitchSession,
  onDeleteSession,
}: ChatPanelProps) {
  const [input, setInput] = useState("");
  const [showSessions, setShowSessions] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isGenerating) return;
    onGenerate(input.trim());
    setInput("");
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Session header */}
      <div className="px-4 py-3 border-b border-stone-200 bg-stone-50">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowSessions(!showSessions)}
            className="flex-1 flex items-center gap-2 px-3 py-2 rounded-md hover:bg-stone-100 transition-colors text-left border border-transparent hover:border-stone-200"
          >
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse shadow-sm" />
            <span className="text-sm font-mono text-stone-700 truncate font-medium">
              {sessions.find((s) => s.id === currentSessionId)?.name || "新会话"}
            </span>
            <span className="text-xs text-stone-400 ml-auto">{showSessions ? "▲" : "▼"}</span>
          </button>
          <button
            onClick={onNewSession}
            className="px-3 py-1.5 text-xs font-mono text-red-600 hover:text-red-700 hover:bg-red-50 rounded-md transition-colors border border-red-200 hover:border-red-300"
            title="新建会话"
          >
            + 新建
          </button>
        </div>

        {/* Session dropdown */}
        {showSessions && (
          <div className="mt-2 max-h-48 overflow-y-auto rounded-lg border border-stone-200 bg-white shadow-lg">
            {sessions.length === 0 && (
              <div className="px-3 py-3 text-xs text-stone-500 font-mono text-center">暂无会话</div>
            )}
            {sessions.map((s) => (
              <div
                key={s.id}
                className={`flex items-center gap-2 px-3 py-2.5 text-xs font-mono cursor-pointer transition-colors border-b border-stone-100 last:border-b-0 ${
                  s.id === currentSessionId
                    ? "bg-red-50 text-red-700 border-l-2 border-l-red-500"
                    : "text-stone-600 hover:bg-stone-50"
                }`}
              >
                <button
                  onClick={() => {
                    onSwitchSession(s.id);
                    setShowSessions(false);
                  }}
                  className="flex-1 text-left truncate"
                >
                  {s.name}
                  <span className="text-stone-400 ml-1">({s.message_count})</span>
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(s.id);
                  }}
                  className="text-stone-400 hover:text-red-500 px-2 py-0.5 rounded hover:bg-red-50 transition-colors"
                  title="删除"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3 bg-stone-50/50">
        {messages.length === 0 && (
          <div className="text-center text-stone-500 mt-12">
            <div className="text-5xl mb-4">⚡</div>
            <p className="text-sm font-mono text-stone-600">描述你的智能合约</p>
            <p className="text-xs text-stone-400 mt-2 bg-stone-100 rounded-md px-3 py-1.5 inline-block">
              &quot;创建一个带有铸造和销毁功能的 ERC20 代币&quot;
            </p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[85%] px-4 py-3 rounded-xl text-sm font-mono shadow-sm ${
                msg.role === "user"
                  ? "bg-gradient-to-r from-red-600 to-red-500 text-white border border-red-700"
                  : "bg-white border border-stone-200 text-stone-700"
              }`}
            >
              <pre className="whitespace-pre-wrap break-words">{msg.content}</pre>
            </div>
          </div>
        ))}
        {isGenerating && (
          <div className="flex justify-start">
            <div className="bg-white border border-stone-200 rounded-xl px-4 py-3 text-sm font-mono text-amber-600 shadow-sm">
              <span className="animate-pulse">🤖 智能体思考中...</span>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-stone-200 bg-white">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={currentSessionId ? "修改你的合约..." : "描述你的合约..."}
            disabled={isGenerating}
            className="flex-1 bg-stone-50 border border-stone-200 rounded-lg px-4 py-2.5 text-sm font-mono text-stone-800 placeholder:text-stone-400 focus:outline-none focus:border-red-400 focus:ring-2 focus:ring-red-100 disabled:opacity-50 transition-all"
          />
          <button
            type="submit"
            disabled={isGenerating || !input.trim()}
            className="px-5 py-2.5 bg-gradient-to-r from-red-600 to-red-500 hover:from-red-700 hover:to-red-600 disabled:from-stone-300 disabled:to-stone-400 disabled:text-stone-500 rounded-lg text-sm font-mono text-white transition-all duration-200 shadow-sm hover:shadow-md disabled:shadow-none font-medium"
          >
            发送
          </button>
        </div>
      </form>
    </div>
  );
}
