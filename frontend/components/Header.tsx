import Link from 'next/link'

export function Header() {
  return (
    <header className="border-b bg-white">
      <div className="container-page flex h-14 items-center justify-between">
        <Link href="/" className="font-semibold text-brand-700">
          NLP Risk Analyzer
        </Link>
        <nav className="text-sm text-gray-600">
          <Link href="/" className="hover:text-gray-900">
            Home
          </Link>
        </nav>
      </div>
    </header>
  )
}
