import { ApiError, apiFetch, describeError } from "@/lib/api/client";
import { API_BASE } from "@/lib/env";
import type {
  Conversation,
  ConversationSummary,
  StockmanStatus,
  StreamEvent,
} from "@/types/stockman";

export function getStockmanStatus(): Promise<StockmanStatus> {
  return apiFetch<StockmanStatus>("/stockman/status");
}

export function listConversations(): Promise<ConversationSummary[]> {
  return apiFetch<ConversationSummary[]>("/stockman/conversations");
}

export function createConversation(): Promise<ConversationSummary> {
  return apiFetch<ConversationSummary>("/stockman/conversations", { method: "POST", body: {} });
}

export function getConversation(id: string): Promise<Conversation> {
  return apiFetch<Conversation>(`/stockman/conversations/${id}`);
}

export function deleteConversation(id: string): Promise<void> {
  return apiFetch<void>(`/stockman/conversations/${id}`, { method: "DELETE" });
}

/**
 * Send a message and consume the server-sent events as they arrive. A POST
 * can't use EventSource, so this reads the response body by hand: events are
 * separated by a blank line, each with an `event:` and a `data:` line.
 */
export async function streamMessage(
  id: string,
  content: string,
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_BASE}/stockman/conversations/${id}/messages`, {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({ content }),
    signal,
  });

  if (!response.ok || !response.body) {
    const text = await response.text();
    let parsed: unknown = text;
    try {
      parsed = JSON.parse(text);
    } catch {
      // a gateway error page; the status is what matters
    }
    const { message } = describeError(parsed, response.statusText);
    throw new ApiError(message, response.status, parsed);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let boundary = buffer.indexOf("\n\n");
    while (boundary >= 0) {
      const chunk = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      const event = parseEvent(chunk);
      if (event) onEvent(event);
      boundary = buffer.indexOf("\n\n");
    }
  }
}

function parseEvent(chunk: string): StreamEvent | null {
  let type = "";
  const data: string[] = [];
  for (const line of chunk.split("\n")) {
    if (line.startsWith("event: ")) type = line.slice(7).trim();
    else if (line.startsWith("data: ")) data.push(line.slice(6));
  }
  if (!type) return null;
  try {
    return { type, data: JSON.parse(data.join("\n")) } as StreamEvent;
  } catch {
    return null;
  }
}
