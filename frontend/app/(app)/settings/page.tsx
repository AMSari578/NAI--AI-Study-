"use client";

import {Check,Languages} from "lucide-react";
import {AppLanguage,useLanguage} from "@/lib/i18n";

const choices:Array<{id:AppLanguage;title:string;description:string}>=[
  {id:"ar",title:"العربية",description:"واجهة عربية كاملة واتجاه من اليمين إلى اليسار"},
  {id:"en",title:"English",description:"English interface with left-to-right layout"},
];

export default function Page(){const{language,setLanguage,t}=useLanguage();return <><header><p className="text-sm font-black uppercase tracking-[.16em] text-primary">{t("Study space")}</p><h1 className="mt-2 text-3xl font-black">{t("Settings")}</h1></header><section className="card mt-8 max-w-3xl bg-white p-6 md:p-8"><div className="flex items-center gap-3"><span className="grid h-11 w-11 place-items-center rounded-xl bg-[#E8F1FF] text-primary"><Languages size={21}/></span><div><h2 className="font-black">{t("Language")}</h2><p className="mt-1 text-sm text-slate-500">{language==="ar"?"اختر لغة واجهة الموقع ولغة المحتوى الذي ينشئه الذكاء الاصطناعي.":"Choose the interface and AI-generated content language."}</p></div></div><div className="mt-6 grid gap-3 sm:grid-cols-2">{choices.map(choice=><button key={choice.id} onClick={()=>setLanguage(choice.id)} className={`flex items-start gap-3 rounded-2xl border p-4 text-start transition ${language===choice.id?"border-primary bg-blue-50 ring-2 ring-primary/10":"hover:border-slate-300"}`}><span className={`mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full ${language===choice.id?"bg-primary text-white":"border"}`}>{language===choice.id&&<Check size={14}/>}</span><span><b className="block">{choice.title}</b><small className="mt-1 block leading-5 text-slate-500">{choice.description}</small></span></button>)}</div><div className="mt-8 border-t pt-6"><h2 className="font-black">{language==="ar"?"الخصوصية":"Privacy"}</h2><p className="mt-2 text-sm leading-7 text-slate-500">{language==="ar"?"ملفاتك وملاحظاتك ومحتواك الدراسي خاصة بحسابك ولا تظهر للمستخدمين الآخرين.":"Your materials, notes, and study content stay private to your account."}</p></div></section></>}

