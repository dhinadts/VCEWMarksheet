import { AppShell } from "@/components/shell/app-shell";import { requireUser } from "@/lib/server-api";
export default async function Layout({children}:{children:React.ReactNode}){const user=await requireUser(["STUDENT"]);return <AppShell user={user}>{children}</AppShell>}
