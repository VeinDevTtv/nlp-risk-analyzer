import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'NLP Risk Analyzer',
  description: 'Finance news risk dashboard',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 text-gray-900 antialiased">
        {children}
      </body>
    </html>
  )
}
