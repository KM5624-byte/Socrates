import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AILEO | AI Labor & Employment Observatory",
  description: "Source-linked labor market data and regulatory timelines for public-interest research.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
