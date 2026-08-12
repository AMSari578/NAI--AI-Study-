"use client";

import { use } from "react";
import TopicWorkspace from "@/features/study/TopicWorkspace";

export default function TopicPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <TopicWorkspace topicId={Number(id)}/>;
}
