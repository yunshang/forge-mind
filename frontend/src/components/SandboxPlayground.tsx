"use client";

import { useState, useEffect, useRef } from "react";
import { callSandboxFunction, estimateGas, type SandboxCallResponse } from "@/lib/api";

interface ContractFunction {
  name: string;
  inputs: Array<{ name: string; type: string }>;
  outputs: Array<{ name: string; type: string }>;
  stateMutability: string;
  isRead: boolean;
}

interface TxRecord {
  timestamp: number;
  functionName: string;
  args: string;
  status: "success" | "error";
  result: string;
}

interface SandboxPlaygroundProps {
  contractAddress: string;
  abi: Array<Record<string, unknown>>;
  functions: ContractFunction[];
}

export default function SandboxPlayground({
  contractAddress,
  abi,
  functions,
}: SandboxPlaygroundProps) {
  const [results, setResults] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [consoleOutput, setConsoleOutput] = useState<string[]>([]);
  const [txHistory, setTxHistory] = useState<TxRecord[]>([]);
  const [showHistory, setShowHistory] = useState(false);

  const callFunction = async (func: ContractFunction, args: unknown[]) => {
    const key = `${func.name}-${JSON.stringify(args)}`;
    setLoading((s) => ({ ...s, [key]: true }));

    setConsoleOutput((prev) => [
      ...prev,
      `> Calling ${func.name}(${args.join(", ")})...`,
    ]);

    try {
      const result: SandboxCallResponse = await callSandboxFunction({
        contract_address: contractAddress,
        abi,
        function_name: func.name,
        args,
        is_read: func.isRead,
      });

      if (result.status === "success") {
        const display = func.isRead
          ? result.result
          : `tx: ${result.transaction_hash}`;
        setResults((s) => ({ ...s, [key]: display }));
        setConsoleOutput((prev) => [
          ...prev,
          `✓ ${func.name} → ${display}`,
        ]);
        setTxHistory((prev) => [
          {
            timestamp: Date.now(),
            functionName: func.name,
            args: JSON.stringify(args),
            status: "success" as const,
            result: display,
          },
          ...prev,
        ].slice(0, 20));
      } else {
        setResults((s) => ({ ...s, [key]: `Error: ${result.error}` }));
        setConsoleOutput((prev) => [
          ...prev,
          `✗ ${func.name} → ${result.error}`,
        ]);
        setTxHistory((prev) => [
          {
            timestamp: Date.now(),
            functionName: func.name,
            args: JSON.stringify(args),
            status: "error" as const,
            result: result.error,
          },
          ...prev,
        ].slice(0, 20));
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      setConsoleOutput((prev) => [...prev, `✗ ${func.name} → ${msg}`]);
      setTxHistory((prev) => [
        {
          timestamp: Date.now(),
          functionName: func.name,
          args: JSON.stringify(args),
          status: "error" as const,
          result: msg,
        },
        ...prev,
      ].slice(0, 20));
    } finally {
      setLoading((s) => ({ ...s, [key]: false }));
    }
  };

  if (!contractAddress || functions.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-stone-500 font-mono text-sm p-6 bg-stone-50">
        <div className="text-5xl mb-4">🎮</div>
        <p className="font-medium text-stone-600">沙盒游乐场</p>
        <p className="text-xs text-stone-400 mt-2 text-center">
          部署合约后即可与函数交互
        </p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-white">
      <div className="px-4 py-3 border-b border-stone-200 bg-gradient-to-r from-emerald-50 to-amber-50">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs font-mono text-emerald-700 font-medium">沙盒已激活</span>
        </div>
        <div className="text-xs font-mono text-stone-500 truncate bg-white/60 rounded px-2 py-1">
          {contractAddress}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-3 bg-stone-50/30">
        {functions.map((func) => (
          <FunctionCard
            key={func.name}
            func={func}
            result={results}
            loading={loading}
            onCall={callFunction}
            contractAddress={contractAddress}
            abi={abi}
          />
        ))}
      </div>

      <div className="border-t border-stone-200 bg-white">
        <div className="px-3 py-2 border-b border-stone-100 bg-stone-50">
          <span className="text-xs font-mono text-stone-500 font-medium">控制台</span>
        </div>
        <div className="h-28 overflow-y-auto p-2 font-mono text-xs bg-stone-50">
          {consoleOutput.length === 0 && (
            <div className="text-stone-400">暂无调用记录</div>
          )}
          {consoleOutput.map((line, i) => (
            <div
              key={i}
              className={`py-0.5 ${
                line.startsWith("✓")
                  ? "text-emerald-600"
                  : line.startsWith("✗")
                    ? "text-red-600"
                    : "text-stone-500"
              }`}
            >
              {line}
            </div>
          ))}
        </div>
      </div>

      <div className="border-t border-stone-200 bg-white">
        <button
          onClick={() => setShowHistory(!showHistory)}
          className="w-full px-3 py-2 flex items-center justify-between bg-stone-50 hover:bg-stone-100 transition-colors"
        >
          <span className="text-xs font-mono text-stone-500 font-medium">
            交易历史 ({txHistory.length})
          </span>
          <span className="text-xs text-stone-400">
            {showHistory ? "收起" : "展开"}
          </span>
        </button>
        {showHistory && (
          <div className="max-h-32 overflow-y-auto">
            {txHistory.length === 0 && (
              <div className="px-3 py-2 text-xs text-stone-400 font-mono">
                暂无交易记录
              </div>
            )}
            {txHistory.map((tx, i) => (
              <div
                key={i}
                className="px-3 py-1.5 text-xs font-mono border-b border-stone-100 flex items-center gap-2"
              >
                <span className="text-stone-400 shrink-0">
                  {new Date(tx.timestamp).toLocaleTimeString("zh-CN")}
                </span>
                <span
                  className={
                    tx.status === "success" ? "text-emerald-600" : "text-red-600"
                  }
                >
                  {tx.functionName}({tx.args})
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function TypeInput({
  paramType,
  name,
  value,
  onChange,
}: {
  paramType: string;
  name: string;
  value: string;
  onChange: (val: string) => void;
}) {
  if (paramType === "bool") {
    return (
      <button
        type="button"
        onClick={() => onChange(value === "true" ? "false" : "true")}
        className={`px-3 py-1.5 rounded-md text-xs font-mono border transition-all ${
          value === "true"
            ? "bg-emerald-100 border-emerald-300 text-emerald-700"
            : "bg-stone-100 border-stone-300 text-stone-500"
        }`}
      >
        {value === "true" ? "true ✓" : "false"}
      </button>
    );
  }

  if (paramType.startsWith("uint") || paramType.startsWith("int")) {
    return (
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={paramType}
        min="0"
        className="w-full bg-white border border-stone-200 rounded-md px-3 py-1.5 text-xs font-mono text-stone-700 placeholder:text-stone-400 focus:outline-none focus:border-red-400 focus:ring-2 focus:ring-red-100 transition-all"
      />
    );
  }

  return (
    <input
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={paramType === "address" ? "0x..." : paramType}
      className="w-full bg-white border border-stone-200 rounded-md px-3 py-1.5 text-xs font-mono text-stone-700 placeholder:text-stone-400 focus:outline-none focus:border-red-400 focus:ring-2 focus:ring-red-100 transition-all"
    />
  );
}

function FunctionCard({
  func,
  result,
  loading,
  onCall,
  contractAddress,
  abi,
}: {
  func: ContractFunction;
  result: Record<string, string>;
  loading: Record<string, boolean>;
  onCall: (func: ContractFunction, args: unknown[]) => void;
  contractAddress: string;
  abi: Array<Record<string, unknown>>;
}) {
  const [args, setArgs] = useState<Record<string, string>>({});
  const [gasEstimate, setGasEstimate] = useState<string | null>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (func.isRead || func.inputs.length === 0) {
      setGasEstimate(null);
      return;
    }

    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(async () => {
      const argValues = func.inputs.map((inp) => args[inp.name] || "");
      try {
        const res = await estimateGas({
          contract_address: contractAddress,
          abi,
          function_name: func.name,
          args: argValues,
        });
        if (res.status === "success") {
          setGasEstimate(
            `⛽ ${res.gas_limit.toLocaleString()} gas ≈ ${res.estimated_cost_eth} ETH`
          );
        } else {
          setGasEstimate(null);
        }
      } catch {
        setGasEstimate(null);
      }
    }, 500);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [args, func.isRead, func.inputs, func.name, contractAddress, abi]);

  const handleCall = () => {
    const argValues = func.inputs.map((inp) => args[inp.name] || "");
    onCall(func, argValues);
  };

  const resultKey = `${func.name}-${JSON.stringify(func.inputs.map((inp) => args[inp.name] || ""))}`;

  return (
    <div
      className={`rounded-lg border p-3 shadow-sm ${
        func.isRead
          ? "bg-emerald-50/50 border-emerald-200"
          : "bg-amber-50/50 border-amber-200"
      }`}
    >
      <div className="flex items-center gap-2 mb-2">
        <span
          className={`text-[10px] px-2 py-0.5 rounded font-mono font-bold ${
            func.isRead
              ? "bg-emerald-100 text-emerald-700 border border-emerald-200"
              : "bg-amber-100 text-amber-700 border border-amber-200"
          }`}
        >
          {func.isRead ? "只读" : "写入"}
        </span>
        <span className="font-mono text-sm text-stone-700 font-medium">
          {func.name}
        </span>
      </div>

      {func.inputs.map((inp) => (
        <div key={inp.name} className="mb-2">
          <label className="text-xs font-mono text-stone-500 mb-1 block">
            {inp.name} ({inp.type})
          </label>
          <TypeInput
            paramType={inp.type}
            name={inp.name}
            value={args[inp.name] || ""}
            onChange={(val) => setArgs((s) => ({ ...s, [inp.name]: val }))}
          />
        </div>
      ))}

      <button
        onClick={handleCall}
        disabled={loading[resultKey]}
        className={`w-full py-2 rounded-md text-xs font-mono text-white transition-all font-medium ${
          func.isRead
            ? "bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-700 hover:to-emerald-600 disabled:from-stone-300 disabled:to-stone-400"
            : "bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-700 hover:to-amber-600 disabled:from-stone-300 disabled:to-stone-400"
        }`}
      >
        {loading[resultKey] ? "调用中..." : `调用 ${func.name}`}
      </button>

      {gasEstimate && (
        <div className="mt-1.5 text-[11px] font-mono text-stone-400 text-center">
          {gasEstimate}
        </div>
      )}

      {result[resultKey] && (
        <div className="mt-2 p-2 bg-stone-100 border border-stone-200 rounded-md text-xs font-mono text-stone-600 break-all">
          {result[resultKey]}
        </div>
      )}
    </div>
  );
}
