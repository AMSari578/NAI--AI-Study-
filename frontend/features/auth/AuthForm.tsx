"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { BookOpenCheck, BrainCircuit, CalendarCheck2 } from "lucide-react";
import { api } from "@/lib/api";
import { BrandMark } from "@/components/layout/Sidebar";

export default function AuthForm({ register = false }: { register?: boolean }) {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    const form = new FormData(event.currentTarget);
    try {
      const data: any = await api(register ? "/auth/register" : "/auth/login", { method: "POST", body: JSON.stringify(Object.fromEntries(form)) });
      localStorage.setItem("najm_token", data.access_token);
      router.push("/dashboard");
    } catch (reason: any) {
      setError(reason.message);
    } finally {
      setLoading(false);
    }
  }

  const features = [[BookOpenCheck, "Understand every lecture"], [BrainCircuit, "Study with intelligent tools"], [CalendarCheck2, "Plan and track your progress"]] as const;
  return <main className="grid min-h-screen gap-4 bg-[#EEF1F7] p-3 md:p-5 lg:grid-cols-[1.05fr_.95fr]">
    <section className="relative hidden overflow-hidden rounded-[28px] bg-gradient-to-br from-[#172554] via-[#312E81] to-[#6D28D9] p-14 text-white lg:flex lg:flex-col lg:justify-between">
      <span className="absolute -right-24 -top-24 h-80 w-80 rounded-full bg-[#2563EB]/35 blur-3xl"/>
      <span className="absolute -bottom-24 left-10 h-72 w-72 rounded-full bg-[#7C3AED]/30 blur-3xl"/>
      <div className="relative flex items-center gap-4"><BrandMark size="lg"/><div><b className="text-3xl font-black">NAI Study</b><p className="text-xs font-bold uppercase tracking-[.22em] text-white/55">Learn with clarity</p></div></div>
      <div className="relative max-w-xl">
        <p className="text-5xl font-black leading-[1.08] xl:text-6xl">Study clearly.<br/><span className="text-[#C4B5FD]">Grow confidently.</span></p>
        <p className="mt-5 text-lg leading-8 text-white/70">Your intelligent learning space for understanding, reviewing, and planning every subject.</p>
        <div className="mt-9 grid gap-3">{features.map(([Icon, label]) => <div key={label} className="flex items-center gap-3 text-sm font-bold text-white/85"><span className="grid h-9 w-9 place-items-center rounded-xl bg-white/10"><Icon size={17}/></span>{label}</div>)}</div>
      </div>
      <p className="relative text-sm text-white/45">Your AI-powered study companion</p>
    </section>
    <section className="flex items-center justify-center rounded-[28px] border border-[#DCE1EC] bg-white/70 p-6 backdrop-blur-xl">
      <form onSubmit={submit} className="w-full max-w-md rounded-[24px] border border-[#E2E7F0] bg-white p-8 shadow-[0_24px_65px_rgba(30,41,59,.09)] md:p-10">
        <div className="mb-8 flex items-center gap-3 lg:hidden"><BrandMark/><div><b className="text-xl font-black">NAI Study</b><p className="text-[9px] font-black uppercase tracking-[.2em] text-neutral">Learn with clarity</p></div></div>
        <p className="text-xs font-black uppercase tracking-[.18em] text-primary">{register ? "Begin your journey" : "Welcome back"}</p>
        <h1 className="mt-2 text-3xl font-black">{register ? "Create your account" : "Continue learning"}</h1>
        <p className="mb-7 mt-2 text-slate-500">{register ? "Build your private study space." : "Sign in to your NAI Study workspace."}</p>
        {register && <label className="mb-4 block"><span className="text-sm font-bold">Full name</span><input required name="name" className="field mt-2"/></label>}
        <label className="mb-4 block"><span className="text-sm font-bold">Email address</span><input required type="email" name="email" className="field mt-2" dir="ltr"/></label>
        <label className="mb-4 block"><span className="text-sm font-bold">Password</span><input required minLength={8} type="password" name="password" className="field mt-2" dir="ltr"/></label>
        {error && <p role="alert" className="mb-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        <button disabled={loading} className="btn btn-primary w-full">{loading ? "Please wait..." : register ? "Create account" : "Log in"}</button>
        <p className="mt-6 text-center text-sm text-slate-500">{register ? "Already have an account? " : "New here? "}<Link className="font-bold text-primary" href={register ? "/login" : "/register"}>{register ? "Log in" : "Create one"}</Link></p>
      </form>
    </section>
  </main>;
}
