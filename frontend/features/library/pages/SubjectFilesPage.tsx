"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, FileText, LoaderCircle, Plus, RefreshCw, Trash2, UploadCloud } from "lucide-react";
import { api, del, post } from "@/lib/api";
import Modal from "@/components/ui/Modal";
import { dateLocale, useLanguage } from "@/lib/i18n";

export default function SubjectFilesPage({params}:{params:Promise<{id:string}>}){
  const{id}=use(params),router=useRouter(),{language}=useLanguage();
  const[data,setData]=useState<any>(),[open,setOpen]=useState(false),[saving,setSaving]=useState(false),[deleting,setDeleting]=useState<number|null>(null),[processing,setProcessing]=useState<number|null>(null),[error,setError]=useState("");
  const load=()=>api(`/subjects/${id}`).then(setData).catch((reason:any)=>setError(reason.message));
  useEffect(()=>{void load()},[id]);

  async function addFile(event:React.FormEvent<HTMLFormElement>){
    event.preventDefault();
    const form=new FormData(event.currentTarget),file=form.get("file") as File,title=String(form.get("title")||"").trim(),description=String(form.get("description")||"").trim();
    setSaving(true);setError("");
    try{
      const topic:any=await post(`/subjects/${id}/topics`,{title,description});
      const upload=new FormData();upload.append("file",file);
      await post(`/topics/${topic.id}/materials`,upload);
      setOpen(false);await load();
    }catch(reason:any){setError(reason.message)}finally{setSaving(false)}
  }
  async function removeFile(item:any){if(!confirm(`هل تريد نقل ملف «${item.file_name}» إلى سلة المهملات؟`))return;setDeleting(item.id);try{await del(`/materials/${item.id}`);await load()}finally{setDeleting(null)}}
  async function reprocess(item:any){setProcessing(item.id);setError("");try{await post(`/materials/${item.id}/reprocess`,{});await load()}catch(reason:any){setError(reason.message)}finally{setProcessing(null)}}
  async function removeSubject(){if(!confirm(`هل تريد نقل مادة «${data.subject.name}» كاملة إلى سلة المهملات؟`))return;await del(`/subjects/${id}`);router.push("/subjects")}

  if(!data)return <div className="card flex items-center gap-3 bg-white p-6 text-slate-500"><LoaderCircle className="animate-spin text-primary" size={20}/>{error||"جارٍ فتح المادة..."}</div>;
  return <div dir="rtl" className="subject-files-page">
    <Link href="/subjects" className="inline-flex items-center gap-2 text-sm font-black text-primary"><ArrowLeft size={16}/>العودة إلى المكتبة</Link>
    <header className="mt-5 flex flex-wrap items-start justify-between gap-5">
      <div><p className="text-sm font-black text-primary">المادة الدراسية</p><h1 className="mt-2 text-3xl font-black md:text-4xl">{data.subject.name}</h1><p className="mt-2 text-slate-500">{data.subject.description||"ملفات المادة ومحتواها الدراسي."}</p></div>
      <div className="flex flex-wrap gap-2"><button onClick={()=>void removeSubject()} className="btn btn-secondary text-red-600"><Trash2 size={17}/>حذف المادة</button><button onClick={()=>setOpen(true)} className="btn btn-primary"><Plus size={17}/>إضافة ملف</button></div>
    </header>

    <section className="mt-9">
      <div className="flex items-end justify-between"><div><h2 className="text-2xl font-black">ملفات المادة</h2><p className="mt-1 text-sm text-slate-500">افتح أي ملف للانتقال إلى الملخص والاختبار والفلاش كارد وخريطة المفاهيم.</p></div><span className="rounded-full bg-blue-50 px-4 py-2 text-sm font-black text-primary">{data.materials.length} ملفات</span></div>
      {error&&<p className="mt-5 rounded-xl bg-red-50 p-4 text-red-600">{error}</p>}
      <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {data.materials.map((item:any)=><article key={item.id} className="material-library-card group">
          <Link href={`/topics/${item.topic_id}`} className="block min-w-0 flex-1 p-5">
            <div className="flex items-start justify-between"><span className="material-file-icon"><FileText size={25}/></span><ArrowLeft className="material-card-arrow" size={20}/></div>
            <h3 dir="auto" className="mt-6 truncate text-lg font-black">{item.file_name}</h3>
            <p className="mt-2 text-sm text-slate-500">{item.topic_title} · {item.extracted_text?`${item.extracted_text.length.toLocaleString(dateLocale(language))} حرف مقروء`:"قيد القراءة"}</p>
            <div className="mt-5 flex flex-wrap gap-2"><span>✨ ملخص</span><span>🧠 اختبار</span><span>🗂️ فلاش كارد</span></div>
          </Link>
          <button disabled={processing===item.id} onClick={()=>void reprocess(item)} className="material-reprocess" title="إعادة قراءة الملف بعمق"><RefreshCw className={processing===item.id?"animate-spin":""} size={16}/><span>{processing===item.id?"جارٍ القراءة...":"إعادة القراءة"}</span></button>
          <button disabled={deleting===item.id} onClick={()=>void removeFile(item)} className="material-delete"><Trash2 size={17}/></button>
        </article>)}
        {!data.materials.length&&<button onClick={()=>setOpen(true)} className="library-empty md:col-span-2 xl:col-span-3"><UploadCloud size={40}/><b>لا توجد ملفات بعد</b><small>أضف أول ملف لهذه المادة لبدء الدراسة.</small></button>}
      </div>
    </section>

    <Modal open={open} onClose={()=>setOpen(false)} title="إضافة ملف للمادة">
      <form onSubmit={addFile} className="space-y-5" dir="rtl">
        <label className="block text-sm font-black">اسم الملف أو الدرس<input required name="title" className="field mt-2" placeholder="مثال: المحاضرة الأولى"/></label>
        <label className="block text-sm font-black">الوصف<textarea name="description" className="field mt-2" placeholder="وصف مختصر لمحتوى الملف"/></label>
        <label className="block text-sm font-black">رفع الملف<input required name="file" type="file" accept=".pdf,.txt,image/png,image/jpeg,image/webp" className="field mt-2"/><small className="mt-2 block font-normal text-slate-500">PDF أو صورة أو نص، بحد أقصى 15MB.</small></label>
        <button disabled={saving} className="btn btn-primary w-full"><UploadCloud size={18}/>{saving?"جارٍ رفع الملف وقراءته...":"إضافة الملف"}</button>
      </form>
    </Modal>
  </div>
}
