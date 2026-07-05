"use client";

import { useState } from "react";

// Tabbed API preview for the landing hero. The request/response mirror the real
// prediction endpoint (POST /api/v1/predictions/{ticker}) — keep them in sync
// with backend/app/schemas/prediction.py if that contract changes.

const TABS = ["curl", "Python", "JavaScript"] as const;
type Tab = (typeof TABS)[number];

const FILE_LABEL: Record<Tab, string> = {
  curl: "terminal",
  Python: "forecast.py",
  JavaScript: "forecast.ts",
};

// Muted one-accent syntax tinting; anything fancier reads as noise at this size.
const tk = {
  cmt: "text-slate-500",
  kw: "text-sky-300",
  str: "text-emerald-300/90",
  num: "text-amber-200/90",
};

function CurlPane() {
  return (
    <pre className="overflow-x-auto p-5 font-mono text-[13px] leading-relaxed text-slate-300">
      <code>
        {"curl -X POST \\\n"}
        {"  "}
        <span className={tk.str}>
          &quot;$API/api/v1/predictions/AAPL?horizon=7d&quot;
        </span>
        {" \\\n"}
        {"  -H "}
        <span className={tk.str}>&quot;Authorization: Bearer $TOKEN&quot;</span>
      </code>
    </pre>
  );
}

function PythonPane() {
  return (
    <pre className="overflow-x-auto p-5 font-mono text-[13px] leading-relaxed text-slate-300">
      <code>
        <span className={tk.kw}>import</span>
        {" requests\n\n"}
        {"r = requests.post(\n"}
        {"    "}
        <span className={tk.kw}>f</span>
        <span className={tk.str}>&quot;{"{API}"}/api/v1/predictions/AAPL&quot;</span>
        {",\n"}
        {"    params="}
        {"{"}
        <span className={tk.str}>&quot;horizon&quot;</span>
        {": "}
        <span className={tk.str}>&quot;7d&quot;</span>
        {"},\n"}
        {"    headers=auth,\n"}
        {")\n"}
        {"forecast = r.json()"}
      </code>
    </pre>
  );
}

function JavaScriptPane() {
  return (
    <pre className="overflow-x-auto p-5 font-mono text-[13px] leading-relaxed text-slate-300">
      <code>
        <span className={tk.kw}>const</span>
        {" res = "}
        <span className={tk.kw}>await</span>
        {" fetch(\n"}
        {"  "}
        <span className={tk.str}>{"`${API}/api/v1/predictions/AAPL?horizon=7d`"}</span>
        {",\n"}
        {"  { method: "}
        <span className={tk.str}>&quot;POST&quot;</span>
        {", headers: auth },\n"}
        {");\n"}
        <span className={tk.kw}>const</span>
        {" forecast = "}
        <span className={tk.kw}>await</span>
        {" res.json();"}
      </code>
    </pre>
  );
}

const PANES: Record<Tab, () => JSX.Element> = {
  curl: CurlPane,
  Python: PythonPane,
  JavaScript: JavaScriptPane,
};

export function CodeTerminal() {
  const [active, setActive] = useState<Tab>("curl");
  const Pane = PANES[active];

  return (
    <div className="overflow-hidden rounded-xl border border-slate-800 bg-[#0b1120] shadow-sm">
      <div className="flex items-center border-b border-slate-800 px-3">
        <div role="tablist" aria-label="Code examples" className="flex">
          {TABS.map((tab) => (
            <button
              key={tab}
              role="tab"
              aria-selected={active === tab}
              onClick={() => setActive(tab)}
              className={`-mb-px border-b-2 px-3 py-3 font-mono text-xs font-medium transition-colors ${
                active === tab
                  ? "border-sky-400 text-white"
                  : "border-transparent text-slate-500 hover:text-slate-300"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
        <span className="ml-auto font-mono text-[11px] text-slate-600">
          {FILE_LABEL[active]}
        </span>
      </div>

      <Pane />

      <div className="border-t border-slate-800 px-5 py-4">
        <p className="mb-1.5 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
          <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          200 OK
        </p>
        <pre className="overflow-x-auto font-mono text-xs leading-relaxed text-slate-400">
          <code>
            {"{\n"}
            {"  "}
            <span className={tk.kw}>&quot;trend&quot;</span>
            {": "}
            <span className={tk.str}>&quot;up&quot;</span>
            {", "}
            <span className={tk.kw}>&quot;confidence&quot;</span>
            {": "}
            <span className={tk.num}>0.63</span>
            {",\n"}
            {"  "}
            <span className={tk.kw}>&quot;expected_low&quot;</span>
            {": "}
            <span className={tk.num}>226.4</span>
            {", "}
            <span className={tk.kw}>&quot;expected_high&quot;</span>
            {": "}
            <span className={tk.num}>241.8</span>
            {",\n"}
            {"  "}
            <span className={tk.kw}>&quot;risk_score&quot;</span>
            {": "}
            <span className={tk.num}>42</span>
            {", "}
            <span className={tk.kw}>&quot;top_factors&quot;</span>
            {": [ … ],\n"}
            {"  "}
            <span className={tk.kw}>&quot;disclaimer&quot;</span>
            {": "}
            <span className={tk.str}>&quot;Educational only — not financial advice.&quot;</span>
            {"\n}"}
          </code>
        </pre>
      </div>
    </div>
  );
}
