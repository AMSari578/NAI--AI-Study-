"use client";

import { useEffect, useState } from "react";
import { Copy, Sparkles, Trash2 } from "lucide-react";
import { api, del, post } from "@/lib/api";
import { useLanguage } from "@/lib/i18n";

const summaryTypes = [
  ["simple", "Simple — main ideas"],
  ["medium", "Medium — balanced"],
  ["detailed", "Detailed — comprehensive"],
] as const;
const typeLabels:Record<string,string>={simple:"بسيط",medium:"متوسط",detailed:"شامل",key_points:"نقاط مهمة",exam_review:"مراجعة اختبار",memorize:"للحفظ"};
const displayType=(value:string,arabic:boolean)=>arabic?(typeLabels[value]||value):value.replaceAll("_"," ");
const summaryDescriptions = {
  ar: {
    simple: "مراجعة سريعة: الفكرة الرئيسية وأهم النقاط فقط (5–12 نقطة).",
    medium: "ملخص متوازن: الأقسام الأساسية والتعريفات والقوائم والخطوات المهمة (18–38 نقطة).",
    detailed: "ملخص شامل: قراءة جميع أجزاء الملف واستخراج المفاهيم والتفاصيل والأمثلة والاستثناءات والأرقام (حتى 65 نقطة لكل جزء كثيف).",
  },
  en: {
    simple: "Quick review: the central idea and only the highest-value points (5–12 points).",
    medium: "Balanced coverage: main sections, definitions, lists, and important processes (18–38 points).",
    detailed: "Comprehensive coverage: every part of the file, including concepts, details, examples, exceptions, and numbers (up to 65 points per dense section).",
  },
} as const;

export default function SummaryStudio({ topicId, materialId }: { topicId: number; materialId?: number | null }) {
  const {language:uiLanguage,t}=useLanguage();
  const [type, setType] = useState("simple");
  const [language, setLanguage] = useState(uiLanguage === "ar" ? "arabic" : "english");
  const [current, setCurrent] = useState<any>();
  const [saved, setSaved] = useState<any[]>([]);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");

  const load = () => api<any[]>(`/topics/${topicId}/summaries`).then(setSaved);
  useEffect(() => { void load(); }, [topicId]);
  useEffect(() => { setLanguage(uiLanguage === "ar" ? "arabic" : "english"); }, [uiLanguage]);

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
        <div><h2 className="text-2xl font-black">{t("Create a study summary")}</h2><p className="mt-1 text-sm text-[#727785]">{t("NAI Study uses only the context you selected.")}</p></div>
        <div className="flex flex-wrap items-end gap-2">
          <label className="text-xs font-black">{t("Mode")}<select value={type} onChange={event => setType(event.target.value)} className="field mt-1">{summaryTypes.map(([id, label]) => <option key={id} value={id}>{t(label)}</option>)}</select></label>
          <label className="text-xs font-black">{t("Language")}<select value={language} onChange={event => setLanguage(event.target.value)} className="field mt-1"><option value="english">{t("English")}</option><option value="arabic">العربية</option></select></label>
          <button disabled={busy} onClick={() => void generate()} className="btn btn-primary"><Sparkles size={17}/>{busy ? t("Creating...") : t("Create summary")}</button>
        </div>
      </div>
      <div className="mt-4 rounded-2xl border border-primary/15 bg-primary/5 px-4 py-3 text-sm leading-7 text-slate-600 dark:text-slate-200">
        <span className="me-2 font-black text-primary">{type === "simple" ? "⚡" : type === "medium" ? "📚" : "🔎"}</span>
        {summaryDescriptions[uiLanguage === "ar" ? "ar" : "en"][type as keyof typeof summaryDescriptions.ar]}
      </div>
      {error && <p className="mt-4 rounded-xl bg-red-50 p-3 text-red-600">{error}</p>}
      {busy && <div className="mt-6 rounded-xl bg-[#F7F7FB] p-10 text-center text-[#727785]">{t("NAI Study is reading your material...")}</div>}
      {current && !busy && <article dir={current.language === "arabic" ? "rtl" : "ltr"} className="summary-beauty mt-6">
        <div className="mb-4 flex items-center gap-2">
          <span className="rounded-full bg-[#E8F1FF] px-3 py-1 text-xs font-black text-primary">{displayType(current.summary_type,current.language==="arabic")}</span>
          <span className="rounded-full bg-[#F1EBFF] px-3 py-1 text-xs font-black text-violet">{current.language==="arabic"?"العربية":"English"}</span>
          <button onClick={() => void copy()} className="btn btn-secondary ms-auto text-xs"><Copy size={14}/>{copied ? t("Copied") : t("Copy")}</button>
        </div>
        <SummaryContent content={current.content}/>
      </article>}
      {!current && !busy && <div className="mt-6 rounded-xl bg-[#F7F7FB] p-10 text-center text-[#727785]">{t("Choose a language and summary mode, then create your summary.")}</div>}
    </section>
    <section className="card bg-white p-6">
      <h3 className="text-lg font-black">{t("Saved summaries")}</h3>
      <p className="mt-1 text-sm text-[#727785]">{t("Your summaries remain available until you delete them.")}</p>
      <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {saved.map(item => <article key={item.id} className="rounded-2xl border bg-[#F7F7FB] p-4">
          <button onClick={() => setCurrent(item)} className="w-full text-start"><div className="flex gap-2 text-[10px] font-black uppercase text-primary"><span>{displayType(item.summary_type,item.language==="arabic")}</span><span>·</span><span>{item.language==="arabic"?"العربية":"English"}</span></div><p className="mt-3 line-clamp-4 whitespace-pre-wrap text-sm leading-6 text-slate-600">{item.content}</p></button>
          <button onClick={() => void remove(item.id)} className="mt-3 flex items-center gap-1 text-xs font-black text-red-500"><Trash2 size={14}/>{t("Delete")}</button>
        </article>)}
        {!saved.length && <p className="col-span-full py-8 text-center text-sm text-[#727785]">{t("No saved summaries yet.")}</p>}
      </div>
    </section>
  </div>;
}

function SummaryContent({content}:{content:string}){
  const lines=String(content||"").split(/\r?\n/).map(line=>line.trim()).filter(Boolean);
  const headingIcons=["📘","🧠","🔑","🧩","📌","🎯","📝","✅"];
  const pointIcons=["🔹","✅","📍","💡"];
  let headingNumber=0;
  const inline=(value:string)=>value.split(/(\*\*[^*]+\*\*)/g).filter(Boolean).map((part,index)=>part.startsWith("**")&&part.endsWith("**")?<strong key={index}>{part.slice(2,-2)}</strong>:part);
  const itemBody=(item:string)=>{const marker=/([0-9٠-٩]+[.)-]\s*)/g,first=item.search(marker);if(first<0)return <p>{inline(item)}</p>;const intro=item.slice(0,first).trim(),numbered=item.slice(first).split(/(?=[0-9٠-٩]+[.)-]\s*)/).map(value=>value.replace(/^[0-9٠-٩]+[.)-]\s*/,"").trim()).filter(Boolean);return <div>{intro&&<p className="mb-2 font-bold">{inline(intro)}</p>}<ol className="summary-enumeration">{numbered.map((value,index)=><li key={index}>{inline(value)}</li>)}</ol></div>};
  return <div className="summary-document">{lines.map((line,index)=>{
    const heading=line.match(/^#{1,3}\s+(.+)/);
    if(heading){const position=headingNumber++;return <h2 key={index} className={`summary-tone-${position%4}`}><span aria-hidden>{headingIcons[position%headingIcons.length]}</span><span>{inline(heading[1])}</span></h2>}
    if(/^---+$/.test(line))return <hr key={index}/>;
    const bullet=line.match(/^[-*•✅🔹🔸📌]\s*(.+)/);
    if(bullet)return <div key={index} className={`summary-document-point summary-point-${index%4}`}><span aria-hidden>{pointIcons[index%pointIcons.length]}</span>{itemBody(bullet[1])}</div>;
    return <p key={index} className={index===0?"summary-intro":""}>{inline(line)}</p>;
  })}</div>;
}
