"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AlertTriangle, ArrowRight, Bell, BookOpenCheck, CalendarDays, ClipboardCheck, Layers3 } from "lucide-react";
import { api, post } from "@/lib/api";

export function TodayOverview({ data }: any) {
  const current = data.continue_studying;
  const href = current?.material_id ? `/materials/${current.material_id}` : current ? `/topics/${current.id}` : "/subjects";
  return <section className="mt-7 grid gap-4 md:grid-cols-3"><article className="card bg-white p-5 md:col-span-2"><div className="flex items-center gap-3"><span className="grid h-11 w-11 place-items-center rounded-xl bg-[#E8F1FF] text-primary"><BookOpenCheck size={20}/></span><div><p className="text-xs font-black uppercase text-primary">Continue studying</p><h2 className="font-black">{current ? current.title : "Choose your first lecture"}</h2><p className="text-xs text-[#727785]">{current ? `${current.subject_name}${current.material_name ? ` · ${current.material_name}` : ""}` : "NAI Study will remember where you stopped."}</p>{current?.last_studied_at && <p className="mt-1 text-[10px] text-[#8B8E99]">Last studied {new Date(current.last_studied_at).toLocaleString()}</p>}</div></div><Link href={href} className="btn btn-primary mt-5">{current ? "Continue" : "Open subjects"}<ArrowRight size={16}/></Link></article><article className="card bg-white p-5"><p className="text-xs font-black uppercase text-violet">Today</p><div className="mt-3 space-y-3"><Link href="/review" className="flex items-center justify-between rounded-xl bg-[#F1EBFF] p-3"><span className="flex items-center gap-2 text-sm font-black"><ClipboardCheck size={16}/>{data.flashcards_due} flashcards due</span><ArrowRight size={14}/></Link><Link href="/planner" className="flex items-center justify-between rounded-xl bg-[#FFF0DE] p-3"><span className="flex items-center gap-2 text-sm font-black"><CalendarDays size={16}/>{data.upcoming_exams?.length || 0} upcoming exams</span><ArrowRight size={14}/></Link></div></article></section>;
}

export function UpcomingToday({ data }: any) {
  return <section className="mt-7 grid gap-4 lg:grid-cols-3"><article className="card bg-white p-5"><div className="flex items-center gap-2"><Bell className="text-violet" size={18}/><h2 className="font-black">Upcoming reminders</h2></div><div className="mt-3 space-y-2">{data.reminders?.slice(0, 4).map((item: any) => <div key={item.id} className="rounded-xl bg-[#F7F7FB] p-3"><b className="text-sm">{item.title}</b><p className="text-xs text-[#727785]">{new Date(item.reminder_datetime).toLocaleString()}</p></div>)}{!data.reminders?.length && <p className="py-5 text-center text-sm text-[#727785]">No upcoming reminders.</p>}</div></article><article className="card bg-white p-5"><div className="flex items-center gap-2"><CalendarDays className="text-[#F59E0B]" size={18}/><h2 className="font-black">Upcoming exams</h2></div><div className="mt-3 space-y-2">{data.upcoming_exams?.slice(0, 4).map((item: any) => <div key={item.id} className="rounded-xl bg-[#FFF0DE] p-3"><b className="text-sm">{item.name}</b><p className="text-xs text-[#9B4E00]">{new Date(item.exam_datetime).toLocaleString()}</p></div>)}{!data.upcoming_exams?.length && <p className="py-5 text-center text-sm text-[#727785]">No upcoming exams.</p>}</div></article><article className="card bg-white p-5"><div className="flex items-center gap-2"><AlertTriangle className="text-red-500" size={18}/><h2 className="font-black">Topics needing review</h2></div><div className="mt-3 space-y-2">{data.weak_topics?.map((item: any) => <Link key={item.topic_id} href={`/topics/${item.topic_id}`} className="block rounded-xl bg-red-50 p-3"><b className="text-sm">{item.topic_title}</b><p className="text-xs text-red-700">{item.subject_name} · {item.label}</p></Link>)}{!data.weak_topics?.length && <p className="py-5 text-center text-sm text-[#727785]">No weak topics identified yet.</p>}</div></article></section>;
}

export function DueFlashcards() {
  const [cards, setCards] = useState<any[]>([]);
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  useEffect(() => { void api<any[]>("/review/due-flashcards").then(setCards).catch(() => setCards([])); }, []);
  const card = cards[index];
  async function rate(rating: string) {
    await post(`/flashcards/${card.id}/review`, { rating });
    setCards(cards.filter(item => item.id !== card.id));
    setIndex(0);
    setFlipped(false);
  }
  return <section className="card bg-white p-5 md:p-6"><div className="flex items-center gap-3"><span className="grid h-11 w-11 place-items-center rounded-xl bg-[#F1EBFF] text-violet"><Layers3 size={20}/></span><div><h2 className="text-xl font-black">Flashcards due today</h2><p className="text-xs text-[#727785]">{cards.length} cards ready for review</p></div></div>{card ? <><button onClick={() => setFlipped(!flipped)} className="mt-5 min-h-56 w-full rounded-2xl bg-gradient-to-br from-primary to-violet p-7 text-center text-white"><small className="font-black uppercase text-white/70">{flipped ? "Answer" : "Question"}</small><p className="mt-5 text-xl font-black leading-8">{flipped ? card.answer : card.question}</p><small className="mt-5 block text-white/70">{flipped ? "Rate your recall" : "Click to reveal"}</small></button>{flipped && <div className="mt-3 grid grid-cols-2 gap-2 md:grid-cols-4">{[["again", "Again"], ["hard", "Hard"], ["good", "Good"], ["easy", "Easy"]].map(([value, label]) => <button key={value} onClick={() => void rate(value)} className={`btn text-sm ${value === "again" ? "border border-red-200 bg-red-50 text-red-700" : value === "hard" ? "border border-[#F59E0B] bg-[#FFF0DE] text-[#9B4E00]" : "btn-secondary"}`}>{label}</button>)}</div>}</> : <div className="mt-5 rounded-xl bg-emerald-50 p-8 text-center text-emerald-800"><b>You’re caught up.</b><p className="mt-1 text-sm">No flashcards are due now.</p></div>}</section>;
}
