import{BookOpenCheck,Brain,FileUp,Layers3,Map,MessageCircle,NotebookPen,Sparkles}from"lucide-react";
export const studyTools=[
  {id:"study",title:"AI Study Tutor",text:"Choose Teach me, Quick review, or Quiz me for this lecture.",Icon:BookOpenCheck,color:"bg-gradient-to-br from-[#2563EB] to-[#7C3AED]",tab:"study"},
  {id:"tutor",title:"Ask NAI",text:"Ask questions and receive an explanation based on your lecture.",Icon:MessageCircle,color:"bg-[#2563EB]",tab:"tutor"},
  {id:"summary",title:"Create summary",text:"Create a simple or detailed summary from your material.",Icon:Sparkles,color:"bg-[#7C3AED]",tab:"summary"},
  {id:"flashcards",title:"Flashcards",text:"Create question-and-answer cards to review your lecture.",Icon:Layers3,color:"bg-[#7C3AED]",tab:"flashcards"},
  {id:"concept",title:"Concept map",text:"Turn the important ideas into a connected visual map.",Icon:Map,color:"bg-[#2563EB]",tab:"concept-map"},
  {id:"quiz",title:"Create quiz",text:"Generate questions and test your understanding.",Icon:Brain,color:"bg-[#F59E0B]",tab:"quiz"}
  ,{id:"materials",title:"Upload materials",text:"Add a PDF, image, or text to a specific lecture.",Icon:FileUp,color:"bg-[#0F766E]",tab:"subjects"}
  ,{id:"notes",title:"Study notes",text:"Open and manage your notes for a chosen lecture.",Icon:NotebookPen,color:"bg-[#64748B]",tab:"notes"}
] as const;

