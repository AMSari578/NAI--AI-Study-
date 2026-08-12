"use client";

import { useEffect, useState } from "react";
import { Copy, Sparkles, Trash2 } from "lucide-react";
import { api, del, post } from "@/lib/api";

const summaryTypes = [
  ["simple", "Simple — main ideas"],
  ["detailed", "Detailed — comprehensive"],
  ["key_points", "Key points"],
  ["exam_review", "Exam review"],
  ["memorize", "What to memorize"],
] as const;

export default function SummaryStudio({ topicId, materialId }: { topicId: number; materialId?: number | null }) {
  const [type, setType] = useState("simple");
  const [language, setLanguage] = useState("english");
  const [current, setCurrent] = useState<any>();
  const [saved, setSaved] = useState<any[]>([]);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");

  const load = () => api<any[]>(`/topics/${topicId}/summaries`).then(setSaved);
  useEffect(() => { void load(); }, [topicId]);

  async function generate() {
    setBusy(true);
    setError("");
    try {
      const created = await post("/ai/summarize", { topic_id: topicId, material_id: materialId || null, summary_type: type, language });
      setCurrent(created);
      await load();
    } catch (reason: any) {
      setError(reason.message);
    } finally {
      setBusy(false);
    }
  }

  async function remove(id: number) {
    await del(`/summaries/${id}`);
    if (current?.id === id) setCurrent(undefined);
    await load();
  }

  async function copy() {
    if (!current?.content) return;
    await navigator.clipboard.writeText(current.content);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  return <div className="space-y-5">
    <section className="card bg-white p-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div><h2 className="text-2xl font-black">Create a study summary</h2><p className="mt-1 text-sm text-[#727785]">NAI Study uses only the context you selected.</p></div>
        <div className="flex flex-wrap items-end gap-2">
          <label className="text-xs font-black">Mode<select value={type} onChange={event => setType(event.target.value)} className="field mt-1">{summaryTypes.map(([id, label]) => <option key={id} value={id}>{label}</option>)}</select></label>
          <label className="text-xs font-black">Language<select value={language} onChange={event => setLanguage(event.target.value)} className="field mt-1"><option value="english">English</option><option value="arabic">العربية</option></select></label>
          <button disabled={busy} onClick={() => void generate()} className="btn btn-primary"><Sparkles size={17}/>{busy ? "Creating..." : "Create summary"}</button>
        </div>
      </div>
      {error && <p className="mt-4 rounded-xl bg-red-50 p-3 text-red-600">{error}</p>}
      {busy && <div className="mt-6 rounded-xl bg-[#F7F7FB] p-10 text-center text-[#727785]">NAI Study is reading your material...</div>}
      {current && !busy && <article dir={current.language === "arabic" ? "rtl" : "ltr"} className="summary-beauty mt-6">
        <div className="mb-4 flex items-center gap-2">
          <span className="rounded-full bg-[#E8F1FF] px-3 py-1 text-xs font-black text-primary">{current.summary_type}</span>
          <span className="rounded-full bg-[#F1EBFF] px-3 py-1 text-xs font-black text-violet">{current.language}</span>
          <button onClick={() => void copy()} className="btn btn-secondary ml-auto text-xs"><Copy size={14}/>{copied ? "Copied" : "Copy"}</button>
        </div>
        <div className="whitespace-pre-wrap leading-8">{current.content}</div>
      </article>}
      {!current && !busy && <div className="mt-6 rounded-xl bg-[#F7F7FB] p-10 text-center text-[#727785]">Choose a language and summary mode, then create your summary.</div>}
    </section>
    <section className="card bg-white p-6">
      <h3 className="text-lg font-black">Saved summaries</h3>
      <p className="mt-1 text-sm text-[#727785]">Your summaries remain available until you delete them.</p>
      <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {saved.map(item => <article key={item.id} className="rounded-2xl border bg-[#F7F7FB] p-4">
          <button onClick={() => setCurrent(item)} className="w-full text-left"><div className="flex gap-2 text-[10px] font-black uppercase text-primary"><span>{item.summary_type}</span><span>·</span><span>{item.language}</span></div><p className="mt-3 line-clamp-4 whitespace-pre-wrap text-sm leading-6 text-slate-600">{item.content}</p></button>
          <button onClick={() => void remove(item.id)} className="mt-3 flex items-center gap-1 text-xs font-black text-red-500"><Trash2 size={14}/>Delete</button>
        </article>)}
        {!saved.length && <p className="col-span-full py-8 text-center text-sm text-[#727785]">No saved summaries yet.</p>}
      </div>
    </section>
  </div>;
}
