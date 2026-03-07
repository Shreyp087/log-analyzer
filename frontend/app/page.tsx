import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import AuthEntryPoint from "@/components/AuthEntryPoint";
import { AUTH_TOKEN_COOKIE } from "@/lib/auth";

export default async function HomePage() {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(AUTH_TOKEN_COOKIE)?.value;

  if (sessionToken) {
    redirect("/dashboard");
  }

  return <AuthEntryPoint />;
}
