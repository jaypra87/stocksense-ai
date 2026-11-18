import type { NextRequest } from "next/server";

import { proxyToBackend } from "@/lib/server/proxy";

// Same-origin API proxy; see lib/server/proxy.ts for why.

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

async function proxy(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  return proxyToBackend(req, `/api/v1/${path.join("/")}`);
}

export { proxy as GET, proxy as POST, proxy as PUT, proxy as PATCH, proxy as DELETE };
