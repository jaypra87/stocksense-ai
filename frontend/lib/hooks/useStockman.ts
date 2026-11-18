"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "@/lib/api/client";
import {
  createConversation,
  deleteConversation,
  getConversation,
  getStockmanStatus,
  listConversations,
  streamMessage,
} from "@/lib/api/stockman";
import type { ChatTurn, StoredMessage, StreamEvent, ToolCall } from "@/types/stockman";

const STATUS_KEY = ["stockman", "status"];
const LIST_KEY = ["stockman", "conversations"];

export function useStockmanStatus() {
  return useQuery({ queryKey: STATUS_KEY, queryFn: getStockmanStatus, staleTime: 60 * 1000 });
}

export function useConversations() {
  return useQuery({ queryKey: LIST_KEY, queryFn: listConversations });
}

export function useConversationMutations() {
  const qc = useQueryClient();
  const refresh = () => {
    void qc.invalidateQueries({ queryKey: LIST_KEY });
  };
  const create = useMutation({ mutationFn: createConversation, onSuccess: refresh });
  const remove = useMutation({ mutationFn: deleteConversation, onSuccess: refresh });
  return { create, remove };
}

/**
 * One chat thread: its stored turns, plus the turn currently streaming in.
 *
 * Stored messages are the model API's own turns, so one answer may span an
 * assistant turn with tool calls, a user turn with the results, and a final
 * assistant turn. `toTurns` folds those into one bubble per answer, with the
 * tool calls attached, which is what the screen shows.
 */
export function useChat(conversationId: string | null, onCreated?: (id: string) => void) {
  const qc = useQueryClient();
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [busy, setBusy] = useState(false);
  const abort = useRef<AbortController | null>(null);

  const stored = useQuery({
    queryKey: ["stockman", "conversation", conversationId],
    queryFn: () => getConversation(conversationId as string),
    enabled: conversationId != null,
    staleTime: Infinity,
  });

  useEffect(() => {
    if (conversationId == null) setTurns([]);
    else if (stored.data) setTurns(toTurns(stored.data.messages));
  }, [conversationId, stored.data]);

  useEffect(() => () => abort.current?.abort(), []);

  const send = useCallback(
    async (text: string) => {
      const content = text.trim();
      if (!content || busy) return;
      setBusy(true);

      let id = conversationId;
      try {
        if (id == null) {
          id = (await createConversation()).id;
          onCreated?.(id);
          void qc.invalidateQueries({ queryKey: LIST_KEY });
        }
      } catch (err) {
        setBusy(false);
        setTurns((t) => [
          ...t,
          { id: key(), role: "assistant", text: "", tools: [], error: messageOf(err) },
        ]);
        return;
      }

      const userTurn: ChatTurn = { id: key(), role: "user", text: content, tools: [] };
      const pendingId = key();
      setTurns((t) => [
        ...t,
        userTurn,
        { id: pendingId, role: "assistant", text: "", tools: [], streaming: true },
      ]);

      const patch = (fn: (turn: ChatTurn) => ChatTurn) =>
        setTurns((t) => t.map((turn) => (turn.id === pendingId ? fn(turn) : turn)));

      abort.current = new AbortController();
      try {
        await streamMessage(
          id,
          content,
          (event) => patch((turn) => apply(turn, event)),
          abort.current.signal,
        );
        patch((turn) => ({ ...turn, streaming: false }));
        // The server saved the real turns; next open reads them back.
        void qc.invalidateQueries({ queryKey: ["stockman", "conversation", id] });
        void qc.invalidateQueries({ queryKey: STATUS_KEY });
        void qc.invalidateQueries({ queryKey: LIST_KEY });
      } catch (err) {
        if (!(err instanceof DOMException && err.name === "AbortError")) {
          patch((turn) => ({ ...turn, streaming: false, error: messageOf(err) }));
        }
      } finally {
        setBusy(false);
      }
    },
    [busy, conversationId, onCreated, qc],
  );

  return { turns, send, busy, loading: stored.isLoading && conversationId != null };
}

function apply(turn: ChatTurn, event: StreamEvent): ChatTurn {
  switch (event.type) {
    case "text_delta":
      return { ...turn, text: turn.text + event.data.text };
    case "text_reset":
      return { ...turn, text: "" };
    case "tool_call":
      return {
        ...turn,
        tools: [...turn.tools, { ...event.data, status: "running" }],
      };
    case "tool_result":
      return {
        ...turn,
        tools: turn.tools.map((t) =>
          t.id === event.data.id ? { ...t, status: event.data.ok ? "ok" : "error" } : t,
        ),
      };
    case "done":
      return { ...turn, streaming: false, grounding: event.data.grounding };
    case "error":
      return { ...turn, streaming: false, error: event.data.message };
    default:
      return turn;
  }
}

export function toTurns(messages: StoredMessage[]): ChatTurn[] {
  const turns: ChatTurn[] = [];
  let current: ChatTurn | null = null;

  for (const m of messages) {
    const toolResults = m.content.filter((b) => b.type === "tool_result");
    if (m.role === "user" && toolResults.length === 0) {
      current = null;
      const text = m.content
        .map((b) => (b.type === "text" ? (b as { text: string }).text : ""))
        .join("");
      turns.push({ id: m.id, role: "user", text, tools: [] });
      continue;
    }
    if (m.role === "user") {
      for (const r of toolResults as {
        tool_use_id: string;
        content: string;
        is_error?: boolean;
      }[]) {
        const call = current?.tools.find((t) => t.id === r.tool_use_id);
        if (call) {
          call.status = r.is_error ? "error" : "ok";
          call.result = parseResult(r.content);
        }
      }
      continue;
    }
    if (!current) {
      current = { id: m.id, role: "assistant", text: "", tools: [] };
      turns.push(current);
    }
    for (const b of m.content) {
      if (b.type === "text") current.text += (b as { text: string }).text;
      else if (b.type === "tool_use") {
        const u = b as { id: string; name: string; input: Record<string, unknown> };
        const call: ToolCall = { id: u.id, name: u.name, input: u.input, status: "ok" };
        current.tools.push(call);
      }
    }
  }
  return turns;
}

function parseResult(content: string): unknown {
  try {
    return JSON.parse(content);
  } catch {
    return content;
  }
}

function messageOf(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  return "Couldn't reach Stock-man. Try again.";
}

let counter = 0;
function key(): string {
  counter += 1;
  return `local-${Date.now()}-${counter}`;
}
