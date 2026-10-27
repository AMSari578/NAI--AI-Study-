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
  Languages,
  Library,
  MessageCircle,
  Moon,
  Sun,
  Trash2,
  X,
} from "lucide-react";
import { useLanguage } from "@/lib/i18n";

export function BrandMark({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const dimensions = size === "lg" ? "h-14 w-14 rounded-2xl" : size === "sm" ? "h-10 w-10 rounded-xl" : "h-12 w-12 rounded-2xl";
  return <span className={`relative grid shrink-0 place-items-center overflow-hidden bg-[#3157D5] text-white shadow-[0_6px_16px_rgba(49,87,213,.22)] ${dimensions}`}>
    <BookOpen size={size === "lg" ? 27 : size === "sm" ? 20 : 23} strokeWidth={2.4}/>
    <Sparkles className="absolute right-1.5 top-1.5 text-[#FDE68A]" size={size === "sm" ? 10 : 12} fill="currentColor"/>
  </span>;
}

const primaryLinks = [
  { href: "/dashboard", label: "Dashboard", Icon: LayoutDashboard, color: "#2563EB", tint: "#E8F1FF" },
  { href: "/subjects", label: "Library", Icon: Library, color: "#7C3AED", tint: "#F1EBFF" },
  { href: "/tests", label: "Tests", Icon: Layers3, color: "#B45B00", tint: "#FFF0DE" },
  { href: "/tools/tutor", label: "Ask the teacher", Icon: MessageCircle, color: "#0F766E", tint: "#E6F4F1" },
  { href: "/trash", label: "Trash", Icon: Trash2, color: "#DC2626", tint: "#FEF2F2" },
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
  const {t}=useLanguage();
  return <div className="mt-6">
    <p className="px-3 text-[10px] font-black uppercase tracking-[.12em] text-[#9295A2]">{t(title)}</p>
    <nav className="mt-2 space-y-1.5">
      {links.map(({ href, label, Icon, color, tint }) => {
        const active = pathname.startsWith(href);
        return <Link
          key={href}
          href={href}
          onClick={close}
          className="group flex min-h-11 items-center gap-3 rounded-lg px-3 font-bold transition-all"
          style={{ background: active ? "#172033" : "transparent", color: active ? "white" : "#526075", boxShadow: active ? "0 5px 14px rgba(23,32,51,.16)" : "none" }}
        >
          <span className="grid h-8 w-8 shrink-0 place-items-center rounded-md transition-colors" style={{ background: active ? "rgba(255,255,255,.1)" : tint, color: active ? "white" : color }}>
            <Icon size={18}/>
          </span>
          <span className="text-sm">{t(label)}</span>
          {active && <span className="ms-auto h-1.5 w-1.5 rounded-full bg-white"/>}
        </Link>;
      })}
    </nav>
  </div>;
}

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [dark, setDark] = useState(false);
  const {language,toggle,t}=useLanguage();

  useEffect(() => setOpen(false), [pathname]);
  useEffect(()=>{const enabled=localStorage.getItem("nai_theme")==="dark";setDark(enabled);document.documentElement.classList.toggle("dark",enabled)},[]);
  function toggleTheme(){setDark(value=>{const next=!value;localStorage.setItem("nai_theme",next?"dark":"light");document.documentElement.classList.toggle("dark",next);return next})}

  function logout() {
    localStorage.removeItem("najm_token");
    router.push("/login");
  }

  const close = () => setOpen(false);
  return <>
    <header className="fixed inset-x-0 top-0 z-40 flex h-16 items-center justify-between border-b border-[#E0E5EC] bg-white/95 px-4 backdrop-blur-xl lg:hidden">
      <Link href="/dashboard" className="flex items-center gap-2.5">
        <BrandMark size="sm"/>
        <span><b className="block text-lg font-black leading-none">NAI Study</b><small className="text-[8px] font-bold uppercase tracking-[.18em] text-neutral">Learn with clarity</small></span>
      </Link>
      <button onClick={() => setOpen(true)} aria-label={t("Open navigation")} className="grid h-11 w-11 place-items-center rounded-xl bg-[#E8F1FF] text-primary"><Menu size={22}/></button>
    </header>

    {open && <button aria-label={t("Close navigation")} onClick={close} className="fixed inset-0 z-40 bg-[#24252D]/35 backdrop-blur-sm lg:hidden"/>}

    <aside className={`app-sidebar fixed inset-y-0 left-0 z-50 flex w-[268px] flex-col border-r border-[#E0E5EC] bg-white shadow-[8px_0_24px_rgba(23,32,51,.035)] transition-transform duration-300 lg:translate-x-0 ${open ? "translate-x-0" : "-translate-x-full"}`}>
      <div className="flex h-20 shrink-0 items-center border-b border-[#E8ECF2] px-5">
        <Link href="/dashboard" onClick={close} className="flex items-center gap-3">
          <BrandMark/>
          <span><b className="block text-xl font-black leading-none tracking-tight">NAI Study</b><small className="mt-1.5 block text-[9px] font-black uppercase tracking-[.2em] text-neutral">Learn with clarity</small></span>
        </Link>
        <button onClick={close} aria-label={t("Close navigation")} className="ms-auto grid h-9 w-9 place-items-center rounded-lg bg-[#EAEBEF] text-[#62636C] lg:hidden"><X size={18}/></button>
      </div>

      <div className="hide-scrollbar flex-1 overflow-y-auto px-4 pb-5">
        <NavGroup title="Study space" links={primaryLinks} pathname={pathname} close={close}/>
      </div>

      <div className="shrink-0 border-t border-[#E8ECF2] bg-[#FAFBFC] p-4">
        <div className="mb-2 grid grid-cols-2 gap-2"><button onClick={toggle} className="flex items-center justify-center gap-2 rounded-xl border border-[#DCE1EC] bg-white px-3 py-2.5 text-xs font-black text-[#526075] transition hover:border-primary hover:text-primary"><Languages size={17}/>{language==="ar"?"English":"العربية"}</button><button onClick={toggleTheme} className="flex items-center justify-center gap-2 rounded-xl border border-[#DCE1EC] bg-white px-3 py-2.5 text-xs font-black text-[#526075] transition hover:border-primary hover:text-primary">{dark?<Sun size={17}/>:<Moon size={17}/>} {dark?"فاتح":"داكن"}</button></div>
        <div className="grid grid-cols-2 gap-2">
          <Link href="/reminders" onClick={close} className={`relative flex items-center gap-2 rounded-xl px-3 py-2.5 text-xs font-black transition ${pathname.startsWith("/reminders") ? "bg-[#7C3AED] text-white" : "bg-[#F1EBFF] text-[#7C3AED]"}`}><Bell size={17}/><span>{t("Reminders")}</span><i className="absolute end-2 top-2 h-1.5 w-1.5 rounded-full bg-[#F59E0B]"/></Link>
          <Link href="/settings" onClick={close} className={`flex items-center gap-2 rounded-xl px-3 py-2.5 text-xs font-black transition ${pathname.startsWith("/settings") ? "bg-[#64748B] text-white" : "bg-[#EAEBEF] text-[#62636C]"}`}><Settings size={17}/><span>{t("Settings")}</span></Link>
        </div>
        <button onClick={logout} className="mt-2 flex w-full items-center justify-center gap-2 rounded-xl px-3 py-2.5 text-sm font-black text-red-600 transition hover:bg-red-50"><LogOut size={17}/>{t("Log out")}</button>
      </div>
    </aside>
  </>;
}

