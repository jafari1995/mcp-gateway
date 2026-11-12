"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { client } from "@/lib/api";
import { setSession } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      const res = await client.login(username.trim(), password);
      setSession(res.session_token, res.user);
      toast.success(`خوش آمدید ${res.user.name}`);
      router.replace("/");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "ورود ناموفق بود");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-md items-center px-4">
      <Card className="w-full overflow-hidden">
        <CardHeader className="border-b bg-secondary/40">
          <p className="text-xs font-semibold text-muted-foreground">ورود به سامانه</p>
          <CardTitle className="font-serif text-3xl">MCP Gateway</CardTitle>
          <CardDescription className="leading-7">
            هر کاربر با نام کاربری و رمز خودش وارد می‌شود و Gateway اختصاصی‌اش را می‌سازد.
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-6">
          <form className="flex flex-col gap-4" onSubmit={(e) => void onSubmit(e)}>
            <div className="flex flex-col gap-2">
              <Label htmlFor="username">نام کاربری</Label>
              <Input
                id="username"
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="password">رمز عبور</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <Button type="submit" size="lg" disabled={busy}>
              {busy ? "در حال ورود..." : "ورود"}
            </Button>
            <p className="text-xs leading-6 text-muted-foreground">
              ادمین پیش‌فرض: <code>admin</code> / <code>dev-admin-key</code>
              <br />
              کاربر عادی را ادمین می‌سازد؛ بعد همان کاربر با رمز خودش وارد می‌شود.
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
