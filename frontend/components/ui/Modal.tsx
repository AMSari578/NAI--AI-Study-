"use client";
import { X } from "lucide-react";

export default function Modal({open,onClose,title,children}:{open:boolean;onClose:()=>void;title:string;children:React.ReactNode}){
  if(!open)return null;
  return <div className="fixed inset-0 z-50 overflow-y-auto overscroll-contain bg-ink/40 p-4 backdrop-blur-sm" onMouseDown={onClose}>
    <div role="dialog" aria-modal="true" aria-labelledby="modal-title" className="card mx-auto my-2 max-h-[calc(100dvh-1rem)] w-full max-w-lg overflow-y-auto overscroll-contain bg-white p-6 sm:my-4 sm:max-h-[calc(100dvh-2rem)]" onMouseDown={event=>event.stopPropagation()}>
      <div className="sticky top-0 z-10 -mx-6 -mt-6 mb-5 flex items-center justify-between gap-4 border-b border-slate-100 bg-white px-6 pb-4 pt-6">
        <h2 id="modal-title" className="text-xl font-black">{title}</h2>
        <button type="button" onClick={onClose} className="icon-button" aria-label="Close dialog" title="Close"><X size={19}/></button>
      </div>
      {children}
    </div>
  </div>;
}
