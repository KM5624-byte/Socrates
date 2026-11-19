import { notFound } from "next/navigation";
import Workspace, { sections, type Search } from "../workspace";

export default async function SectionPage({ params, searchParams }: {
  params: Promise<{ section: string }>;
  searchParams: Search;
}) {
  const { section } = await params;
  const view = sections.find((item) => item.id === section);
  if (!view) notFound();
  return <Workspace section={view.id} searchParams={searchParams} />;
}
