"use client";

import { useState, useCallback } from "react";
import ChatPanel from "@/components/ChatPanel";
import TerminalLog from "@/components/TerminalLog";
import CodeViewer from "@/components/CodeViewer";
import CodeEditor from "@/components/CodeEditor";
import FlowCanvas from "@/components/FlowCanvas";
import SandboxPlayground from "@/components/SandboxPlayground";
import { useAgent } from "@/hooks/useAgent";
import { exportCode, exportImage } from "@/lib/exportUtils";

type CenterTab = "code" | "graph";

interface GraphData {
  nodes: any[];
  edges: any[];
}

export default function Home() {
  const {
    isGenerating,
    result,
    error,
    logs,
    messages,
    sessionId,
    sessions,
    generate,
    reset,
    createNewSession,
    switchSession,
    removeSession,
  } = useAgent();

  const [centerTab, setCenterTab] = useState<CenterTab>("code");
  const [flowElement, setFlowElement] = useState<HTMLElement | null>(null);
  const [liveGraphData, setLiveGraphData] = useState<GraphData | null>(null);
  const [isEditMode, setIsEditMode] = useState(false);

  const handleExportCode = useCallback(() => {
    if (result?.solidity_code && result?.contract_name) {
      exportCode(result.solidity_code, result.contract_name);
    }
  }, [result]);

  const handleExportImage = useCallback(() => {
    if (flowElement) {
      exportImage(flowElement, "contract-topology");
    }
  }, [flowElement]);

  const handleFlowExportRef = useCallback((element: HTMLElement | null) => {
    setFlowElement(element);
  }, []);

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-stone-50">
      {/* Header */}
      <header className="h-14 border-b border-stone-200 bg-white flex items-center px-4 shrink-0 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="text-xl">⚡</div>
          <span className="font-mono text-base font-bold text-stone-800 tracking-wider">
            FORGEMIND
          </span>
          <span className="text-xs font-mono text-stone-500 bg-stone-100 px-2 py-0.5 rounded">v0.2.0</span>
        </div>
        <div className="ml-auto flex items-center gap-2">
          {result?.sandbox_result?.contract_address && (
            <span className="text-xs font-mono text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded">
              SANDBOX: {result.sandbox_result.contract_address.slice(0, 10)}...
            </span>
          )}
          {sessionId && (
            <span className="text-xs font-mono text-stone-600 bg-stone-100 border border-stone-200 px-2 py-0.5 rounded">
              {sessionId}
            </span>
          )}
          <button
            onClick={reset}
            className="text-xs font-mono text-stone-500 hover:text-stone-700 px-3 py-1.5 rounded-md hover:bg-stone-100 transition-colors border border-stone-200"
          >
            重置
          </button>
        </div>
      </header>

      {/* Main 3-panel layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left panel: Chat + Terminal */}
        <div className="w-80 flex flex-col border-r border-stone-200 bg-white shrink-0">
          <div className="flex-1 overflow-hidden">
            <ChatPanel
              onGenerate={generate}
              isGenerating={isGenerating}
              messages={messages}
              sessions={sessions}
              currentSessionId={sessionId}
              onNewSession={() => createNewSession()}
              onSwitchSession={switchSession}
              onDeleteSession={removeSession}
            />
          </div>
          <TerminalLog logs={logs} isRunning={isGenerating} />
        </div>

        {/* Center panel: Code + Graph tabs */}
        <div className="flex-1 flex flex-col overflow-hidden bg-white">
          <div className="flex items-center border-b border-stone-200 bg-stone-50 shrink-0">
            <div className="flex">
              <button
                onClick={() => setCenterTab("code")}
                className={`px-5 py-2.5 text-sm font-mono transition-all duration-200 ${
                  centerTab === "code"
                    ? "text-red-700 border-b-2 border-red-600 bg-red-50"
                    : "text-stone-600 hover:text-stone-800 hover:bg-stone-100"
                }`}
              >
                📄 代码
              </button>
              <button
                onClick={() => setCenterTab("graph")}
                className={`px-5 py-2.5 text-sm font-mono transition-all duration-200 ${
                  centerTab === "graph"
                    ? "text-amber-700 border-b-2 border-amber-600 bg-amber-50"
                    : "text-stone-600 hover:text-stone-800 hover:bg-stone-100"
                }`}
              >
                🔷 拓扑
              </button>
            </div>
            
            <div className="ml-auto flex items-center gap-2 px-4">
              {result?.solidity_code && centerTab === "code" && (
                <>
                  <button
                    onClick={() => setIsEditMode(!isEditMode)}
                    className={`text-xs font-mono px-3 py-1.5 rounded-md transition-all duration-200 shadow-sm hover:shadow-md ${
                      isEditMode
                        ? "text-white bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-700 hover:to-emerald-600"
                        : "text-stone-600 bg-stone-100 hover:bg-stone-200 border border-stone-200"
                    }`}
                    title={isEditMode ? "退出编辑模式" : "进入编辑模式"}
                  >
                    {isEditMode ? "✏️ 编辑中" : "📝 编辑代码"}
                  </button>
                  <button
                    onClick={handleExportCode}
                    className="text-xs font-mono text-white bg-gradient-to-r from-red-600 to-red-500 hover:from-red-700 hover:to-red-600 px-3 py-1.5 rounded-md transition-all duration-200 shadow-sm hover:shadow-md"
                    title="导出Solidity代码"
                  >
                    📥 导出代码
                  </button>
                </>
              )}
              {centerTab === "graph" && (result?.graph_data?.nodes?.length ?? 0) > 0 && (
                <button
                  onClick={handleExportImage}
                  className="text-xs font-mono text-white bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-700 hover:to-amber-600 px-3 py-1.5 rounded-md transition-all duration-200 shadow-sm hover:shadow-md"
                  title="导出拓扑图片"
                >
                  🖼️ 导出图片
                </button>
              )}
              {result?.audit_result && (
                <span
                  className={`text-xs font-mono px-3 py-1 rounded-md font-medium ${
                    result.audit_result.status === "PASS"
                      ? "text-emerald-700 bg-emerald-50 border border-emerald-200"
                      : "text-red-700 bg-red-50 border border-red-200"
                  }`}
                >
                  审计: {result.audit_result.status === "PASS" ? "通过" : "失败"}
                </span>
              )}
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-hidden">
            {centerTab === "code" ? (
              isEditMode ? (
                <CodeEditor
                  initialCode={result?.solidity_code || ""}
                  contractName={result?.contract_name || ""}
                  onGraphUpdate={setLiveGraphData}
                />
              ) : (
                <CodeViewer
                  code={result?.solidity_code || ""}
                  contractName={result?.contract_name || ""}
                />
              )
            ) : (
              <FlowCanvas 
                graphData={liveGraphData || result?.graph_data || { nodes: [], edges: [] }} 
                onExportImage={handleFlowExportRef}
              />
            )}
          </div>

          {/* Audit details bar */}
          {result?.audit_result?.vulnerabilities?.length ? (
            <div className="border-t border-stone-200 bg-stone-50 px-4 py-3 max-h-28 overflow-y-auto">
              <div className="text-xs font-mono text-stone-500 mb-2 font-medium">
                发现 {result.audit_result.vulnerabilities.length} 个问题：
              </div>
              {result.audit_result.vulnerabilities.map((v, i) => (
                <div key={i} className="text-xs font-mono py-1 flex items-start gap-2">
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                      v.severity === "high"
                        ? "text-red-700 bg-red-100 border border-red-200"
                        : v.severity === "medium"
                          ? "text-amber-700 bg-amber-100 border border-amber-200"
                          : "text-stone-600 bg-stone-100 border border-stone-200"
                    }`}
                  >
                    {v.severity === "high" ? "高" : v.severity === "medium" ? "中" : "低"}
                  </span>
                  <div className="flex-1">
                    <span className="text-stone-700 font-medium">{v.vulnerability}</span>
                    <span className="text-stone-500 ml-1">— {v.description}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : null}
        </div>

        {/* Right panel: Sandbox Playground */}
        <div className="w-80 border-l border-stone-200 bg-white shrink-0 overflow-hidden">
          <SandboxPlayground
            contractAddress={result?.sandbox_result?.contract_address || ""}
            abi={(result?.sandbox_result?.abi as Array<Record<string, unknown>>) || []}
            functions={result?.sandbox_result?.functions || []}
          />
        </div>
      </div>
    </div>
  );
}
