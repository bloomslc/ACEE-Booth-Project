import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Photo Booth",
  description: "A project for the ACEE booth",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body className="flex min-h-svh items-center justify-center">
        {children}
      </body>
    </html>
  );
}