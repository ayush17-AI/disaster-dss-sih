import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Disaster DSS Dashboard",
  description: "Role C - Disaster Management Decision Support System",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body style={{ margin: 0, fontFamily: "sans-serif", backgroundColor: "#f4f6f8" }}>
        {children}
      </body>
    </html>
  );
}