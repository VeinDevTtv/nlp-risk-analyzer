import './globals.css'
// type import removed to avoid IDE/module resolution issues in some environments

export const metadata = {
  title: 'NLP Risk Analyzer',
  description: 'Finance news risk dashboard',
  icons: {
    icon: '/favicon.svg',
  },
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
