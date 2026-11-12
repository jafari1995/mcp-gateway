import type { Metadata } from "next";
import { Toaster } from "sonner";
import { AuthGate } from "@/components/auth-gate";
import "./globals.css";

export const metadata: Metadata = {
  title: "MCP Gateway",
  description: "دروازه مینیمال MCP برای دمو و دفاع پایان‌نامه",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fa" dir="rtl">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,600;8..60,700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <AuthGate>{children}</AuthGate>
        <Toaster richColors position="top-center" dir="rtl" />
      </body>
    </html>
  );
}
