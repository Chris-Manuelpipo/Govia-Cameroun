import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import "./globals.css";

// Public Sans (SIL OFL), auto-hébergée : aucune requête vers un service externe à l'usage.
const texte = localFont({
  src: [
    { path: "./fonts/public-sans-latin-400.woff2", weight: "400", style: "normal" },
    { path: "./fonts/public-sans-latin-500.woff2", weight: "500", style: "normal" },
    { path: "./fonts/public-sans-latin-600.woff2", weight: "600", style: "normal" },
    { path: "./fonts/public-sans-latin-700.woff2", weight: "700", style: "normal" },
  ],
  variable: "--font-texte",
  display: "swap",
});

export const metadata: Metadata = {
  title: "GOVIA Cameroun : démarches administratives",
  description: "Annuaire des démarches administratives au Cameroun et assistant fondé sur les textes applicables.",
};

export const viewport: Viewport = {
  themeColor: "#0b2a4a",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" className={texte.variable}>
      <body>{children}</body>
    </html>
  );
}
