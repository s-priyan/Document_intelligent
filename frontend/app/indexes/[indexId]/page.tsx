import { IndexDetail } from "@/components/documents/IndexDetail";
export default async function IndexPage({ params }: { params: Promise<{ indexId: string }> }) {
  const { indexId } = await params;
  return <main className="px-4 py-10 sm:py-16"><IndexDetail indexId={indexId} /></main>;
}
