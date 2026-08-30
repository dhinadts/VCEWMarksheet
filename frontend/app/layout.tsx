import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = { title: { default: "VCEW Results", template: "%s | VCEW Results" }, description: "University internal marksheet digitization and results administration" };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
