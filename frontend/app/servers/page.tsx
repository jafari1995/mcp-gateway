"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { Trash2 } from "lucide-react";
import { client, type Server, type Tool } from "@/lib/api";
import { isAdmin } from "@/lib/auth";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function ServersPage() {
  const admin = isAdmin();
  const [servers, setServers] = useState<Server[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [tools, setTools] = useState<Tool[]>([]);
  const [name, setName] = useState("");
  const [baseUrl, setBaseUrl] = useState("http://demo-mcp:8100/mcp");
  const [authHeader, setAuthHeader] = useState("");
  const [busy, setBusy] = useState(false);

  const selected = servers.find((s) => s.id === selectedId) || null;

  const refresh = useCallback(async (preferId?: number | null) => {
    const list = await client.servers();
    setServers(list);
    setSelectedId((current) => {
      const want = preferId !== undefined ? preferId : current;
      if (want != null && list.some((s) => s.id === want)) return want;
      return list[0]?.id ?? null;
    });
  }, []);

  useEffect(() => {
    void refresh().catch((err) => toast.error(String(err)));
  }, [refresh]);

  useEffect(() => {
    if (selectedId == null) {
      setTools([]);
      return;
    }
    void client
      .serverTools(selectedId)
      .then(setTools)
      .catch((err) => toast.error(String(err)));
  }, [selectedId]);

  function statusLabel(status: string) {
    if (status === "online") return "آنلاین";
    if (status === "error") return "خطا";
    if (status === "registered") return "ثبت‌شده";
    return status;
  }

  async function addServer() {
    if (!name.trim() || !baseUrl.trim()) {
      toast.error("نام و آدرس را پر کنید");
      return;
    }
    setBusy(true);
    try {
      const server = await client.createServer({
        name: name.trim(),
        base_url: baseUrl.trim(),
        auth_header: authHeader.trim() || null,
      });
      setName("");
      setAuthHeader("");
      await refresh(server.id);
      toast.success(`سرور «${server.name}» اضافه شد`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "افزودن ناموفق بود");
    } finally {
      setBusy(false);
    }
  }

  async function addOrOpenDemo() {
    setBusy(true);
    try {
      const server = await client.createDemoServer();
      await refresh(server.id);
      toast.success(
        servers.some((s) => s.name === "demo-mcp")
          ? "demo-mcp از قبل بود؛ باز شد"
          : "demo-mcp اضافه شد"
      );
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "خطا");
    } finally {
      setBusy(false);
    }
  }

  async function syncSelected() {
    if (!selected) return;
    setBusy(true);
    try {
      const updated = await client.syncServer(selected.id);
      await refresh(updated.id);
      setTools(await client.serverTools(updated.id));
      toast.success("Sync موفق بود");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Sync ناموفق");
      await refresh(selected.id);
    } finally {
      setBusy(false);
    }
  }

  async function removeServer(server: Server) {
    if (!confirm(`سرور «${server.name}» حذف شود؟`)) return;
    setBusy(true);
    try {
      await client.deleteServer(server.id);
      await refresh(null);
      toast.success(`«${server.name}» حذف شد`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "حذف ناموفق بود");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
      <Card>
        <CardHeader>
          <CardTitle>{admin ? "کاتالوگ MCP" : "MCPهای موجود"}</CardTitle>
          <CardDescription className="leading-7">
            {admin
              ? "هر تعداد MCP با نام یکتا می‌توانید اضافه کنید. برای حذف از دکمه سطل زباله استفاده کنید."
              : "این لیست توسط ادمین مدیریت می‌شود. انتخاب tool در صفحه Gateway من است."}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {admin ? (
            <div className="flex flex-col gap-3 rounded-xl border bg-secondary/30 p-3">
              <p className="text-sm font-medium">افزودن MCP جدید</p>
              <div className="flex flex-col gap-2">
                <Label>نام یکتا</Label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="مثلاً notes-prod یا crm"
                />
              </div>
              <div className="flex flex-col gap-2">
                <Label>Base URL</Label>
                <Input
                  className="direction-ltr text-left"
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                  placeholder="http://demo-mcp:8100/mcp"
                />
              </div>
              <div className="flex flex-col gap-2">
                <Label>هدر احراز upstream (اختیاری)</Label>
                <Input
                  className="direction-ltr text-left"
                  value={authHeader}
                  onChange={(e) => setAuthHeader(e.target.value)}
                  placeholder="Bearer sk-..."
                  autoComplete="off"
                />
                <p className="text-xs leading-6 text-muted-foreground">
                  برای MCPهای عمومی که API key می‌خواهند. فقط Gateway به upstream می‌فرستد؛ به کلاینت لو نمی‌رود.
                </p>
              </div>
              <Button disabled={busy} onClick={() => void addServer()}>
                افزودن به کاتالوگ
              </Button>
              <Button disabled={busy} variant="secondary" onClick={() => void addOrOpenDemo()}>
                افزودن / باز کردن demo-mcp
              </Button>
              <p className="text-xs leading-6 text-muted-foreground">
                دکمه demo-mcp فقط یک نمونه آماده است. برای MCPهای بیشتر نام و URL جدید بدهید.
              </p>
            </div>
          ) : null}

          <div className="flex flex-col gap-2">
            {!servers.length ? (
              <p className="text-sm text-muted-foreground">هنوز سروری ثبت نشده است.</p>
            ) : null}
            {servers.map((s) => (
              <div
                key={s.id}
                className={`flex items-stretch gap-2 rounded-lg border p-2 ${
                  selectedId === s.id ? "border-primary bg-secondary" : ""
                }`}
              >
                <button
                  type="button"
                  className="min-w-0 flex-1 px-1 py-1 text-right text-sm"
                  onClick={() => setSelectedId(s.id)}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium">{s.name}</span>
                    <Badge
                      variant={
                        s.status === "online"
                          ? "success"
                          : s.status === "error"
                            ? "danger"
                            : "secondary"
                      }
                    >
                      {statusLabel(s.status)}
                    </Badge>
                  </div>
                  <div className="truncate text-left text-xs text-muted-foreground direction-ltr">
                    {s.base_url}
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">{s.tool_count} tool</div>
                </button>
                {admin ? (
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    className="self-center"
                    disabled={busy}
                    title="حذف"
                    onClick={() => void removeServer(s)}
                  >
                    <Trash2 className="size-4" />
                  </Button>
                ) : null}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-3">
          <div>
            <CardTitle>{selected ? selected.name : "یک MCP انتخاب کنید"}</CardTitle>
            <CardDescription className="leading-7">
              {selected?.last_error
                ? `آخرین خطا: ${selected.last_error}`
                : selected
                  ? selected.base_url
                  : "برای دیدن toolها یک سرور را از لیست انتخاب کنید"}
            </CardDescription>
          </div>
          {admin && selected ? (
            <div className="flex gap-2">
              <Button disabled={busy} variant="secondary" onClick={() => void syncSelected()}>
                Sync ابزارها
              </Button>
              <Button
                disabled={busy}
                variant="destructive"
                onClick={() => void removeServer(selected)}
              >
                حذف سرور
              </Button>
            </div>
          ) : null}
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {tools.map((tool) => (
            <div key={tool.id} className="rounded-lg border px-3 py-2">
              <div className="text-sm font-medium">{tool.name}</div>
              <div className="text-xs text-muted-foreground">
                {tool.description || "بدون توضیح"}
              </div>
            </div>
          ))}
          {selected && !tools.length ? (
            <p className="text-sm text-muted-foreground">
              toolی نیست. {admin ? "Sync را بزنید." : "از ادمین بخواهید Sync کند."}
            </p>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
