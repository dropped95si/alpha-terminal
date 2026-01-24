import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AlphaTerminal // Master Matrix",
  description: "Next.js dashboard powered by your scanner JSON outputs",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="scanlines min-h-screen p-4 md:p-6 lg:p-8 overflow-x-hidden">
        {children}
      </body>
    </html>
  );
}
