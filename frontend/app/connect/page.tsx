"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { client, type ConnectInfo } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function ConnectPage() {
  const [info, setInfo] = useState<ConnectInfo | null>(null);

  useEffect(() => {
    void client
      .connect()
      .then(setInfo)
      .catch((err) => toast.error(String(err)));
  }, []);

  if (!info) {
    return <p className="text-sm text-muted-foreground">در حال بارگذاری...</p>;
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>اتصال کلاینت AI</CardTitle>
          <CardDescription className="leading-7">{info.hint}</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <code className="rounded-lg border bg-secondary/50 p-3 text-sm">{info.mcp_url}</code>
          <Button
            variant="secondary"
            onClick={() => {
              void navigator.clipboard.writeText(info.mcp_url);
              toast.success("کپی شد");
            }}
          >
            کپی URL
          </Button>
          <ol className="flex list-decimal flex-col gap-2 pr-5 text-sm leading-7 text-muted-foreground">
            <li>وارد حساب خودتان شوید.</li>
            <li>در «Gateway من» toolها را از لیست انتخاب کنید.</li>
            <li>platform token را کپی کنید.</li>
            <li>URL + Bearer token را در Cursor/Claude بگذارید.</li>
          </ol>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>نمونه کانفیگ</CardTitle>
          <CardDescription>به‌جای YOUR_PLATFORM_TOKEN همان token صفحه Gateway را بگذارید.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <pre className="overflow-x-auto rounded-lg border bg-secondary/50 p-4 text-xs leading-relaxed">
            {info.example_cursor_snippet}
          </pre>
          <Button
            onClick={() => {
              void navigator.clipboard.writeText(info.example_cursor_snippet);
              toast.success("کپی شد");
            }}
          >
            کپی snippet
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
