"use client";

import { Check, Copy, KeyRound, Plug } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { useToast } from "@/components/ui/Toast";
import { mcpTokenApi } from "@/lib/api/auth";
import type { McpToken } from "@/types/auth";

// Lets another assistant use Stock-man's tools over MCP. The token is a
// session of its own: it shows up in the session list and "sign out
// everywhere" revokes it. It is shown once and never stored here.
export function ConnectAssistant() {
  const { toast } = useToast();
  const [token, setToken] = useState<McpToken | null>(null);
  const [busy, setBusy] = useState(false);
  const [origin, setOrigin] = useState("");

  useEffect(() => setOrigin(window.location.origin), []);

  const url = `${origin}${token?.url_path ?? "/mcp"}`;
  const command = token
    ? `claude mcp add --transport http stocksense ${url} --header "Authorization: Bearer ${token.token}"`
    : "";

  async function mint() {
    setBusy(true);
    try {
      setToken(await mcpTokenApi());
    } catch {
      toast("Couldn't create a token right now", "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="space-y-3">
      <CardTitle className="flex items-center gap-2">
        <Plug className="h-4 w-4 text-accent" aria-hidden /> Connect an AI assistant
      </CardTitle>
      <p className="text-sm text-muted-foreground">
        Claude Desktop, Claude Code or any MCP client can use the same tools Stock-man uses: quotes,
        forecasts, risk, sentiment, indicators, backtests and your paper portfolio. They can draft a
        paper trade but never place one.
      </p>

      {token ? (
        <div className="space-y-3">
          <Field label="Server URL" value={url} onCopy={() => toast("URL copied")} />
          <Field
            label="Bearer token"
            value={token.token}
            secret
            onCopy={() => toast("Token copied")}
          />
          <Field label="Claude Code" value={command} mono onCopy={() => toast("Command copied")} />
          <p className="text-xs text-muted-foreground">
            This token is shown once. It expires on{" "}
            {new Date(token.expires_at).toLocaleDateString()}, appears in your session list, and
            &ldquo;Sign out everywhere&rdquo; revokes it.
          </p>
        </div>
      ) : (
        <Button variant="secondary" size="sm" onClick={() => void mint()} loading={busy}>
          <KeyRound className="h-4 w-4" aria-hidden /> Create a connector token
        </Button>
      )}
    </Card>
  );
}

function Field({
  label,
  value,
  secret = false,
  mono = false,
  onCopy,
}: {
  label: string;
  value: string;
  secret?: boolean;
  mono?: boolean;
  onCopy: () => void;
}) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      onCopy();
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard access can be blocked; the value is selectable below.
    }
  }

  return (
    <div>
      <div className="mb-1 text-xs font-medium text-muted-foreground">{label}</div>
      <div className="flex items-center gap-2 rounded-lg border border-border bg-background/50 px-3 py-2">
        <code
          className={`min-w-0 flex-1 truncate text-xs ${mono || secret ? "font-mono" : ""}`}
          title={secret ? undefined : value}
        >
          {secret ? `${value.slice(0, 12)}…${value.slice(-6)}` : value}
        </code>
        <button
          type="button"
          onClick={() => void copy()}
          aria-label={`Copy ${label.toLowerCase()}`}
          className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          {copied ? (
            <Check className="h-4 w-4 text-bullish" aria-hidden />
          ) : (
            <Copy className="h-4 w-4" aria-hidden />
          )}
        </button>
      </div>
    </div>
  );
}
