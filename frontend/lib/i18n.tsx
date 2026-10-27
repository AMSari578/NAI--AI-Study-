"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";

export type AppLanguage = "ar" | "en";

const ar: Record<string, string> = {
  "Dashboard":"الرئيسية","Subjects":"المواد","Library":"المكتبة","Summaries":"الملخصات","Tests":"الاختبارات","Review":"المراجعة","Ask the teacher":"اسأل المدرس","Trash":"سلة المهملات",
  "Progress":"التقدم","Planner":"المخطط الدراسي","Calendar":"التقويم","Search":"البحث","Focus":"التركيز","Mock exam":"اختبار تجريبي",
  "Reminders":"التذكيرات","Settings":"الإعدادات","Log out":"تسجيل الخروج","Study space":"مساحة الدراسة","Plan and improve":"خطط وتطور",
  "Learn with clarity":"تعلّم بوضوح","Open navigation":"فتح القائمة","Close navigation":"إغلاق القائمة","Language":"اللغة",
  "Welcome back":"مرحبًا بعودتك","Begin your journey":"ابدأ رحلتك","Create your account":"أنشئ حسابك","Continue learning":"تابع التعلّم",
  "Build your private study space.":"أنشئ مساحتك الدراسية الخاصة.","Sign in to your NAI Study workspace.":"سجّل الدخول إلى مساحة NAI Study.",
  "Full name":"الاسم الكامل","Email address":"البريد الإلكتروني","Password":"كلمة المرور","Please wait...":"يرجى الانتظار...",
  "Create account":"إنشاء حساب","Log in":"تسجيل الدخول","Already have an account?":"لديك حساب بالفعل؟","New here?":"مستخدم جديد؟",
  "Create one":"أنشئ حسابًا","Understand every lecture":"افهم كل محاضرة","Study with intelligent tools":"ذاكر بأدوات ذكية",
  "Plan and track your progress":"خطط وتابع تقدمك","Study clearly.":"ذاكر بوضوح.","Grow confidently.":"وتقدّم بثقة.",
  "Your intelligent learning space for understanding, reviewing, and planning every subject.":"مساحتك الذكية لفهم كل مادة ومراجعتها والتخطيط لها.",
  "Your AI-powered study companion":"رفيقك الدراسي المدعوم بالذكاء الاصطناعي",
  "Daily tasks":"مهام اليوم","View all tasks":"عرض كل المهام","Add task":"إضافة مهمة","No due date":"بلا موعد",
  "Chat with NAI Study":"تحدث مع NAI Study","New chat":"محادثة جديدة","Open full chat":"فتح المحادثة الكاملة",
  "Recently studied":"آخر ما تمت دراسته","Updates automatically":"تتحدث تلقائيًا","Latest materials":"أحدث الملفات","Start a conversation":"ابدأ محادثة",
  "Choose a lecture first":"اختر محاضرة أولًا","NAI Study is thinking...":"NAI Study يفكر...","Preparing your study space...":"جارٍ تجهيز مساحتك الدراسية...",
  "Continue studying":"تابع الدراسة","Choose your first lecture":"اختر محاضرتك الأولى","Open subjects":"فتح المواد","Continue":"متابعة","Today":"اليوم",
  "Upcoming reminders":"التذكيرات القادمة","Upcoming exams":"الاختبارات القادمة","Topics needing review":"مواضيع تحتاج مراجعة",
  "No upcoming reminders.":"لا توجد تذكيرات قادمة.","No upcoming exams.":"لا توجد اختبارات قادمة.","No weak topics identified yet.":"لم يتم تحديد مواضيع ضعيفة بعد.",
  "Flashcards due today":"بطاقات مستحقة اليوم","You're caught up.":"أنجزت كل شيء.","No flashcards are due now.":"لا توجد بطاقات مستحقة الآن.",
  "Overview":"نظرة عامة","Materials":"الملفات","Tutor":"المعلم الذكي","Summary":"الملخص","Flashcards":"البطاقات التعليمية","Concept Map":"خريطة المفاهيم","Quiz":"الاختبار","Notes":"الملاحظات",
  "What would you like to study?":"ماذا تريد أن تدرس؟","Every tool uses this lecture, its materials, and your private notes as context.":"تستخدم كل أداة هذه المحاضرة وملفاتها وملاحظاتك الخاصة كسياق.",
  "Ask NAI":"اسأل NAI","Create summary":"إنشاء ملخص","Review flashcards":"مراجعة البطاقات","Concept map":"خريطة المفاهيم","Test yourself":"اختبر نفسك","Study notes":"ملاحظات الدراسة",
  "Open files and text saved for this lecture":"افتح الملفات والنصوص المحفوظة للمحاضرة","Study with your AI tutor":"تعلّم مع معلمك الذكي",
  "Generate a focused study summary":"أنشئ ملخصًا دراسيًا مركزًا","Remember ideas with active recall":"تذكر الأفكار بالاسترجاع النشط",
  "Connect the important lesson ideas":"اربط أفكار الدرس المهمة","Create questions and check understanding":"أنشئ أسئلة واختبر فهمك","Write and improve your notes":"اكتب ملاحظاتك وحسّنها",
  "Saved materials":"الملفات المحفوظة","Add a PDF, image, or text to begin.":"أضف PDF أو صورة أو نصًا للبدء.","Text extracted":"تم استخراج النص",
  "Ready for visual analysis":"جاهز للتحليل البصري","Upload PDF, image, or text":"رفع PDF أو صورة أو نص","Processing your file...":"جارٍ معالجة الملف...",
  "Add text":"إضافة نص","Text title":"عنوان النص","Paste your notes or a textbook paragraph here...":"الصق ملاحظاتك أو فقرة من الكتاب هنا...","Save text":"حفظ النص",
  "Your personal tutor":"معلمك الشخصي","Uses this lecture and your private notes":"يستخدم هذه المحاضرة وملاحظاتك الخاصة","Start a study session":"ابدأ جلسة دراسية",
  "NAI Study is answering...":"NAI Study يجيب...","New note":"ملاحظة جديدة","Note title":"عنوان الملاحظة","Save note":"حفظ الملاحظة","Saving...":"جارٍ الحفظ...",
  "Create a study summary":"إنشاء ملخص دراسي","NAI Study uses only the context you selected.":"يستخدم NAI Study السياق الذي اخترته فقط.","Mode":"النوع",
  "Simple — main ideas":"بسيط — الأفكار الرئيسية","Medium — balanced":"متوسط — المفاهيم والتفاصيل المهمة","Detailed — comprehensive":"شامل — كل ما ورد في الملف","Key points":"النقاط المهمة","Exam review":"مراجعة للاختبار","What to memorize":"ما يجب حفظه",
  "English":"الإنجليزية","Arabic":"العربية","Creating...":"جارٍ الإنشاء...","NAI Study is reading your material...":"يقرأ NAI Study المادة بعمق...",
  "Copied":"تم النسخ","Copy":"نسخ","Choose a language and summary mode, then create your summary.":"اختر اللغة ونوع الملخص ثم اضغط إنشاء.",
  "Saved summaries":"الملخصات المحفوظة","Your summaries remain available until you delete them.":"تبقى ملخصاتك محفوظة حتى تحذفها.","No saved summaries yet.":"لا توجد ملخصات محفوظة بعد.","Delete":"حذف",
  "Question type":"نوع الأسئلة","Multiple choice":"اختيار من متعدد","True / False":"صح أو خطأ","Short answer / Essay":"إجابة قصيرة / مقالية","Questions":"عدد الأسئلة",
  "Preparing...":"جارٍ الإعداد...","Create quiz":"إنشاء اختبار","Question":"السؤال","Correct concepts":"المفاهيم الصحيحة","Missing concepts":"المفاهيم الناقصة",
  "Suggested answer:":"الإجابة المقترحة:","Answers stay editable until submission.":"يمكنك تغيير الإجابات حتى التسليم.","Submit all answers":"تسليم جميع الإجابات","Correct:":"الصحيح:",
  "Create manually or generate from your selected context.":"أنشئ بطاقة يدويًا أو ولّدها من المحتوى المحدد.","Manual card":"بطاقة يدوية","Generate with AI":"توليد بالذكاء الاصطناعي",
  "Front / question":"الوجه الأمامي / السؤال","Back / answer":"الوجه الخلفي / الإجابة","Save card":"حفظ البطاقة","Answer":"الإجابة","Previous":"السابق","Next":"التالي",
  "again":"إعادة","hard":"صعب","good":"جيد","easy":"سهل","Create your first flashcard when you are ready.":"أنشئ أول بطاقة تعليمية عندما تكون جاهزًا.",
  "Zoom, pan, and explore the important ideas from your selected context.":"كبّر وصغّر وتجوّل لاستكشاف الأفكار المهمة.","Building map...":"جارٍ بناء الخريطة...","Create map":"إنشاء الخريطة","Create a map when you are ready.":"أنشئ خريطة مفاهيم عندما تكون جاهزًا.",
  "Loading subject...":"جارٍ تحميل المادة...","New lecture":"محاضرة جديدة","Lectures":"المحاضرات","Quizzes":"الاختبارات",
  "Generated quizzes":"الاختبارات المنشأة","Study materials":"المواد الدراسية","Add lecture":"إضافة محاضرة","Lecture title":"عنوان المحاضرة","Short description":"وصف مختصر","Create study space":"إنشاء مساحة الدراسة",
  "Subjects /":"المواد /","Everything for this subject in one study space.":"كل ما يخص هذه المادة في مساحة دراسية واحدة.","No lectures yet. Add your first lecture to begin.":"لا توجد محاضرات بعد. أضف أول محاضرة للبدء.",
  "Open":"فتح","Loading your mistakes...":"جارٍ تحميل أخطائك...","Marked for review":"محدد للمراجعة","Done":"تم","No quiz mistakes waiting":"لا توجد أخطاء اختبار بانتظارك",
  "Incorrect answers will appear here.":"ستظهر الإجابات الخاطئة هنا.","Create a quiz":"إنشاء اختبار","Your answer":"إجابتك","Expected idea":"الإجابة الصحيحة","Review mistakes":"مراجعة الأخطاء",
  "Your progress":"تقدمك","Learning progress":"تقدم التعلّم","Topic strengths":"مستوى المواضيع","Topics studied":"المواضيع المدروسة","Minutes studied":"دقائق الدراسة","Study sessions":"جلسات الدراسة",
  "Loading...":"جارٍ التحميل...","Unable to complete the request":"تعذر إكمال الطلب","Cancel":"إلغاء","Close":"إغلاق","Save":"حفظ","Add":"إضافة","Edit":"تعديل",
  "Choose a lecture to begin":"اختر محاضرة للبدء","Choose one of your recent lectures from the list.":"اختر إحدى محاضراتك الأخيرة من القائمة.",
  "Ask NAI Study about this lecture...":"اسأل NAI Study عن هذه المحاضرة...","You":"أنت","NAI Study AI":"ذكاء NAI Study",
  "Rate your recall":"قيّم مدى تذكرك","Click to reveal":"اضغط لإظهار الإجابة","Again":"إعادة","Hard":"صعب","Good":"جيد","Easy":"سهل",
  "cards ready for review":"بطاقات جاهزة للمراجعة","flashcards due":"بطاقات مستحقة","upcoming exams":"اختبارات قادمة",
  "Browse results by subject and open the lecture where they were created.":"تصفح النتائج حسب المادة وافتح المحاضرة التي أُنشئت فيها.",
  "View results":"عرض النتائج","No subjects found yet.":"لا توجد مواد حتى الآن.","Result category not found.":"فئة النتائج غير موجودة.",
  "Choose a study tool":"اختر أداة دراسية","First choose what you want to do. You will select the subject and lecture on the next page.":"اختر أولًا ما تريد فعله، ثم حدد المادة والمحاضرة في الصفحة التالية.",
  "Choose tool":"اختيار الأداة","Tool not found":"الأداة غير موجودة","Back to tools":"العودة للأدوات","All study tools":"كل أدوات الدراسة",
  "Choose your study context":"اختر سياق الدراسة","Choose the subject, exact lecture, and a specific material when you want NAI Study to focus on one file.":"اختر المادة والمحاضرة والملف المحدد الذي تريد أن يركز عليه NAI Study.",
  "Step 1":"الخطوة 1","Step 2":"الخطوة 2","Step 3":"الخطوة 3","Subject":"المادة","Lecture / topic":"المحاضرة / الموضوع","Material":"الملف",
  "Choose a subject":"اختر مادة","Choose a lecture":"اختر محاضرة","Use the whole lecture":"استخدم المحاضرة كاملة","No materials in this lecture yet.":"لا توجد ملفات في هذه المحاضرة بعد.",
  "You can still use the topic description and notes, or upload a material first.":"يمكنك استخدام وصف الموضوع والملاحظات أو رفع ملف أولًا.",
  "Focus mode":"وضع التركيز","Reduce distractions":"قلّل المشتتات","Duration":"المدة","Whole lecture":"المحاضرة كاملة","Start focus session":"بدء جلسة التركيز","Finish":"إنهاء",
  "No notes for this lecture.":"لا توجد ملاحظات لهذه المحاضرة.","Open selected material":"فتح الملف المحدد","Distraction-free study session":"جلسة دراسة بلا مشتتات",
  "Daily review":"المراجعة اليومية","Review center":"مركز المراجعة","Nothing manually marked for review.":"لا يوجد شيء محدد يدويًا للمراجعة.",
  "What do you want to review?":"ماذا تريد أن تراجع؟","Study this mistake with NAI Study":"راجع هذا الخطأ مع NAI Study","NAI Study tutor":"معلم NAI Study",
  "See what is going well and what needs another review.":"شاهد ما أتقنته وما يحتاج إلى مراجعة إضافية.","Study a topic to begin tracking useful progress.":"ادرس موضوعًا ليبدأ تتبع تقدمك.",
  "Study note":"ملاحظة دراسية","Opening note...":"جارٍ فتح الملاحظة...","Bold":"عريض","Italic":"مائل","Highlight":"تمييز","Bullets":"نقاط","Numbered list":"قائمة مرقمة","Checklist":"قائمة تحقق","Table":"جدول","Link":"رابط","Paragraph":"فقرة","Heading":"عنوان","Subheading":"عنوان فرعي",
  "Summarize":"تلخيص","Organize":"تنظيم","Explain":"شرح","NAI Study + Notes":"NAI Study والملاحظات",
  "No readable text is available for this page.":"لا يوجد نص قابل للقراءة في هذه الصفحة.","Open selectable page text":"فتح نص الصفحة القابل للتحديد","Selected text":"النص المحدد","Clear selection":"إلغاء التحديد","Explain this page":"اشرح هذه الصفحة","Summarize this page":"لخص هذه الصفحة","What should I memorize?":"ماذا يجب أن أحفظ؟","Ask about this page...":"اسأل عن هذه الصفحة...","NAI Study is working with this context...":"يعمل NAI Study على هذا السياق...",
  "Study library":"مكتبتك الدراسية","All your subjects, lessons, and generated content in one place.":"كل موادك ودروسك والمحتوى الذي أنشأته في مكان واحد.",
  "Add subject":"إضافة مادة","All subjects":"جميع المواد","Updates automatically when you add a lesson or file.":"تتحدث تلقائيًا عند إضافة درس أو ملف جديد.",
  "Start by adding your first subject":"ابدأ بإضافة أول مادة","Create the subject, then add its lessons and files.":"أنشئ المادة ثم أضف الدروس والملفات الخاصة بها.",
  "Add a new subject":"إضافة مادة جديدة","Subject name":"اسم المادة","Brief description":"وصف مختصر","What will you study in this subject?":"ماذا ستدرس في هذه المادة؟",
  "Subject file":"ملف المادة","PDF, image, or text file, up to 15MB.":"PDF أو صورة أو ملف نصي، بحد أقصى 15MB.","Choose an icon":"اختر أيقونة","Choose a subject color":"اختر لون المادة",
  "The subject will appear with this icon and color.":"ستظهر المادة بهذه الأيقونة واللون.","Save subject and upload file":"حفظ المادة ورفع الملف","Creating the subject and reading the file...":"جارٍ إنشاء المادة وقراءة الملف...",
  "Study subject":"المادة الدراسية","Subject files and study content.":"ملفات المادة ومحتواها الدراسي.","Back to library":"العودة إلى المكتبة","Delete subject":"حذف المادة","Add file":"إضافة ملف",
  "Subject files":"ملفات المادة","Open any file to create summaries, quizzes, flashcards, and concept maps.":"افتح أي ملف للانتقال إلى الملخص والاختبار والفلاش كارد وخريطة المفاهيم.",
  "No files yet":"لا توجد ملفات بعد","Add the first file to start studying.":"أضف أول ملف لهذه المادة لبدء الدراسة.","Add a file to the subject":"إضافة ملف للمادة","File or lesson name":"اسم الملف أو الدرس","File description":"وصف مختصر لمحتوى الملف","Upload file":"رفع الملف","Uploading and reading the file...":"جارٍ رفع الملف وقراءته...",
  "Create a simple, medium, or comprehensive summary":"أنشئ ملخصًا بسيطًا أو متوسطًا أو شاملًا","Test your understanding using the file content":"اختبر فهمك بأسئلة من محتوى الملف","Concept maps":"خرائط المفاهيم","Connect the most important ideas in an interactive map":"اربط أهم الأفكار في خريطة تفاعلية","Chat with the AI teacher about this file":"تحدث مع المدرس الذكي حول هذا الملف",
};

const englishByArabic = new Map(Object.entries(ar).map(([english, arabic]) => [arabic, english]));

const I18nContext = createContext<{language:AppLanguage;setLanguage:(language:AppLanguage)=>void;toggle:()=>void;t:(text:string)=>string;isRtl:boolean}>({language:"ar",setLanguage:()=>{},toggle:()=>{},t:(text)=>text,isRtl:true});

function translateDynamic(text: string): string {
  const exact = ar[text.trim()];
  if (exact) return text.replace(text.trim(), exact);
  return text
    .replace(/(\d+) pending/g, "$1 قيد الانتظار")
    .replace(/(\d+) completed/g, "$1 مكتملة")
    .replace(/(\d+) saved/g, "$1 محفوظ")
    .replace(/(\d+) questions/g, "$1 أسئلة")
    .replace(/(\d+) materials/g, "$1 ملفات")
    .replace(/(\d+) lectures/g, "$1 محاضرات")
    .replace(/Last studied /g, "آخر دراسة: ")
    .replace(/Question (\d+)/g, "السؤال $1");
}

function translateToEnglish(text:string):string{
  const trimmed=text.trim();
  const exact=englishByArabic.get(trimmed);
  if(exact)return text.replace(trimmed,exact);
  return text
    .replace(/(\d+) مواد/g,"$1 subjects")
    .replace(/(\d+) دروس/g,"$1 lessons")
    .replace(/(\d+) ملفات/g,"$1 files")
    .replace(/(\d+) ملخصات/g,"$1 summaries")
    .replace(/(\d+) أسئلة/g,"$1 questions")
    .replace(/حرف مقروء/g,"readable characters")
    .replace(/قيد القراءة/g,"processing");
}

function LegacyTranslator({language}:{language:AppLanguage}) {
  const originalsRef=useRef(new Map<Text,string>());
  const attributeOriginalsRef=useRef(new Map<Element,Map<string,string>>());
  useEffect(()=>{
    const originals=originalsRef.current;
    const attributeOriginals=attributeOriginalsRef.current;
    const translateText=(textNode:Text)=>{
      const parent=textNode.parentElement;
      if(!parent||["SCRIPT","STYLE","CODE","PRE"].includes(parent.tagName)) return;
      if(!originals.has(textNode)) originals.set(textNode,textNode.data);
      const original=originals.get(textNode)!;
      const next=language==="ar"?translateDynamic(original):translateToEnglish(original);
      if(textNode.data!==next) textNode.data=next;
    };
    const translateNode = (root: Node) => {
      if(root.nodeType===Node.TEXT_NODE) translateText(root as Text);
      const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
      let node: Node|null;
      while((node=walker.nextNode())) translateText(node as Text);
      const elements=root instanceof Element?[root,...Array.from(root.querySelectorAll("*"))]:[];
      for(const element of elements){
        for(const name of ["placeholder","aria-label","title"]){
          const value=element.getAttribute(name); if(!value) continue;
          let map=attributeOriginals.get(element); if(!map){map=new Map();attributeOriginals.set(element,map)}
          if(!map.has(name)) map.set(name,value);
          const original=map.get(name)!; const next=language==="ar"?translateDynamic(original):translateToEnglish(original);
          if(value!==next) element.setAttribute(name,next);
        }
      }
    };
    translateNode(document.body);
    const observer=new MutationObserver(records=>records.forEach(record=>{
      if(record.type==="characterData") translateText(record.target as Text);
      record.addedNodes.forEach(node=>translateNode(node));
    }));
    observer.observe(document.body,{childList:true,characterData:true,subtree:true});
    return()=>observer.disconnect();
  },[language]);
  return null;
}

export function LanguageProvider({children}:{children:React.ReactNode}){
  const[language,setLanguageState]=useState<AppLanguage>("ar");
  useEffect(()=>{const saved=localStorage.getItem("nai_language");if(saved==="en"||saved==="ar")setLanguageState(saved)},[]);
  const setLanguage=useCallback((value:AppLanguage)=>{setLanguageState(value);localStorage.setItem("nai_language",value)},[]);
  useEffect(()=>{document.documentElement.lang=language;document.documentElement.dir=language==="ar"?"rtl":"ltr"},[language]);
  const value=useMemo(()=>({language,setLanguage,toggle:()=>setLanguage(language==="ar"?"en":"ar"),t:(text:string)=>language==="ar"?translateDynamic(text):text,isRtl:language==="ar"}),[language,setLanguage]);
  return <I18nContext.Provider value={value}><LegacyTranslator language={language}/>{children}</I18nContext.Provider>;
}

export const useLanguage=()=>useContext(I18nContext);
