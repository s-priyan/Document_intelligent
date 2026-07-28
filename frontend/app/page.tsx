import { DocumentManager } from "@/components/documents/DocumentManager";

export default function HomePage() {
  return (
    <main className="flex min-h-dvh items-center justify-center px-4 py-10 sm:py-16">
      <DocumentManager />
    </main>
  );
}
