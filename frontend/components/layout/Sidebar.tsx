"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import {
  BarChart3,
  Bell,
  BookOpen,
  Brain,
  CalendarDays,
  ClipboardCheck,
  Layers3,
  LayoutDashboard,
  LogOut,
  Menu,
  Search,
  Settings,
  Sparkles,
  Timer,
  X,
} from "lucide-react";

export function BrandMark({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const dimensions = size === "lg" ? "h-14 w-14 rounded-2xl" : size === "sm" ? "h-10 w-10 rounded-xl" : "h-12 w-12 rounded-2xl";
  return <span className={`relative grid shrink-0 place-items-center overflow-hidden bg-gradient-to-br from-[#2563EB] via-[#4F46E5] to-[#7C3AED] text-white shadow-[0_12px_28px_rgba(79,70,229,.28)] ${dimensions}`}>
    <span className="absolute -right-3 -top-3 h-8 w-8 rounded-full bg-white/20 blur-sm"/>
    <BookOpen size={size === "lg" ? 27 : size === "sm" ? 20 : 23} strokeWidth={2.4}/>
    <Sparkles className="absolute right-1.5 top-1.5 text-[#FDE68A]" size={size === "sm" ? 10 : 12} fill="currentColor"/>
  </span>;
}

const primaryLinks = [
  { href: "/dashboard", label: "Dashboard", Icon: LayoutDashboard, color: "#2563EB", tint: "#E8F1FF" },
  { href: "/subjects", label: "Subjects", Icon: BookOpen, color: "#7C3AED", tint: "#F1EBFF" },
  { href: "/summaries", label: "Summaries", Icon: Sparkles, color: "#7C3AED", tint: "#F1EBFF" },
  { href: "/tests", label: "Tests", Icon: Layers3, color: "#7C3AED", tint: "#EDE9FE" },
  { href: "/review", label: "Review", Icon: ClipboardCheck, color: "#F59E0B", tint: "#FFF0DE" },
] as const;

const organizeLinks = [
  { href: "/progress", label: "Progress", Icon: BarChart3, color: "#0F766E", tint: "#E6F4F1" },
  { href: "/planner", label: "Planner", Icon: CalendarDays, color: "#2563EB", tint: "#E8F1FF" },
  { href: "/calendar", label: "Calendar", Icon: CalendarDays, color: "#7C3AED", tint: "#F1EBFF" },
  { href: "/search", label: "Search", Icon: Search, color: "#64748B", tint: "#EAEBEF" },
  { href: "/focus", label: "Focus", Icon: Timer, color: "#0F766E", tint: "#E6F4F1" },
  { href: "/exam-mode", label: "Mock exam", Icon: Brain, color: "#F59E0B", tint: "#FFF0DE" },
] as const;

type NavigationLink = (typeof primaryLinks)[number] | (typeof organizeLinks)[number];

function NavGroup({ title, links, pathname, close }: { title: string; links: readonly NavigationLink[]; pathname: string; close: () => void }) {
  return <div className="mt-6">
    <p className="px-3 text-[10px] font-black uppercase tracking-[.2em] text-[#9295A2]">{title}</p>
    <nav className="mt-2 space-y-1.5">
      {links.map(({ href, label, Icon, color, tint }) => {
        const active = pathname.startsWith(href);
        return <Link
          key={href}
          href={href}
          onClick={close}
          className="group flex min-h-12 items-center gap-3 rounded-xl px-3 font-extrabold transition-all"
          style={{ background: active ? color : "transparent", color: active ? "white" : "#555965", boxShadow: active ? `0 9px 22px ${color}32` : "none" }}
        >
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg transition-transform group-hover:scale-105" style={{ background: active ? "rgba(255,255,255,.2)" : tint, color: active ? "white" : color }}>
            <Icon size={18}/>
          </span>
          <span className="text-sm">{label}</span>
          {active && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-white"/>}
        </Link>;
      })}
    </nav>
  </div>;
}

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [open, setOpen] = useState(false);

  useEffect(() => setOpen(false), [pathname]);

  function logout() {
    localStorage.removeItem("najm_token");
    router.push("/login");
  }

  const close = () => setOpen(false);
  return <>
    <header className="fixed inset-x-0 top-0 z-40 flex h-16 items-center justify-between border-b border-[#D9DBE8] bg-[#F7F7FB]/95 px-4 backdrop-blur-xl lg:hidden">
      <Link href="/dashboard" className="flex items-center gap-2.5">
        <BrandMark size="sm"/>
        <span><b className="block text-lg font-black leading-none">NAI Study</b><small className="text-[8px] font-bold uppercase tracking-[.18em] text-neutral">Learn with clarity</small></span>
      </Link>
      <button onClick={() => setOpen(true)} aria-label="Open navigation" className="grid h-11 w-11 place-items-center rounded-xl bg-[#E8F1FF] text-primary"><Menu size={22}/></button>
    </header>

    {open && <button aria-label="Close navigation" onClick={close} className="fixed inset-0 z-40 bg-[#24252D]/35 backdrop-blur-sm lg:hidden"/>}

    <aside className={`fixed inset-y-0 left-0 z-50 flex w-[282px] flex-col border-r border-[#D9DBE8] bg-[#F7F7FB]/98 shadow-[18px_0_45px_rgba(46,50,73,.08)] backdrop-blur-xl transition-transform duration-300 lg:translate-x-0 ${open ? "translate-x-0" : "-translate-x-full"}`}>
      <div className="flex h-20 shrink-0 items-center border-b border-[#D9DBE8] px-5">
        <Link href="/dashboard" onClick={close} className="flex items-center gap-3">
          <BrandMark/>
          <span><b className="block text-xl font-black leading-none tracking-tight">NAI Study</b><small className="mt-1.5 block text-[9px] font-black uppercase tracking-[.2em] text-neutral">Learn with clarity</small></span>
        </Link>
        <button onClick={close} aria-label="Close navigation" className="ml-auto grid h-9 w-9 place-items-center rounded-lg bg-[#EAEBEF] text-[#62636C] lg:hidden"><X size={18}/></button>
      </div>

      <div className="hide-scrollbar flex-1 overflow-y-auto px-4 pb-5">
        <NavGroup title="Study space" links={primaryLinks} pathname={pathname} close={close}/>
        <NavGroup title="Plan and improve" links={organizeLinks} pathname={pathname} close={close}/>
      </div>

      <div className="shrink-0 border-t border-[#D9DBE8] bg-white/60 p-4">
        <div className="grid grid-cols-2 gap-2">
          <Link href="/reminders" onClick={close} className={`relative flex items-center gap-2 rounded-xl px-3 py-2.5 text-xs font-black transition ${pathname.startsWith("/reminders") ? "bg-[#7C3AED] text-white" : "bg-[#F1EBFF] text-[#7C3AED]"}`}><Bell size={17}/><span>Reminders</span><i className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-[#F59E0B]"/></Link>
          <Link href="/settings" onClick={close} className={`flex items-center gap-2 rounded-xl px-3 py-2.5 text-xs font-black transition ${pathname.startsWith("/settings") ? "bg-[#64748B] text-white" : "bg-[#EAEBEF] text-[#62636C]"}`}><Settings size={17}/><span>Settings</span></Link>
        </div>
        <button onClick={logout} className="mt-2 flex w-full items-center justify-center gap-2 rounded-xl px-3 py-2.5 text-sm font-black text-red-600 transition hover:bg-red-50"><LogOut size={17}/>Log out</button>
      </div>
    </aside>
  </>;
}

