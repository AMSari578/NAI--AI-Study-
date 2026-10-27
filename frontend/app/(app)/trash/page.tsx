"use client";

import { useEffect, useState } from "react";
import { ArchiveRestore, Trash2 } from "lucide-react";
import { api, del, post } from "@/lib/api";

const labels:Record<string,string>={subject:"مادة",material:"ملف",summary:"ملخص",quiz:"اختبار","concept-map":"خريطة مفاهيم",conversation:"محادثة"};
const emojis:Record<string,string>={subject:"📚",material:"📄",summary:"✨",quiz:"🧠","concept-map":"🗺️",conversation:"💬"};

export default function TrashPage(){
  const[items,setItems]=useState<any[]>([]),[error,setError]=useState("");
  const load=()=>api<any[]>("/trash").then(setItems).catch((reason:any)=>setError(reason.message));
  useEffect(()=>{void load()},[]);
  async function restore(item:any){await post(`/trash/${item.type}/${item.id}/restore`,{});await load()}
  async function remove(item:any){if(!confirm("حذف هذا العنصر نهائيًا؟ لا يمكن التراجع عن ذلك."))return;await del(`/trash/${item.type}/${item.id}`);await load()}
  return <>
    <header><p className="text-sm font-black text-red-500">🗑️ العناصر المحذوفة</p><h1 className="mt-2 text-3xl font-black">سلة المهملات</h1><p className="mt-2 text-slate-500">استعد أي عنصر حُذف بالخطأ، أو احذفه نهائيًا.</p></header>
    {error&&<p className="mt-6 rounded-xl bg-red-50 p-4 text-red-600">{error}</p>}
    <section className="card mt-8 overflow-hidden bg-white"><div className="divide-y divide-slate-200">{items.map(item=><article key={`${item.type}-${item.id}`} className="interactive-row flex flex-wrap items-center gap-4 p-5"><span className="emoji-orb">{emojis[item.type]||"🗂️"}</span><div className="min-w-0 flex-1"><b className="block truncate">{item.title}</b><small className="text-slate-500">{labels[item.type]||item.type}{item.subject?` · ${item.subject}`:""}</small></div><button onClick={()=>void restore(item)} className="btn btn-secondary"><ArchiveRestore size={17}/>استعادة</button><button onClick={()=>void remove(item)} className="btn border border-red-200 bg-red-50 text-red-600"><Trash2 size={17}/>حذف نهائي</button></article>)}{!items.length&&<div className="p-16 text-center"><div className="text-5xl">🌿</div><h2 className="mt-4 text-xl font-black">السلة فارغة</h2><p className="mt-2 text-slate-500">لا توجد عناصر محذوفة حاليًا.</p></div>}</div></section>
  </>
}
