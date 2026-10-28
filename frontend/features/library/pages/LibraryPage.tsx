"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  Atom,
  BookOpen,
  Calculator,
  ChevronLeft,
  Code2,
  FlaskConical,
  Languages,
  Plus,
  Trash2,
} from "lucide-react";
import { api, del, post } from "@/lib/api";
import Modal from "@/components/ui/Modal";

const icons: Record<string, any> = {
  book: BookOpen,
  science: FlaskConical,
  math: Calculator,
  code: Code2,
  languages: Languages,
  atom: Atom,
};
const iconChoices = ["book", "science", "math", "code", "languages", "atom"];
const colors = ["#2563EB", "#7C3AED", "#F59E0B", "#0F9B83", "#E11D48", "#64748B"];

const statCards = [
  { key: "subjects", label: "المواد", emoji: "📚", color: "#2563EB", tint: "#E8F0FF" },
  { key: "quizzes", label: "الاختبارات", emoji: "🧠", color: "#CC6900", tint: "#FFF0E0" },
  { key: "summaries", label: "الملخصات", emoji: "✨", color: "#7C3AED", tint: "#F1E8FF" },
  { key: "concept_maps", label: "خرائط المفاهيم", emoji: "🗺️", color: "#07866F", tint: "#E2F4EF" },
] as const;

export default function LibraryPage() {
  const [items, setItems] = useState<any[]>([]);
  const [statistics, setStatistics] = useState<Record<string, number>>({});
  const [open, setOpen] = useState(false);
  const [icon, setIcon] = useState("book");
  const [color, setColor] = useState("#2563EB");
  const [deleting, setDeleting] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    const [subjectsResult, statisticsResult] = await Promise.allSettled([
      api<any[]>("/subjects"),
      api<Record<string, number>>("/statistics"),
    ]);
    if (subjectsResult.status === "fulfilled") setItems(subjectsResult.value);
    if (statisticsResult.status === "fulfilled") setStatistics(statisticsResult.value || {});
    const failed = [subjectsResult, statisticsResult].find(result => result.status === "rejected") as PromiseRejectedResult | undefined;
    setError(failed ? String(failed.reason?.message || "تعذر تحديث بعض الإحصائيات.") : "");
  }
  useEffect(() => {
    const refresh = () => { void load(); };
    const refreshWhenVisible = () => { if (document.visibilityState === "visible") refresh(); };
    refresh();
    window.addEventListener("focus", refresh);
    window.addEventListener("pageshow", refresh);
    document.addEventListener("visibilitychange", refreshWhenVisible);
    return () => {
      window.removeEventListener("focus", refresh);
      window.removeEventListener("pageshow", refresh);
      document.removeEventListener("visibilitychange", refreshWhenVisible);
    };
  }, []);

  const localTotals = useMemo(() => ({
    subjects: Math.max(items.length, Number(statistics.subjects || 0)),
    summaries: Math.max(items.reduce((total, item) => total + Number(item.summary_count || 0), 0), Number(statistics.summaries || 0)),
    quizzes: Number(statistics.quizzes || 0),
    concept_maps: Number(statistics.concept_maps || 0),
  }), [items, statistics]);

  async function add(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const file = form.get("file") as File;
    const data: any = {name:form.get("name"),description:form.get("description")};
    data.icon = icon;
    data.color = color;
    setSaving(true);
    let createdSubject:any;
    try {
      createdSubject = await post("/subjects", data);
      const topic:any = await post(`/subjects/${createdSubject.id}/topics`, {title:file.name.replace(/\.[^.]+$/, "") || data.name, description:data.description || ""});
      const upload = new FormData();
      upload.append("file", file);
      await post(`/topics/${topic.id}/materials`, upload);
      setOpen(false);
      setIcon("book");
      setColor("#2563EB");
      await load();
    } catch (reason:any) {
      if(createdSubject?.id) await del(`/subjects/${createdSubject.id}`).catch(()=>undefined);
      setError(reason.message || "تعذر إنشاء المادة أو قراءة الملف.");
    } finally { setSaving(false); }
  }

  async function remove(item: any) {
    if (!confirm(`هل تريد نقل مادة «${item.name}» إلى سلة المهملات؟`)) return;
    setDeleting(item.id);
    try {
      await del(`/subjects/${item.id}`);
      await load();
    } finally {
      setDeleting(null);
    }
  }

  return <div dir="rtl" className="library-page">
    <header className="flex flex-wrap items-end justify-between gap-5">
      <div>
        <p className="text-sm font-black text-primary">مكتبتك الدراسية</p>
        <h1 className="mt-2 text-3xl font-black md:text-4xl">المكتبة</h1>
        <p className="mt-2 text-slate-500">كل موادك ودروسك والمحتوى الذي أنشأته في مكان واحد.</p>
      </div>
      <button onClick={() => setOpen(true)} className="btn btn-primary library-add"><Plus size={18}/>إضافة مادة</button>
    </header>

    <section className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {statCards.map(card => <article key={card.key} className="library-stat group" style={{"--stat-color":card.color,"--stat-tint":card.tint} as React.CSSProperties}>
        <span className="library-stat-glow"/>
        <span className="library-stat-emoji" aria-hidden>{card.emoji}</span>
        <strong>{localTotals[card.key] || 0}</strong>
        <div><span>{card.label}</span><ChevronLeft size={20}/></div>
      </article>)}
    </section>

    <section className="mt-10">
      <div className="flex items-end justify-between gap-4">
        <div><h2 className="text-2xl font-black">جميع المواد</h2><p className="mt-1 text-sm text-slate-500">تتحدث تلقائيًا عند إضافة درس أو ملف جديد.</p></div>
        <span className="rounded-full bg-blue-50 px-4 py-2 text-sm font-black text-primary">{items.length} مواد</span>
      </div>
      {error && <p className="mt-5 rounded-xl bg-red-50 p-4 text-red-600">{error}</p>}
      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        {items.map(item => {
          const Icon = icons[item.icon] || BookOpen;
          return <article key={item.id} className="library-subject group">
            <Link href={`/subjects/${item.id}`} className="flex min-w-0 flex-1 items-center gap-4 p-5">
              <span className="library-subject-icon" style={{backgroundColor:`${item.color}16`,color:item.color}}><Icon size={25}/></span>
              <div className="min-w-0 flex-1">
                <h3 dir="auto" className="truncate text-lg font-black">{item.name}</h3>
                <p className="mt-1 text-sm text-slate-500">{item.topic_count} دروس · {item.summary_count} ملخصات · {item.question_count} أسئلة</p>
              </div>
              <ChevronLeft className="library-arrow" size={21}/>
            </Link>
            <button disabled={deleting === item.id} onClick={() => void remove(item)} className="library-delete" aria-label={`حذف ${item.name}`}><Trash2 size={18}/></button>
          </article>;
        })}
        {!items.length && !error && <button onClick={() => setOpen(true)} className="library-empty lg:col-span-2"><span>📚</span><b>ابدأ بإضافة أول مادة</b><small>أنشئ المادة ثم أضف الدروس والملفات الخاصة بها.</small></button>}
      </div>
    </section>

    <Modal open={open} onClose={() => setOpen(false)} title="إضافة مادة جديدة">
      <form onSubmit={add} className="space-y-5" dir="rtl">
        {error&&<p className="rounded-xl bg-red-50 p-3 text-sm text-red-600">{error}</p>}
        <label className="block text-sm font-black">اسم المادة<input required name="name" className="field mt-2" placeholder="مثال: علم الأدوية"/></label>
        <label className="block text-sm font-black">وصف مختصر<textarea name="description" className="field mt-2" placeholder="ماذا ستدرس في هذه المادة؟"/></label>
        <label className="block text-sm font-black">ملف المادة<input required name="file" type="file" accept=".pdf,.txt,image/png,image/jpeg,image/webp" className="field mt-2"/><small className="mt-2 block font-normal text-slate-500">PDF أو صورة أو ملف نصي، بحد أقصى 15MB.</small></label>
        <fieldset><legend className="text-sm font-black">اختر أيقونة</legend><div className="mt-3 grid grid-cols-6 gap-2">{iconChoices.map(key => {const Icon=icons[key];return <button type="button" key={key} onClick={()=>setIcon(key)} className={`grid aspect-square place-items-center rounded-xl border-2 transition ${icon===key?"border-primary bg-blue-50 text-primary":"border-slate-200 text-slate-500 hover:border-primary"}`}><Icon size={20}/></button>})}</div></fieldset>
        <fieldset><legend className="text-sm font-black">اختر لون المادة</legend><div className="mt-3 flex flex-wrap gap-3">{colors.map(value=><button type="button" key={value} onClick={()=>setColor(value)} className={`h-9 w-9 rounded-full transition ${color===value?"scale-110 ring-4 ring-slate-300 ring-offset-2":""}`} style={{backgroundColor:value}} aria-label={value}/>)}</div></fieldset>
        <div className="flex items-center gap-3 rounded-xl bg-slate-50 p-3"><span className="grid h-11 w-11 place-items-center rounded-xl" style={{backgroundColor:`${color}18`,color}}>{(() => {const Icon=icons[icon];return <Icon size={21}/>})()}</span><p className="text-sm text-slate-500">ستظهر المادة بهذه الأيقونة واللون.</p></div>
        <button disabled={saving} className="btn btn-primary w-full">{saving?"جارٍ إنشاء المادة وقراءة الملف...":"حفظ المادة ورفع الملف"}</button>
      </form>
    </Modal>
  </div>;
}
