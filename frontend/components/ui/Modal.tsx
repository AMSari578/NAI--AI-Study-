"use client";
import { X } from "lucide-react";

export default function Modal({open,onClose,title,children}:{open:boolean;onClose:()=>void;title:string;children:React.ReactNode}){
  if(!open)return null;
  return <div className="fixed inset-0 z-50 grid place-items-center bg-ink/40 p-4 backdrop-blur-sm" onMouseDown={onClose}>
    <div role="dialog" aria-modal="true" aria-labelledby="modal-title" className="card w-full max-w-lg bg-white p-6" onMouseDown={event=>event.stopPropagation()}>
      <div className="mb-5 flex items-center justify-between gap-4">
        <h2 id="modal-title" className="text-xl font-black">{title}</h2>
        <button type="button" onClick={onClose} className="icon-button" aria-label="Close dialog" title="Close"><X size={19}/></button>
      </div>
      {children}
    </div>
  </div>;
}
