import { ChatPanel } from "@/components/chat/ChatPanel";

interface ChatPageProps {
  params: Promise<{ indexId: string }>;
}

export default async function ChatPage({ params }: ChatPageProps) {
  const { indexId } = await params;
  return (
    <main className="min-h-dvh">
      <ChatPanel indexId={decodeURIComponent(indexId)} />
    </main>
  );
}
