import Workspace, { type Search } from "./workspace";

export default async function Page({ searchParams }: { searchParams: Search }) {
  return <Workspace searchParams={searchParams} />;
}
