"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Background,
  BackgroundVariant,
  Controls,
  MarkerType,
  MiniMap,
  Panel,
  ReactFlow,
  useEdgesState,
  useNodesState,
} from "@xyflow/react";
import { Expand, LoaderCircle, Map as MapIcon, Sparkles, Trash2 } from "lucide-react";
import { api, del, post } from "@/lib/api";
import { useLanguage } from "@/lib/i18n";

const palettes = [
  {background:"#3157D5",border:"#3157D5",color:"#fff"},
  {background:"#F1EBFF",border:"#A78BFA",color:"#4C1D95"},
  {background:"#E8F1FF",border:"#93C5FD",color:"#1E3A8A"},
  {background:"#E2F4EF",border:"#6EE7B7",color:"#065F46"},
];

function graphFrom(item:any){
  const rawNodes=item?.data?.nodes||[],rawEdges=item?.data?.edges||[];
  const levels=new Map<number,any[]>();
  rawNodes.forEach((node:any,index:number)=>{const level=Math.max(0,Number(node.level)||0);levels.set(level,[...(levels.get(level)||[]),{...node,index}])});
  const nodes=rawNodes.map((node:any,index:number)=>{
    const level=Math.max(0,Number(node.level)||0),row=levels.get(level)||[],slot=row.findIndex(value=>value.index===index),width=Math.max(1,row.length),palette=palettes[Math.min(level,palettes.length-1)];
    return {
      id:String(node.id),
      position:{x:(slot-(width-1)/2)*300,y:level*205},
      data:{label:<div dir="auto" className="concept-node-content"><b>{node.label}</b>{node.detail&&<p>{node.detail}</p>}</div>},
      style:{width:240,minHeight:88,borderRadius:18,border:`2px solid ${palette.border}`,background:palette.background,color:palette.color,boxShadow:"0 14px 32px rgba(25,20,52,.14)",padding:15},
    };
  });
  const ids=new Set(nodes.map((node:any)=>node.id));
  const edges=rawEdges.filter((edge:any)=>ids.has(String(edge.source))&&ids.has(String(edge.target))).map((edge:any,index:number)=>({id:`edge-${index}`,source:String(edge.source),target:String(edge.target),type:"smoothstep",animated:false,markerEnd:{type:MarkerType.ArrowClosed,color:"#7C3AED"},style:{stroke:"#7C3AED",strokeWidth:2.2}}));
  return {nodes,edges};
}

export default function InteractiveConceptMap({topicId,materialId}:{topicId:number;materialId?:number|null}){
  const{language}=useLanguage();
  const[item,setItem]=useState<any>(),[busy,setBusy]=useState(false),[loading,setLoading]=useState(true),[error,setError]=useState("");
  const initial=useMemo(()=>graphFrom(item),[item]);
  const[nodes,setNodes,onNodesChange]=useNodesState(initial.nodes);
  const[edges,setEdges,onEdgesChange]=useEdgesState(initial.edges);

  useEffect(()=>{setLoading(true);api<any[]>(`/topics/${topicId}/concept-maps`).then(items=>setItem(items[0])).catch((reason:any)=>setError(reason.message)).finally(()=>setLoading(false))},[topicId]);
  useEffect(()=>{setNodes(initial.nodes);setEdges(initial.edges)},[initial,setNodes,setEdges]);

  async function generate(){setBusy(true);setError("");try{setItem(await post("/ai/concept-map",{topic_id:topicId,material_id:materialId||null,language:language==="ar"?"arabic":"english"}))}catch(reason:any){setError(reason.message)}finally{setBusy(false)}}
  async function remove(){if(!item?.id||!confirm(language==="ar"?"حذف خريطة المفاهيم ونقلها إلى سلة المهملات؟":"Move this concept map to trash?"))return;await del(`/concept-maps/${item.id}`);setItem(undefined)}

  return <section className="card bg-white p-5 md:p-6">
    <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-2xl font-black">{language==="ar"?"خريطة المفاهيم التفاعلية":"Interactive concept map"}</h2><p className="mt-1 text-sm text-slate-500">{language==="ar"?"اسحب العقد، حرّك المساحة، واستخدم أدوات التكبير والتصغير.":"Drag nodes, pan the canvas, and use the zoom controls."}</p></div><div className="flex gap-2"><button disabled={busy} onClick={()=>void generate()} className="btn btn-primary"><Sparkles size={17}/>{busy?(language==="ar"?"جارٍ بناء الخريطة...":"Building map..."):(language==="ar"?"إنشاء خريطة جديدة":"Create new map")}</button>{item&&<button onClick={()=>void remove()} className="btn border border-red-200 bg-red-50 text-red-600"><Trash2 size={17}/>{language==="ar"?"حذف":"Delete"}</button>}</div></div>
    {error&&<p className="mt-4 rounded-xl bg-red-50 p-3 text-red-600">{error}</p>}
    {loading?<div className="concept-map-empty"><LoaderCircle className="animate-spin"/>{language==="ar"?"جارٍ تحميل الخريطة...":"Loading map..."}</div>:nodes.length?<div className="concept-flow mt-6"><ReactFlow nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} fitView fitViewOptions={{padding:.25}} minZoom={.15} maxZoom={3} nodesDraggable panOnDrag zoomOnScroll zoomOnPinch zoomOnDoubleClick elementsSelectable><Background variant={BackgroundVariant.Dots} color="#9B87C5" gap={24} size={1.3}/><MiniMap pannable zoomable nodeColor={(node:any)=>String(node.style?.background||"#7C3AED")} maskColor="rgba(20,12,34,.12)"/><Controls showInteractive/><Panel position="top-left" className="concept-hint"><Expand size={14}/>{language==="ar"?"حرّك وكبّر الخريطة":"Move and zoom"}</Panel></ReactFlow></div>:<button onClick={()=>void generate()} className="concept-map-empty w-full"><MapIcon size={42}/><b>{language==="ar"?"لا توجد خريطة بعد":"No concept map yet"}</b><span>{language==="ar"?"اضغط لإنشاء خريطة من معلومات الملف.":"Create a map from the file information."}</span></button>}
  </section>;
}
