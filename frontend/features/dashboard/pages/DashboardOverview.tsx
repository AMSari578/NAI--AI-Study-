"use client";

import {useEffect,useState} from "react";
import Link from "next/link";
import {BookOpen,Brain,CheckCircle2,ListChecks,ArrowLeft} from "lucide-react";
import {api} from "@/lib/api";

const cards=[
  ["subjects","المواد","📚",BookOpen,"stat-blue","/subjects"],
  ["quizzes","الاختبارات","🧠",Brain,"stat-amber","/tests"],
  ["completed_quizzes","اختبارات مكتملة","✅",CheckCircle2,"stat-emerald","/tests"],
  ["completed_tasks","المهام المنجزة","🎯",ListChecks,"stat-violet","/tasks"],
] as const;

export default function DashboardOverview(){
  const[data,setData]=useState<any>(),[error,setError]=useState("");
  useEffect(()=>{const load=()=>api("/statistics").then(value=>{setData(value);setError("")}).catch((reason:any)=>setError(reason.message));const visible=()=>{if(document.visibilityState==="visible")void load()};void load();window.addEventListener("focus",load);window.addEventListener("pageshow",load);document.addEventListener("visibilitychange",visible);return()=>{window.removeEventListener("focus",load);window.removeEventListener("pageshow",load);document.removeEventListener("visibilitychange",visible)}},[]);
  return <main dir="rtl" className="dashboard-stats-only">
    <header className="card bg-white p-6 md:p-8"><p className="text-sm font-black text-primary">مساحتك الدراسية</p><h1 className="mt-2 text-3xl font-black md:text-4xl">لوحة التحكم</h1><p className="mt-3 text-slate-500">إحصائيات تقدمك الدراسي في مكان واحد.</p></header>
    {error&&<p className="mt-5 rounded-xl bg-red-50 p-4 text-red-600">{error}</p>}
    <section className="mt-7 grid gap-5 sm:grid-cols-2 xl:grid-cols-4">{cards.map(([key,label,emoji,Icon,color,href])=><Link key={key} href={href} className={`stat-card card group min-h-[230px] bg-white p-6 ${color}`}><span className="stat-icon grid h-16 w-16 place-items-center rounded-2xl"><span className="text-3xl" aria-hidden>{emoji}</span><Icon className="absolute opacity-0" size={24}/></span><b className="mt-8 block text-5xl">{Number(data?.[key]||0)}</b><div className="mt-3 flex items-center justify-between"><span className="text-lg font-black text-slate-500">{label}</span><ArrowLeft className="text-slate-300 transition group-hover:-translate-x-1 group-hover:text-primary" size={20}/></div></Link>)}</section>
  </main>;
}
