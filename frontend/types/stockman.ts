// Mirrors backend/app/schemas/stockman.py and the SSE events in
// backend/app/services/stockman/agent.py.

export interface TextBlock {
  type: "text";
  text: string;
}

export interface ToolUseBlock {
  type: "tool_use";
  id: string;
  name: string;
  input: Record<string, unknown>;
}

export interface ToolResultBlock {
  type: "tool_result";
  tool_use_id: string;
  content: string;
  is_error?: boolean;
}

export type ContentBlock = TextBlock | ToolUseBlock | ToolResultBlock | { type: string };

export interface StoredMessage {
  id: string;
  role: "user" | "assistant";
  content: ContentBlock[];
  created_at: string | null;
}

export interface ConversationSummary {
  id: string;
  title: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface Conversation extends ConversationSummary {
  messages: StoredMessage[];
}

export interface StockmanStatus {
  enabled: boolean;
  model: string;
  budget: { used: number; limit: number };
  disclaimer: string;
}

export interface Grounding {
  checked: number;
  unmatched: string[];
}

export type StreamEvent =
  | { type: "text_delta"; data: { text: string } }
  | { type: "text_reset"; data: Record<string, never> }
  | { type: "tool_call"; data: { id: string; name: string; input: Record<string, unknown> } }
  | { type: "tool_result"; data: { id: string; name: string; ok: boolean } }
  | {
      type: "done";
      data: { grounding: Grounding; usage: { input_tokens: number; output_tokens: number } };
    }
  | { type: "error"; data: { message: string } };

/** A tool call as the UI shows it: the request, and the result once it lands. */
export interface ToolCall {
  id: string;
  name: string;
  input: Record<string, unknown>;
  status: "running" | "ok" | "error";
  result?: unknown;
}

/** What one assistant answer looks like on screen. Several stored turns
 * (tool rounds) collapse into one of these. */
export interface ChatTurn {
  id: string;
  role: "user" | "assistant";
  text: string;
  tools: ToolCall[];
  streaming?: boolean;
  error?: string;
  grounding?: Grounding;
}
