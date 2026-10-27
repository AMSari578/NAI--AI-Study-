"use client";

import {useEffect,useState} from "react";
import Link from "next/link";
import {BookOpen,Brain,Map,Sparkles,ArrowLeft,FileText} from "lucide-react";
import {api} from "@/lib/api";

const cards=[
  ["subjects","المواد","📚",BookOpen,"stat-blue","/subjects"],
  ["quizzes","الاختبارات","🧠",Brain,"stat-amber","/tests"],
  ["summaries","الملخصات","✨",Sparkles,"stat-violet","/summaries"],
  ["concept_maps","خرائط المفاهيم","🗺️",Map,"stat-emerald","/results/concept-maps"],
] as const;

export default function DashboardOverview(){
  const[data,setData]=useState<any>(),[error,setError]=useState("");
  useEffect(()=>{api("/dashboard").then(setData).catch((reason:any)=>setError(reason.message))},[]);
  if(!data)return <div className="card p-8">{error||"جارٍ تحميل لوحة التحكم..."}</div>;
  return <>
    <header><p className="text-sm font-black text-primary">لوحة التحكم</p><h1 className="mt-2 text-3xl font-black">مرحبًا، {data.user.name.split(" ")[0]}</h1><p className="mt-2 text-slate-500">نظرة سريعة على مكتبتك وكل المحتوى الدراسي الذي أنشأته.</p></header>
    <section className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{cards.map(([key,label,emoji,Icon,color,href])=><Link key={key} href={href} className={`stat-card card group bg-white p-5 ${color}`}><span className="stat-icon grid h-14 w-14 place-items-center rounded-2xl"><span className="text-2xl" aria-hidden>{emoji}</span><Icon className="absolute opacity-0" size={22}/></span><b className="mt-5 block text-3xl">{data.statistics?.[key]||0}</b><div className="mt-1 flex items-center justify-between"><span className="font-bold text-slate-500">{label}</span><ArrowLeft className="text-slate-300 transition group-hover:-translate-x-1 group-hover:text-primary" size={18}/></div></Link>)}</section>
    <section className="mt-8"><div className="flex items-end justify-between"><div><h2 className="text-xl font-black">آخر المواد</h2><p className="mt-1 text-sm text-slate-500">تتحدث تلقائيًا عند إضافة ملف أو فتح درس.</p></div><Link href="/subjects" className="text-sm font-black text-primary">فتح المكتبة</Link></div><div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">{data.recent_topics?.map((topic:any)=><Link key={topic.id} href={`/topics/${topic.id}`} className="card flex items-center gap-4 bg-white p-5"><span className="grid h-11 w-11 place-items-center rounded-xl bg-blue-50 text-primary"><BookOpen size={20}/></span><span className="min-w-0 flex-1"><b className="block truncate">{topic.title}</b><small className="text-slate-500">{topic.subject_name} · {topic.material_count} ملفات</small></span><ArrowLeft size={17} className="text-slate-300"/></Link>)}{!data.recent_topics?.length&&<div className="card col-span-full p-10 text-center text-slate-500"><FileText className="mx-auto mb-3"/>ابدأ بإضافة مادة من المكتبة.</div>}</div></section>
  </>;
}
