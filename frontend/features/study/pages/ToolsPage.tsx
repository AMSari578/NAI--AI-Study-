"use client";
import Link from"next/link";
import{ArrowRight}from"lucide-react";
import{studyTools}from"@/lib/studyTools";

export default function ToolsPage(){return <><header><p className="text-sm font-black uppercase tracking-[.16em] text-primary">NAI Study tools</p><h1 className="mt-2 text-3xl font-black md:text-4xl">Choose a study tool</h1><p className="mt-2 text-[#727785]">First choose what you want to do. You will select the subject and lecture on the next page.</p></header><div className="mt-8 grid gap-5 sm:grid-cols-2 xl:grid-cols-4">{studyTools.map(({id,title,text,Icon,color})=><Link key={id} href={`/tools/${id}`} className="card group flex min-h-[250px] flex-col bg-white p-6 transition hover:-translate-y-1 hover:border-primary hover:shadow-md"><span className={`grid h-12 w-12 place-items-center rounded-xl text-white ${color}`}><Icon size={21}/></span><h2 className="mt-5 text-lg font-black">{title}</h2><p className="mt-2 text-sm leading-6 text-[#727785]">{text}</p><span className="mt-auto flex items-center gap-2 pt-5 text-sm font-black text-primary">Choose tool <ArrowRight size={17} className="transition group-hover:translate-x-1"/></span></Link>)}</div></>}

