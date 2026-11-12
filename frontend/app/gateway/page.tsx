"use client";

import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { client, type Token, type Tool } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";

export default function MyGatewayPage() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [selected, setSelected] = useState<Record<number, boolean>>({});
  const [label, setLabel] = useState("my-gateway");
  const [tokens, setTokens] = useState<Token[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [rawToken, setRawToken] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function refresh() {
    const [catalog, mine] = await Promise.all([client.catalogTools(), client.myTokens()]);
    setTools(catalog);
    setTokens(mine);
  }

  useEffect(() => {
    void refresh().catch((err) => toast.error(String(err)));
  }, []);

  const grouped = useMemo(() => {
    const map = new Map<string, Tool[]>();
    for (const tool of tools) {
      const key = tool.server_name || `server-${tool.server_id}`;
      const list = map.get(key) || [];
      list.push(tool);
      map.set(key, list);
    }
    return Array.from(map.entries());
  }, [tools]);

  const selectedIds = Object.entries(selected)
    .filter(([, on]) => on)
    .map(([id]) => Number(id));

  const editingToken = tokens.find((t) => t.id === editingId) || null;
  const isEditing = editingToken != null && !editingToken.revoked_at;

  function resetCreateMode() {
    setEditingId(null);
    setSelected({});
    setLabel("my-gateway");
    setRawToken(null);
  }

  async function startEdit(token: Token) {
    if (token.revoked_at) {
      toast.error("token باطل‌شده قابل ویرایش نیست");
      return;
    }
    setBusy(true);
    try {
      const grants = await client.myGrants(token.id);
      const next: Record<number, boolean> = {};
      for (const tool of grants) {
        if (tool.granted) next[tool.id] = true;
      }
      setSelected(next);
      setLabel(token.label);
      setEditingId(token.id);
      setRawToken(null);
      toast.message(`در حال ویرایش: ${token.label}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "بارگذاری grantها ناموفق بود");
    } finally {
      setBusy(false);
    }
  }

  function toggleServer(serverTools: Tool[], on: boolean) {
    setSelected((prev) => {
      const next = { ...prev };
      for (const tool of serverTools) next[tool.id] = on;
      return next;
    });
  }

  async function save() {
    if (selectedIds.length === 0) {
      toast.error("حداقل یک tool انتخاب کنید");
      return;
    }
    setBusy(true);
    try {
      if (isEditing && editingId != null) {
        await client.setMyGrants(editingId, selectedIds);
        await refresh();
        toast.success("toolهای Gateway به‌روز شد");
      } else {
        const token = await client.buildGateway({
          label: label || "my-gateway",
          tool_ids: selectedIds,
        });
        setRawToken(token.raw_token || null);
        setEditingId(token.id);
        await refresh();
        toast.success("Gateway شما ساخته شد");
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "ذخیره ناموفق بود");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-3">
          <div>
            <CardTitle>{isEditing ? "ویرایش Gateway" : "ساخت Gateway من"}</CardTitle>
            <CardDescription className="leading-7">
              {isEditing
                ? `toolهای token «${editingToken.label}» را کم یا زیاد کنید. خودِ token عوض نمی‌شود.`
                : "از کاتالوگ MCP، toolها را انتخاب کنید و یک platform token بسازید."}
            </CardDescription>
          </div>
          {isEditing ? (
            <Button variant="outline" disabled={busy} onClick={resetCreateMode}>
              ساخت جدید
            </Button>
          ) : null}
        </CardHeader>
        <CardContent className="flex flex-col gap-5">
          {isEditing ? (
            <div className="rounded-xl border bg-secondary/40 px-3 py-2 text-sm leading-7">
              در حال ویرایش: <span className="font-medium">{editingToken.label}</span>{" "}
              <span className="text-muted-foreground">({editingToken.token_prefix}…)</span>
            </div>
          ) : (
            <div className="flex flex-col gap-2 md:max-w-sm">
              <Label>برچسب token</Label>
              <Input value={label} onChange={(e) => setLabel(e.target.value)} />
            </div>
          )}

          {!grouped.length ? (
            <p className="text-sm text-muted-foreground">
              هنوز toolی در کاتالوگ نیست. ادمین باید MCP را ثبت و Sync کند.
            </p>
          ) : (
            grouped.map(([serverName, serverTools]) => {
              const allOn = serverTools.every((t) => selected[t.id]);
              const someOn = serverTools.some((t) => selected[t.id]);
              return (
                <div key={serverName} className="rounded-xl border p-4">
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <h3 className="font-medium">{serverName}</h3>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary">
                        {serverTools.filter((t) => selected[t.id]).length}/{serverTools.length}
                      </Badge>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => toggleServer(serverTools, !allOn)}
                      >
                        {allOn ? "حذف همه" : someOn ? "انتخاب همه" : "انتخاب همه"}
                      </Button>
                    </div>
                  </div>
                  <div className="flex flex-col gap-2">
                    {serverTools.map((tool) => (
                      <div
                        key={tool.id}
                        className="flex items-center justify-between gap-3 rounded-lg border px-3 py-2"
                      >
                        <div>
                          <div className="text-sm font-medium">{tool.name}</div>
                          <div className="text-xs text-muted-foreground">
                            {tool.description || "بدون توضیح"}
                          </div>
                        </div>
                        <Switch
                          checked={Boolean(selected[tool.id])}
                          onCheckedChange={(checked) =>
                            setSelected((prev) => ({ ...prev, [tool.id]: checked }))
                          }
                        />
                      </div>
                    ))}
                  </div>
                </div>
              );
            })
          )}

          <Button size="lg" disabled={busy || selectedIds.length === 0} onClick={() => void save()}>
            {busy
              ? "در حال ذخیره..."
              : isEditing
                ? `ذخیره تغییرات (${selectedIds.length} tool)`
                : `ساخت Gateway با ${selectedIds.length} tool`}
          </Button>

          {rawToken ? (
            <div className="rounded-xl border border-dashed bg-accent/40 p-4">
              <p className="mb-2 text-sm font-medium">
                platform token (فقط یک‌بار نمایش داده می‌شود)
              </p>
              <code className="block break-all text-sm">{rawToken}</code>
              <Button
                className="mt-3"
                variant="secondary"
                onClick={() => {
                  void navigator.clipboard.writeText(rawToken);
                  toast.success("کپی شد");
                }}
              >
                کپی token
              </Button>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Gateway / Tokenهای من</CardTitle>
          <CardDescription className="leading-7">
            روی «ویرایش toolها» بزنید تا allowlist همان token را عوض کنید. ابطال، token را از کار می‌اندازد.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          {tokens.map((t) => (
            <div
              key={t.id}
              className={`flex flex-wrap items-center justify-between gap-3 rounded-lg border px-3 py-2 ${
                editingId === t.id ? "border-primary bg-secondary/50" : ""
              }`}
            >
              <div>
                <div className="text-sm font-medium">{t.label}</div>
                <div className="text-xs text-muted-foreground">{t.token_prefix}…</div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={t.revoked_at ? "danger" : "success"}>
                  {t.revoked_at ? "باطل‌شده" : "فعال"}
                </Badge>
                {!t.revoked_at ? (
                  <>
                    <Button
                      size="sm"
                      variant={editingId === t.id ? "secondary" : "outline"}
                      disabled={busy}
                      onClick={() => void startEdit(t)}
                    >
                      ویرایش toolها
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={busy}
                      onClick={() => {
                        void (async () => {
                          if (!confirm(`token «${t.label}» ابطال شود؟`)) return;
                          setBusy(true);
                          try {
                            await client.revokeMyToken(t.id);
                            if (editingId === t.id) resetCreateMode();
                            await refresh();
                            toast.success("ابطال شد");
                          } catch (err) {
                            toast.error(err instanceof Error ? err.message : "خطا");
                          } finally {
                            setBusy(false);
                          }
                        })();
                      }}
                    >
                      ابطال
                    </Button>
                  </>
                ) : null}
              </div>
            </div>
          ))}
          {!tokens.length ? (
            <p className="text-sm text-muted-foreground">هنوز tokenی نساخته‌اید.</p>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
