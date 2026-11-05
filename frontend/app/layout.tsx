import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GOVIA Cameroun — Assistance administrative",
  description: "Agent d'assistance administrative et de conformité aux procédures publiques",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body className="min-h-screen flex flex-col">
        {children}
      </body>
    </html>
  );
}
