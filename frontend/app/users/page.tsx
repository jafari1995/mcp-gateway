"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff } from "lucide-react";
import { toast } from "sonner";
import { client, type User } from "@/lib/api";
import { isAdmin } from "@/lib/auth";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function UsersPage() {
  const router = useRouter();
  const [users, setUsers] = useState<User[]>([]);
  const [name, setName] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    if (!isAdmin()) {
      router.replace("/");
      return;
    }
    void client
      .users()
      .then(setUsers)
      .catch((err) => toast.error(String(err)));
  }, [router]);

  return (
    <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
      <Card className="overflow-hidden">
        <CardHeader className="border-b bg-secondary/40">
          <p className="text-xs font-semibold text-muted-foreground">مدیریت دسترسی</p>
          <CardTitle>افزودن کاربر</CardTitle>
          <CardDescription className="leading-7">
            کاربر با همین نام کاربری و رمز می‌تواند وارد شود و Gateway خودش را بسازد.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 pt-6">
          <div className="flex flex-col gap-2">
            <Label>نام نمایشی</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="flex flex-col gap-2">
            <Label>نام کاربری</Label>
            <Input value={username} onChange={(e) => setUsername(e.target.value)} />
          </div>
          <div className="flex flex-col gap-2">
            <Label>ایمیل</Label>
            <Input value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="create-user-password">رمز عبور</Label>
            <div className="relative">
              <Input
                id="create-user-password"
                type={showPassword ? "text" : "password"}
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="pe-11"
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute end-1 top-1/2 h-8 w-8 -translate-y-1/2 px-0 text-muted-foreground"
                aria-label={showPassword ? "مخفی کردن رمز" : "نمایش رمز"}
                onClick={() => setShowPassword((v) => !v)}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </Button>
            </div>
          </div>
          <Button
            onClick={() => {
              void (async () => {
                try {
                  await client.createUser({ name, username, email, password, role: "user" });
                  setName("");
                  setUsername("");
                  setEmail("");
                  setPassword("");
                  setShowPassword(false);
                  setUsers(await client.users());
                  toast.success("کاربر ساخته شد — می‌تواند با همین رمز وارد شود");
                } catch (err) {
                  toast.error(err instanceof Error ? err.message : "خطا");
                }
              })();
            }}
          >
            ایجاد کاربر
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>لیست کاربران</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          {users.map((u) => (
            <div key={u.id} className="flex items-center justify-between rounded-lg border px-3 py-2">
              <div>
                <div className="text-sm font-medium">
                  {u.name} <span className="text-muted-foreground">(@{u.username})</span>
                </div>
                <div className="text-xs text-muted-foreground">{u.email}</div>
              </div>
              <Badge variant={u.role === "admin" ? "default" : "secondary"}>
                {u.role === "admin" ? "ادمین" : "کاربر"}
              </Badge>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
