import "./globals.css";

export const metadata = {
  title: "NAI Study — Your AI Learning Space",
  description: "A clear, intelligent space for studying, reviewing, and planning.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en" dir="ltr"><body>{children}</body></html>;
}
