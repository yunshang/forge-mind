"use client";

import { useState, useCallback, useEffect } from "react";
import {
  createSession,
  listSessions,
  getSession,
  deleteSession as apiDeleteSession,
  generateInSession,
  type GenerateResponse,
  type Session,
  type SessionSummary,
  type SessionMessage,
} from "@/lib/api";

export interface AgentState {
  isGenerating: boolean;
  result: GenerateResponse | null;
  error: string | null;
  logs: GenerateResponse["logs"];
  sessionId: string | null;
  sessions: SessionSummary[];
  messages: SessionMessage[];
}

export function useAgent() {
  const [state, setState] = useState<AgentState>({
    isGenerating: false,
    result: null,
    error: null,
    logs: [],
    sessionId: null,
    sessions: [],
    messages: [],
  });

  // Load sessions on mount
  useEffect(() => {
    refreshSessions();
  }, []);

  const refreshSessions = useCallback(async () => {
    try {
      const sessions = await listSessions();
      setState((s) => ({ ...s, sessions }));
    } catch {
      // API might not be ready yet
    }
  }, []);

  const createNewSession = useCallback(async (name?: string) => {
    try {
      const session = await createSession(name);
      setState((s) => ({
        ...s,
        sessionId: session.id,
        messages: [],
        result: null,
        error: null,
        logs: [],
        sessions: [
          { id: session.id, name: session.name, message_count: 0, has_result: false, created_at: session.created_at, updated_at: session.updated_at },
          ...s.sessions,
        ],
      }));
      return session.id;
    } catch (err) {
      setState((s) => ({
        ...s,
        error: err instanceof Error ? err.message : "Failed to create session",
      }));
      return null;
    }
  }, []);

  const switchSession = useCallback(async (sessionId: string) => {
    try {
      const session: Session = await getSession(sessionId);
      const result = session.current_result && "status" in session.current_result
        ? (session.current_result as GenerateResponse)
        : null;
      setState((s) => ({
        ...s,
        sessionId,
        messages: session.messages,
        result,
        error: null,
        logs: result?.logs || [],
      }));
    } catch (err) {
      setState((s) => ({
        ...s,
        error: err instanceof Error ? err.message : "Failed to load session",
      }));
    }
  }, []);

  const removeSession = useCallback(async (sessionId: string) => {
    try {
      await apiDeleteSession(sessionId);
      setState((s) => {
        const remaining = s.sessions.filter((x) => x.id !== sessionId);
        const isCurrent = s.sessionId === sessionId;
        return {
          ...s,
          sessions: remaining,
          sessionId: isCurrent ? null : s.sessionId,
          messages: isCurrent ? [] : s.messages,
          result: isCurrent ? null : s.result,
        };
      });
    } catch {
      // ignore
    }
  }, []);

  const generate = useCallback(async (prompt: string) => {
    // Auto-create session if none exists
    let sid = state.sessionId;
    if (!sid) {
      const newId = await createNewSession();
      if (!newId) return;
      sid = newId;
    }

    setState((s) => ({
      ...s,
      isGenerating: true,
      error: null,
      logs: [],
      messages: [...s.messages, { role: "user", content: prompt, timestamp: new Date().toISOString() }],
    }));

    try {
      const result = await generateInSession(sid, prompt);
      setState((s) => ({
        ...s,
        isGenerating: false,
        result,
        error: result.error || null,
        logs: result.logs,
        messages: [
          ...s.messages,
          {
            role: "assistant",
            content: result.status === "success"
              ? `Generated ${result.contract_name}\nAudit: ${result.audit_result?.status || "N/A"}\nSandbox: ${result.sandbox_result?.status || "N/A"}`
              : `Error: ${result.error || "Unknown"}`,
            timestamp: new Date().toISOString(),
          },
        ],
      }));
      refreshSessions();
    } catch (err) {
      setState((s) => ({
        ...s,
        isGenerating: false,
        error: err instanceof Error ? err.message : "Unknown error",
      }));
    }
  }, [state.sessionId, createNewSession, refreshSessions]);

  const reset = useCallback(() => {
    setState((s) => ({
      ...s,
      isGenerating: false,
      result: null,
      error: null,
      logs: [],
      sessionId: null,
      messages: [],
    }));
  }, []);

  return {
    ...state,
    generate,
    reset,
    createNewSession,
    switchSession,
    removeSession,
    refreshSessions,
  };
}
