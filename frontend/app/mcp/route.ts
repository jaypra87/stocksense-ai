import type { NextRequest } from "next/server";

import { proxyToBackend } from "@/lib/server/proxy";

// The MCP endpoint, on this origin so a connector's URL is just the site
// plus /mcp and the backend stays private. Auth is the bearer token the
// client sends; nothing here reads the browser cookie.

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

function proxy(req: NextRequest) {
  return proxyToBackend(req, "/mcp");
}

export { proxy as GET, proxy as POST, proxy as DELETE };
