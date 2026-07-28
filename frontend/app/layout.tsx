import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Chat With Your Docs",
  description:
    "Upload a document collection, build a knowledge index, and chat with your documents.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
