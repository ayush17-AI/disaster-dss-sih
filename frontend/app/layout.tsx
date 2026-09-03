import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Disaster DSS',
  description: 'Hazard Red-Zoning DSS',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
