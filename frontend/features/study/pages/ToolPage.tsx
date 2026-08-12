"use client";
import{use,useEffect,useState}from"react";
import Link from"next/link";
import{useRouter}from"next/navigation";
import{ArrowLeft,ArrowRight,BookOpen}from"lucide-react";
import{api}from"@/lib/api";
import{studyTools}from"@/lib/studyTools";
import StudyMode from"@/features/study/StudyMode";
import SummaryStudio from"@/features/study/SummaryStudio";
import QuizStudio from"@/features/study/QuizStudio";
import FlashcardStudio from"@/features/study/FlashcardStudio";
import ConceptStudio from"@/features/study/ConceptStudio";

const embeddedTools=["study","summary","quiz","flashcards","concept"];

export default function ToolPage({params}:{params:Promise<{tool:string}>}){
  const{tool}=use(params),router=useRouter(),chosen=studyTools.find(item=>item.id===tool);
  const[subjects,setSubjects]=useState<any[]>([]),[subjectId,setSubjectId]=useState(""),[topics,setTopics]=useState<any[]>([]),[topicId,setTopicId]=useState(""),[materials,setMaterials]=useState<any[]>([]),[materialId,setMaterialId]=useState(""),[busy,setBusy]=useState(false),[started,setStarted]=useState(false);
  useEffect(()=>{api("/subjects").then(setSubjects)},[]);
  useEffect(()=>{setTopics([]);setTopicId("");setMaterials([]);setMaterialId("");if(!subjectId)return;setBusy(true);api(`/subjects/${subjectId}`).then((value:any)=>setTopics(value.topics||[])).finally(()=>setBusy(false))},[subjectId]);
  useEffect(()=>{setMaterials([]);setMaterialId("");if(!topicId)return;setBusy(true);api(`/topics/${topicId}`).then((value:any)=>setMaterials(value.materials||[])).finally(()=>setBusy(false))},[topicId]);
  if(!chosen)return <div className="card p-8"><h1 className="text-2xl font-black">Tool not found</h1><Link href="/tools" className="mt-4 inline-block font-bold text-primary">Back to tools</Link></div>;
  const Icon=chosen.Icon,needsMaterial=chosen.id==="study"||chosen.id==="tutor";
  function start(){if(!topicId)return;if(embeddedTools.includes(chosen!.id))setStarted(true);else router.push(`/topics/${topicId}?tab=${chosen!.tab}`)}
  const selectedMaterial=materialId?Number(materialId):null;
  const workspace=chosen.id==="study"?<StudyMode topicId={Number(topicId)} materialId={selectedMaterial}/>:chosen.id==="summary"?<SummaryStudio topicId={Number(topicId)} materialId={selectedMaterial}/>:chosen.id==="quiz"?<QuizStudio topicId={Number(topicId)} materialId={selectedMaterial}/>:chosen.id==="concept"?<ConceptStudio topicId={Number(topicId)} materialId={selectedMaterial}/>:<FlashcardStudio topicId={Number(topicId)} materialId={selectedMaterial}/>;
  return <>
    <Link href="/tools" className="inline-flex items-center gap-2 text-sm font-bold text-[#727785]"><ArrowLeft size={16}/>All study tools</Link>
    <header className="mt-6 flex items-center gap-4"><span className={`grid h-14 w-14 place-items-center rounded-2xl text-white shadow-md ${chosen.color}`}><Icon size={25}/></span><div><h1 className="text-3xl font-black">{chosen.title}</h1><p className="mt-1 text-[#727785]">{chosen.text}</p></div></header>
    {!started&&<section className="card mt-8 bg-white p-6 md:p-9"><h2 className="text-xl font-black">Choose your study context</h2><p className="mt-2 text-sm text-[#727785]">Choose the subject, exact lecture, and a specific material when you want NAI Study to focus on one file.</p><div className="mt-7 grid gap-6 md:grid-cols-3"><label className="font-bold"><span className="mb-2 block text-sm text-primary">Step 1</span>Subject<select value={subjectId} onChange={event=>setSubjectId(event.target.value)} className="field mt-2"><option value="">Choose a subject</option>{subjects.map(item=><option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label className="font-bold"><span className="mb-2 block text-sm text-primary">Step 2</span>Lecture / topic<select disabled={!subjectId||busy} value={topicId} onChange={event=>setTopicId(event.target.value)} className="field mt-2"><option value="">Choose a lecture</option>{topics.map(item=><option key={item.id} value={item.id}>{item.title}</option>)}</select></label><label className="font-bold"><span className="mb-2 block text-sm text-primary">Step 3</span>Material<select disabled={!topicId||busy} value={materialId} onChange={event=>setMaterialId(event.target.value)} className="field mt-2"><option value="">Use the whole lecture</option>{materials.map(item=><option key={item.id} value={item.id}>{item.file_name}</option>)}</select></label></div>{topicId&&!busy&&!materials.length&&<div className="mt-6 rounded-xl bg-[#FFF0DE] p-4 text-[#9B4E00]"><BookOpen className="mb-2"/><b>No materials in this lecture yet.</b><p className="mt-1 text-sm">You can still use the topic description and notes, or upload a material first.</p></div>}<button disabled={!topicId||(needsMaterial&&materials.length>0&&!materialId)} onClick={start} className="btn btn-primary mt-7 min-w-52">Continue to {chosen.title}<ArrowRight size={18}/></button></section>}
    {started&&<div className="mt-8">{workspace}</div>}
  </>
}

