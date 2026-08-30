import { redirect } from "next/navigation";
import { requireUser } from "@/lib/server-api";
export default async function Dashboard(){const user=await requireUser();redirect(`/${user.user_type.toLowerCase()}`)}
