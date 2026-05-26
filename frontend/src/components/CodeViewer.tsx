"use client";

import { useMemo } from "react";
import { exportCode } from "@/lib/exportUtils";

interface CodeViewerProps {
  code: string;
  contractName: string;
}

const KEYWORDS = /\b(contract|function|modifier|event|struct|enum|mapping|address|uint\d*|int\d*|bool|string|bytes\d*|pragma|solidity|import|return|returns|if|else|for|while|require|revert|emit|public|private|internal|external|view|pure|payable|override|virtual|abstract|interface|library|is|as|from|memory|storage|calldata|delete|new|try|catch|unchecked|assembly)\b/g;
const STRINGS = /(["'])(?:(?=(\\?))\2.)*?\1/g;
const COMMENTS = /(\/\/.*$|\/\*[\s\S]*?\*\/)/gm;
const NUMBERS = /\b(\d+)\b/g;
const ADDRESSES = /\b(0x[a-fA-F0-9]{40})\b/g;

function highlightSolidity(code: string): string {
  let html = code
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  html = html.replace(COMMENTS, '<span class="text-stone-400 italic">$1</span>');
  html = html.replace(STRINGS, '<span class="text-emerald-600">$&</span>');
  html = html.replace(KEYWORDS, '<span class="text-red-600 font-semibold">$1</span>');
  html = html.replace(ADDRESSES, '<span class="text-amber-600">$1</span>');
  html = html.replace(NUMBERS, '<span class="text-sky-600">$1</span>');

  return html;
}

export default function CodeViewer({ code, contractName }: CodeViewerProps) {
  const lines = useMemo(() => (code || "").split("\n"), [code]);
  const highlighted = useMemo(() => highlightSolidity(code || "// Generated Solidity code will appear here"), [code]);

  const handleExport = () => {
    if (code) {
      exportCode(code, contractName || "contract");
    }
  };

  return (
    <div className="h-full flex flex-col bg-white">
      <div className="px-4 py-3 border-b border-stone-200 flex items-center gap-2 bg-stone-50 shrink-0">
        <span className="text-sm">📄</span>
        <span className="text-sm font-mono text-stone-600 font-medium">
          {contractName || "未命名"}.sol
        </span>
        <div className="ml-auto flex items-center gap-2">
          {code && (
            <button
              onClick={handleExport}
              className="text-xs font-mono text-white bg-gradient-to-r from-red-600 to-red-500 hover:from-red-700 hover:to-red-600 px-3 py-1.5 rounded-md transition-all shadow-sm hover:shadow-md"
              title="导出 .sol 文件"
            >
              📥 导出
            </button>
          )}
          {code && (
            <span className="text-xs font-mono text-stone-500 bg-stone-100 px-2 py-0.5 rounded">
              {lines.length} 行
            </span>
          )}
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
          <pre className="flex-1 p-3 overflow-x-auto">
            <code
              className="text-sm font-mono leading-6 text-stone-700"
              dangerouslySetInnerHTML={{ __html: highlighted }}
            />
          </pre>
        </div>
      </div>
    </div>
  );
}
