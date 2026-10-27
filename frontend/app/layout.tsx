import "./globals.css";
import { LanguageProvider } from "@/lib/i18n";

export const metadata = {
  title: "NAI Study — Your AI Learning Space",
  description: "A clear, intelligent space for studying, reviewing, and planning.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="ar" dir="rtl" suppressHydrationWarning><body><LanguageProvider>{children}</LanguageProvider></body></html>;
}
