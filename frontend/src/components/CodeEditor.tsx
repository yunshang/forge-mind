"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { visualizeContract } from "@/lib/api";

interface CodeEditorProps {
  initialCode: string;
  contractName: string;
  onGraphUpdate: (graphData: { nodes: any[]; edges: any[] }) => void;
}

export default function CodeEditor({ initialCode, contractName, onGraphUpdate }: CodeEditorProps) {
  const [code, setCode] = useState(initialCode);
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    setCode(initialCode);
  }, [initialCode]);

  const updateGraph = useCallback(async (codeToVisualize: string) => {
    setIsUpdating(true);
    setError(null);
    try {
      const result = await visualizeContract(codeToVisualize, contractName);
      if (result.status === "success" && result.graph_data) {
        onGraphUpdate(result.graph_data);
      } else {
        setError(result.error || "Failed to visualize");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to visualize");
    } finally {
      setIsUpdating(false);
    }
  }, [contractName, onGraphUpdate]);

  const handleCodeChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newCode = e.target.value;
    setCode(newCode);

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      updateGraph(newCode);
    }, 500);
  };

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const start = e.currentTarget.selectionStart;
      const end = e.currentTarget.selectionEnd;
      const value = e.currentTarget.value;
      
      const newValue = value.substring(0, start) + '  ' + value.substring(end);
      setCode(newValue);
      
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.selectionStart = textareaRef.current.selectionEnd = start + 2;
        }
      }, 0);
    }
  };

  const lines = code.split('\n');

  return (
    <div className="h-full flex flex-col bg-white">
      <div className="px-4 py-3 border-b border-stone-200 bg-stone-50 shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-sm">✏️</span>
          <span className="text-sm font-mono text-stone-600 font-medium">
            编辑器 - {contractName || "未命名"}.sol
          </span>
          <div className="ml-auto flex items-center gap-2">
            {isUpdating && (
              <span className="text-xs font-mono text-amber-600 animate-pulse">
                更新拓扑图中...
              </span>
            )}
            {error && (
              <span className="text-xs font-mono text-red-600 bg-red-50 px-2 py-0.5 rounded">
                {error}
              </span>
            )}
            <span className="text-xs font-mono text-stone-500 bg-stone-100 px-2 py-0.5 rounded">
              {lines.length} 行
            </span>
          </div>
        </div>
      </div>
      <div className="flex-1 overflow-auto bg-stone-50 border border-stone-100 m-2 rounded-lg">
        <div className="flex">
          <div className="shrink-0 text-right pr-4 pl-4 py-3 select-none border-r border-stone-200 bg-stone-100/50">
            {lines.map((_, i) => (
              <div key={i} className="text-xs font-mono text-stone-400 leading-6">
                {i + 1}
              </div>
            ))}
          </div>
          <textarea
            ref={textareaRef}
            value={code}
            onChange={handleCodeChange}
            onKeyDown={handleKeyDown}
            className="flex-1 p-3 bg-transparent border-none outline-none resize-none font-mono text-sm leading-6 text-stone-700 w-full"
            style={{ minHeight: '100%', whiteSpace: 'pre', overflowWrap: 'normal' }}
            spellCheck={false}
            data-gramm={false}
          />
        </div>
      </div>
    </div>
  );
}