import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ACEE Booth Project",
  description: "A project for the ACEE booth",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body className="flex min-h-screen items-center justify-center bg-gray-100">
        {children}
      </body>
    </html>
  );
}