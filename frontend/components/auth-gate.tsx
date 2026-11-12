"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { isAuthenticated } from "@/lib/auth";
import { AppShell } from "@/components/app-shell";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const isLogin = pathname === "/login";

  useEffect(() => {
    const authed = isAuthenticated();
    if (!isLogin && !authed) {
      router.replace("/login");
      return;
    }
    if (isLogin && authed) {
      router.replace("/");
      return;
    }
    setReady(true);
  }, [isLogin, pathname, router]);

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">
        در حال بررسی نشست...
      </div>
    );
  }

  if (isLogin) return <>{children}</>;
  return <AppShell>{children}</AppShell>;
}
