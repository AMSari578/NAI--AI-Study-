"use client";

import { useEffect, useState } from "react";
import { Copy, Printer, Sparkles, Trash2 } from "lucide-react";
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
    simple: "مراجعة سريعة: الفكرة الرئيسية وأهم المعلومات في 3–4 أقسام، مع جدول مصطلحات ونقاط للتذكّر.",
    medium: "ملخص متوازن: كل أجزاء الملف الأساسية مشروحة ببساطة، مع التعريفات والخطوات والمقارنات وجدول المفاهيم.",
    detailed: "ملخص شامل: كل مفهوم وتعريف وخطوة ورقم ومثال قد يأتي في الاختبار، مقسّم إلى أقسام وأقسام فرعية.",
  },
  en: {
    simple: "Quick review: the central idea and the most important facts in 3–4 sections, with a key-terms table and exam reminders.",
    medium: "Balanced coverage: every main part of the file explained simply, with definitions, steps, comparisons, and a concepts table.",
    detailed: "Comprehensive coverage: every concept, definition, step, number, and example you could be tested on, organized into sections and sub-sections.",
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
    const arabic = current.language === "arabic", plain = summaryPlainText(current.content);
    try {
      // Rich HTML keeps headings, colors, and the table when pasted into Word or Google Docs; plain text is the fallback.
      await navigator.clipboard.write([new ClipboardItem({
        "text/html": new Blob([summaryHtml(current.content, arabic)], { type: "text/html" }),
        "text/plain": new Blob([plain], { type: "text/plain" }),
      })]);
    } catch {
      await navigator.clipboard.writeText(plain);
    }
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  function print() {
    document.body.classList.add("sx-printing");
    window.addEventListener("afterprint", () => document.body.classList.remove("sx-printing"), { once: true });
    window.print();
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
          <button onClick={print} className="btn btn-secondary text-xs"><Printer size={14}/>{t("Print / PDF")}</button>
        </div>
        <SummaryContent content={current.content} date={current.created_at}/>
      </article>}
      {!current && !busy && <div className="mt-6 rounded-xl bg-[#F7F7FB] p-10 text-center text-[#727785]">{t("Choose a language and summary mode, then create your summary.")}</div>}
    </section>
    <section className="card bg-white p-6">
      <h3 className="text-lg font-black">{t("Saved summaries")}</h3>
      <p className="mt-1 text-sm text-[#727785]">{t("Your summaries remain available until you delete them.")}</p>
      <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {saved.map(item => <article key={item.id} className="rounded-2xl border bg-[#F7F7FB] p-4">
          <button onClick={() => setCurrent(item)} className="w-full text-start"><div className="flex gap-2 text-[10px] font-black uppercase text-primary"><span>{displayType(item.summary_type,item.language==="arabic")}</span><span>·</span><span>{item.language==="arabic"?"العربية":"English"}</span></div><p className="mt-3 line-clamp-4 whitespace-pre-wrap text-sm leading-6 text-slate-600">{summaryPreview(item.content)}</p></button>
          <button onClick={() => void remove(item.id)} className="mt-3 flex items-center gap-1 text-xs font-black text-red-500"><Trash2 size={14}/>{t("Delete")}</button>
        </article>)}
        {!saved.length && <p className="col-span-full py-8 text-center text-sm text-[#727785]">{t("No saved summaries yet.")}</p>}
      </div>
    </section>
  </div>;
}

export const summaryPreview=(content:string)=>String(content||"").split(/\r?\n/).filter(line=>line.trim()&&!/^\s*(\||---)/.test(line)).map(line=>line.replace(/^\s*(#{1,3}|>|[-*•]|[0-9٠-٩]+[.)])\s*/,"").replace(/\*\*/g,"")).join("\n");

const sectionIcons=["📘","🧠","🔑","🧩","📌","🎯","📝","✅"];
const sectionLabel=/^((?:أولًا|ثانيًا|ثالثًا|رابعًا|خامسًا|سادسًا|سابعًا|ثامنًا|تاسعًا|عاشرًا)|[IVXL]+\.|[0-9٠-٩]+\.)\s*/;
const leadingEmoji=/^(\p{Extended_Pictographic}(?:️|‍\p{Extended_Pictographic})*)\s*/u;
const inline=(value:string)=>value.split(/(\*\*[^*]+\*\*)/g).filter(Boolean).map((part,index)=>part.startsWith("**")&&part.endsWith("**")?<strong key={index}>{part.slice(2,-2)}</strong>:part);

type Block={kind:"p"|"sub"|"num"|"bullet"|"table"|"hr";text?:string;rows?:string[][]};
type Section={label:string;emoji:string;title:string;blocks:Block[]};

// Parses the Markdown that /ai/summarize produces (and older summaries) into a header plus sections.
function parseSummary(content:string){
  const lines=String(content||"").split(/\r?\n/).map(line=>line.trim()).filter(Boolean);
  let title="",subtitle="";const intro:Block[]=[],sections:Section[]=[];
  for(let index=0;index<lines.length;index++){
    const line=lines[index],target=sections.length?sections[sections.length-1].blocks:intro;
    if(/^#\s+/.test(line)&&!title&&!sections.length){title=line.replace(/^#\s+/,"");continue}
    if(/^>\s*/.test(line)&&!sections.length){subtitle=line.replace(/^>\s*/,"");continue}
    if(/^##\s+/.test(line)||(/^#\s+/.test(line))){
      let rest=line.replace(/^#{1,2}\s+/,"");const label=rest.match(sectionLabel)?.[1]||"";rest=rest.replace(sectionLabel,"");
      const emoji=rest.match(leadingEmoji)?.[1]||"";rest=rest.replace(leadingEmoji,"");
      sections.push({label,emoji:emoji||sectionIcons[sections.length%sectionIcons.length],title:rest,blocks:[]});continue}
    if(/^###\s+/.test(line)){target.push({kind:"sub",text:line.replace(/^###\s+/,"")});continue}
    if(/^---+$/.test(line)){target.push({kind:"hr"});continue}
    if(line.startsWith("|")){
      const rows:string[][]=[];
      while(index<lines.length&&lines[index].startsWith("|")){const cells=lines[index].replace(/^\||\|$/g,"").split("|").map(cell=>cell.trim());if(!cells.every(cell=>/^:?-{3,}:?$/.test(cell)))rows.push(cells);index++}
      index--;target.push({kind:"table",rows});continue}
    const numbered=line.match(/^[0-9٠-٩]+[.)]\s+(.+)/);if(numbered){target.push({kind:"num",text:numbered[1]});continue}
    const bullet=line.match(/^[-*•✅🔹🔸📌]\s*(.+)/u);if(bullet){target.push({kind:"bullet",text:bullet[1]});continue}
    target.push({kind:"p",text:line});
  }
  return {title,subtitle,intro,sections};
}

function SummaryBlocks({blocks}:{blocks:Block[]}){
  const out:React.ReactNode[]=[];
  for(let index=0;index<blocks.length;index++){
    const block=blocks[index];
    if(block.kind==="num"||block.kind==="bullet"){
      const kind=block.kind,group:Block[]=[];
      while(index<blocks.length&&blocks[index].kind===kind){group.push(blocks[index]);index++}
      index--;
      out.push(kind==="num"
        ?<ol key={index} className="sx-terms">{group.map((item,itemIndex)=>{const [, term, explanation]=item.text!.match(/^\*\*(.+?)\*\*\s*[—–-]\s*(.+)$/)||[];return <li key={itemIndex}><span className="sx-num">{itemIndex+1}</span><p>{term?<><b className="sx-term">{term}</b><span className="sx-dash"> — </span>{inline(explanation)}</>:inline(item.text!)}</p></li>})}</ol>
        :<ul key={index} className="sx-bullets">{group.map((item,itemIndex)=><li key={itemIndex}><span aria-hidden>✦</span><p>{inline(item.text!)}</p></li>)}</ul>);
      continue;
    }
    if(block.kind==="sub")out.push(<h4 key={index} className="sx-sub">{inline(block.text!)}</h4>);
    else if(block.kind==="hr")out.push(<hr key={index} className="sx-hr"/>);
    else if(block.kind==="table"){const[head,...rows]=block.rows!;out.push(<div key={index} className="sx-table-wrap"><table className="sx-table"><thead><tr>{head.map((cell,cellIndex)=><th key={cellIndex}>{inline(cell)}</th>)}</tr></thead><tbody>{rows.map((row,rowIndex)=><tr key={rowIndex}>{row.map((cell,cellIndex)=><td key={cellIndex}>{inline(cell)}</td>)}</tr>)}</tbody></table></div>)}
    else out.push(<p key={index} className="sx-p">{inline(block.text!)}</p>);
  }
  return <>{out}</>;
}

const tones=[["#2563eb","#eff6ff"],["#7c3aed","#f5f3ff"],["#d97706","#fffbeb"],["#059669","#ecfdf5"],["#db2777","#fdf2f8"]];
const escapeHtml=(value:string)=>value.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
const boldHtml=(value:string,color:string)=>escapeHtml(value).replace(/\*\*(.+?)\*\*/g,`<b style="color:${color}">$1</b>`);

// Inline-styled HTML so the report keeps its look when pasted into Word or Google Docs.
function summaryHtml(content:string,arabic:boolean){
  const {title,subtitle,intro,sections}=parseSummary(content),dir=arabic?"rtl":"ltr",align=arabic?"right":"left";
  const blocks=(items:Block[],color:string,bg:string)=>items.map(block=>{
    if(block.kind==="sub")return `<h3 style="margin:14px 0 6px;font-size:13pt;color:#1f2433">● ${boldHtml(block.text!,color)}</h3>`;
    if(block.kind==="num"){const [, term, explanation]=block.text!.match(/^\*\*(.+?)\*\*\s*[—–-]\s*(.+)$/)||[];return `<p style="margin:5px 0;padding:6px 10px;background:${bg};border-${arabic?"right":"left"}:3px solid ${color}">${term?`<b style="color:${color}">${escapeHtml(term)}</b> — ${boldHtml(explanation,color)}`:boldHtml(block.text!,color)}</p>`}
    if(block.kind==="bullet")return `<p style="margin:5px 0">✦ ${boldHtml(block.text!,color)}</p>`;
    if(block.kind==="table"){const[head,...rows]=block.rows!;return `<table style="width:100%;border-collapse:collapse;margin:8px 0" dir="${dir}"><tr>${head.map(cell=>`<th style="background:${color};color:#fff;padding:7px 10px;border:1px solid ${color};text-align:${align}">${escapeHtml(cell)}</th>`).join("")}</tr>${rows.map((row,index)=>`<tr>${row.map((cell,cellIndex)=>`<td style="padding:7px 10px;border:1px solid #d9dee8;${index%2?`background:${bg};`:""}${cellIndex===0?`color:${color};font-weight:bold;`:""}">${boldHtml(cell,color)}</td>`).join("")}</tr>`).join("")}</table>`}
    if(block.kind==="hr")return "";
    return `<p style="margin:6px 0;color:#3b4458">${boldHtml(block.text!,color)}</p>`;
  }).join("");
  return `<div dir="${dir}" style="font-family:Segoe UI,Tahoma,Arial,sans-serif;font-size:11.5pt;line-height:1.8;color:#1f2433;text-align:${align}">`
    +(title?`<h1 style="text-align:center;font-size:20pt;color:#1e1b4b;margin:0 0 4px">${escapeHtml(title)}</h1>`:"")
    +(subtitle?`<p style="text-align:center;color:#5b6478;margin:0 0 14px">${boldHtml(subtitle,"#6d28d9")}</p>`:"")
    +(intro.length?`<div style="padding:10px 14px;background:#f8fafc;border:1px dashed #cbd5e1;margin-bottom:12px">${blocks(intro,"#4f46e5","#f8fafc")}</div>`:"")
    +sections.map((section,index)=>{const[color,bg]=section.emoji==="⭐"?["#ca8a04","#fefce8"]:section.emoji==="🏁"?["#4f46e5","#eef2ff"]:section.emoji==="📊"?["#0891b2","#ecfeff"]:tones[index%tones.length];return `<h2 style="margin:18px 0 8px;padding:8px 12px;font-size:15pt;color:${color};background:${bg};border-${arabic?"right":"left"}:5px solid ${color}">${section.emoji} ${section.label?section.label+" ":""}${escapeHtml(section.title)}</h2>${blocks(section.blocks,color,bg)}`}).join("")
    +"</div>";
}

// Clean text (no Markdown symbols) for pasting into chats or plain-text notes.
function summaryPlainText(content:string){
  const {title,subtitle,intro,sections}=parseSummary(content),strip=(value:string)=>value.replace(/\*\*/g,"");
  const blocks=(items:Block[])=>{let number=0;return items.flatMap(block=>{
    number=block.kind==="num"?number+1:0;
    if(block.kind==="hr")return [];
    if(block.kind==="table")return block.rows!.slice(1).map(row=>`• ${strip(row[0])}: ${strip(row.slice(1).join(" — "))}`);
    if(block.kind==="num")return [`${number}. ${strip(block.text!)}`];
    if(block.kind==="bullet")return [`• ${strip(block.text!)}`];
    if(block.kind==="sub")return ["",`▸ ${strip(block.text!)}`];
    return [strip(block.text!)];
  })};
  const lines=[title&&`📘 ${strip(title)}`,subtitle&&strip(subtitle),"",...blocks(intro)];
  sections.forEach(section=>{lines.push("",`${section.emoji} ${section.label?section.label+" ":""}${strip(section.title)}`,...blocks(section.blocks))});
  return lines.join("\n").replace(/\n{3,}/g,"\n\n").trim();
}

function SummaryContent({content,date}:{content:string;date?:string}){
  const {title,subtitle,intro,sections}=parseSummary(content),arabic=/[؀-ۿ]/.test(title+subtitle);
  const created=date?new Date(date).toLocaleDateString(arabic?"ar-SA":"en-US",{year:"numeric",month:"long",day:"numeric"}):"";
  return <div className="sx-doc">
    {title&&<header className="sx-hero"><span className="sx-hero-badge">📑 {arabic?"تقرير دراسي":"Study report"}</span><h1>{inline(title)}</h1>{subtitle&&<p>{inline(subtitle)}</p>}{created&&<small className="sx-hero-date">🗓️ {created} · NAI Study</small>}</header>}
    {intro.length>0&&<div className="sx-intro"><SummaryBlocks blocks={intro}/></div>}
    {sections.map((section,index)=>{
      const special=section.emoji==="⭐"?"sx-remember":section.emoji==="🏁"?"sx-conclusion":section.emoji==="📊"?"sx-glance":"";
      return <section key={index} className={`sx-section sx-tone-${index%5} ${special}`}>
        <h2><span className="sx-emoji" aria-hidden>{section.emoji}</span>{section.label&&<span className="sx-label">{section.label}</span>}<span>{inline(section.title)}</span></h2>
        <SummaryBlocks blocks={section.blocks.filter(block=>block.kind!=="hr")}/>
      </section>})}
  </div>;
}
