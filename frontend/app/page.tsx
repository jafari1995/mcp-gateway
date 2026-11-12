"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { client, type Overview } from "@/lib/api";
import { isAdmin } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function OverviewPage() {
  const [data, setData] = useState<Overview | null>(null);
  const admin = isAdmin();

  useEffect(() => {
    void client
      .overview()
      .then(setData)
      .catch((err) => toast.error(err instanceof Error ? err.message : "خطا"));
  }, []);

  if (!data) {
    return <p className="text-sm text-muted-foreground">در حال بارگذاری...</p>;
  }

  const stats = admin
    ? [
        { label: "کاربران", value: data.users },
        { label: "Tokenهای فعال", value: data.tokens_active },
        { label: "MCP serverها", value: data.servers },
        { label: "Toolها", value: data.tools },
      ]
    : [
        { label: "Tokenهای من", value: data.tokens_active },
        { label: "MCPهای موجود", value: data.servers },
        { label: "Toolهای قابل انتخاب", value: data.tools },
      ];

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>
            سلام {data.me?.name || ""}
          </CardTitle>
          <CardDescription className="leading-7">
            {admin
              ? "به‌عنوان ادمین می‌توانید کاربر بسازید، کاتالوگ MCP را مدیریت کنید، و Sync بگیرید."
              : "به‌عنوان کاربر، از صفحهٔ Gateway من، MCP/toolها را انتخاب کنید و token بگیرید."}
          </CardDescription>
        </CardHeader>
      </Card>

      <div className={`grid gap-4 ${admin ? "sm:grid-cols-2 lg:grid-cols-4" : "sm:grid-cols-3"}`}>
        {stats.map((s) => (
          <Card key={s.label}>
            <CardHeader>
              <CardDescription>{s.label}</CardDescription>
              <CardTitle className="font-serif text-4xl">{s.value}</CardTitle>
            </CardHeader>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>شروع سریع</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          {admin ? (
            <>
              <Button asChild variant="secondary">
                <Link href="/users">ساخت کاربر</Link>
              </Button>
              <Button asChild variant="secondary">
                <Link href="/servers">ثبت / Sync مربوط به MCP</Link>
              </Button>
            </>
          ) : null}
          <Button asChild>
            <Link href="/gateway">ساخت Gateway من</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/connect">راهنمای اتصال</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
