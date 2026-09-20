import { ChatPanel } from "@/components/chat/ChatPanel";

interface ChatPageProps {
  params: Promise<{ indexId: string }>;
  searchParams: Promise<{ question?: string }>;
}

export default async function ChatPage({ params, searchParams }: ChatPageProps) {
  const { indexId } = await params;
  const { question } = await searchParams;
  return (
    <main className="min-h-dvh">
      <ChatPanel key={indexId} indexId={indexId} initialQuestion={question} />
    </main>
  );
}
