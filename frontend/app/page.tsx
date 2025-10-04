"use client";
import Link from 'next/link';
import { useState } from 'react';
import { TickerCard } from '@/components/TickerCard';
import { Header } from '@/components/Header';
import { Footer } from '@/components/Footer';

const DEFAULT_WATCHLIST = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN'];

export default function HomePage() {
  const [query, setQuery] = useState('');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const symbol = query.trim().toUpperCase();
    if (!symbol) return;
    window.location.href = `/ticker/${symbol}`;
  };

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="container-page flex-1 py-8">
        <section className="mb-8 rounded-lg bg-white p-6 shadow">
          <h1 className="mb-4 text-2xl font-semibold">Risk Dashboard</h1>
          <form onSubmit={handleSearch} className="flex gap-2">
            <input
              type="text"
              placeholder="Enter ticker symbol (e.g., AAPL)"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-200"
            />
            <button
              type="submit"
              className="rounded-md bg-brand-600 px-4 py-2 font-medium text-white hover:bg-brand-700"
            >
              Search
            </button>
          </form>
        </section>

        <section className="rounded-lg bg-white p-6 shadow">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-semibold">Watchlist</h2>
            <Link href="#" className="text-sm text-brand-700 hover:underline">
              Manage
            </Link>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {DEFAULT_WATCHLIST.map((symbol) => (
              <TickerCard key={symbol} symbol={symbol} />
            ))}
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
