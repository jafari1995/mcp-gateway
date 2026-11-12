"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Cable, LayoutDashboard, LogOut, Server, Sparkles, Users } from "lucide-react";
import { toast } from "sonner";
import { clearSession, getSessionUser, isAdmin } from "@/lib/auth";
import { client } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const user = getSessionUser();
  const admin = isAdmin();

  const links = [
    { href: "/", label: "نمای کلی", icon: LayoutDashboard },
    { href: "/gateway", label: "Gateway من", icon: Sparkles },
    ...(admin ? [{ href: "/users", label: "کاربران", icon: Users }] : []),
    { href: "/servers", label: admin ? "کاتالوگ MCP" : "لیست MCP", icon: Server },
    { href: "/connect", label: "اتصال", icon: Cable },
  ];

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-8 px-4 py-8 md:px-8">
      <header className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
        <div className="flex flex-col gap-2">
          <p className="text-xs font-semibold text-muted-foreground">سامانهٔ MCP Gateway</p>
          <h1 className="font-serif text-4xl tracking-tight text-foreground md:text-5xl">
            MCP Gateway
          </h1>
          <p className="max-w-xl text-sm leading-7 text-muted-foreground">
            وارد شوید، MCPها را از لیست انتخاب کنید، toolهای مجاز را بسازید و platform token بگیرید.
          </p>
        </div>
        <div className="flex flex-col items-stretch gap-3 md:items-end">
          <nav className="flex flex-wrap gap-2 rounded-xl border bg-card/80 p-1.5 shadow-sm backdrop-blur">
            {links.map(({ href, label, icon: Icon }) => {
              const active = pathname === href || (href !== "/" && pathname.startsWith(href));
              return (
                <Link
                  key={href}
                  href={href}
                  className={cn(
                    "inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors",
                    active
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                  )}
                >
                  <Icon className="size-4" />
                  {label}
                </Link>
              );
            })}
          </nav>
          <div className="flex items-center justify-between gap-3 text-sm text-muted-foreground md:justify-end">
            <span>
              {user?.name} ({user?.role === "admin" ? "ادمین" : "کاربر"}) —{" "}
              <strong className="text-foreground">{user?.username}</strong>
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                void (async () => {
                  try {
                    await client.logout();
                  } catch {
                    /* ignore */
                  }
                  clearSession();
                  toast.success("خارج شدید");
                  router.replace("/login");
                })();
              }}
            >
              <LogOut className="size-4" />
              خروج
            </Button>
          </div>
        </div>
      </header>
      <main>{children}</main>
    </div>
  );
}
