import Link from 'next/link';
import { Scale, BookOpen, Compass, ShieldCheck, Layers, Upload, BarChart3 } from 'lucide-react';
import ThemeToggle from '@/components/ThemeToggle';

export default function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-slate-200/80 bg-white/90 backdrop-blur-md dark:border-slate-800 dark:bg-slate-900/90 transition-colors">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-sky-700 via-sky-600 to-indigo-600 text-white shadow-md shadow-sky-500/20 group-hover:scale-105 transition-transform">
            <Scale className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-tight text-slate-900 dark:text-white">IP-SAKTI</span>
              <span className="rounded bg-sky-100 dark:bg-sky-950/80 px-1.5 py-0.5 text-[10px] font-semibold text-sky-800 dark:text-sky-300 uppercase tracking-wider border border-sky-200/50 dark:border-sky-800/60">
                Sahayak
              </span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 hidden sm:block">
              Multilingual Legal & Regulatory Guidance
            </p>
          </div>
        </Link>

        <nav className="flex items-center gap-1 sm:gap-2">
          <Link
            href="/chat"
            className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white transition-colors"
          >
            <Compass className="h-4 w-4 text-sky-600 dark:text-sky-400" />
            <span>Chat</span>
          </Link>
          <Link
            href="/compare"
            className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white transition-colors"
          >
            <Layers className="h-4 w-4 text-sky-600 dark:text-sky-400" />
            <span className="hidden md:inline">Compare IP</span>
          </Link>
          <Link
            href="/sources"
            className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white transition-colors"
          >
            <BookOpen className="h-4 w-4 text-sky-600 dark:text-sky-400" />
            <span className="hidden md:inline">Sources</span>
          </Link>
          <Link
            href="/upload"
            className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white transition-colors"
          >
            <Upload className="h-4 w-4 text-sky-600 dark:text-sky-400" />
            <span className="hidden lg:inline">Analyze Doc</span>
          </Link>
          <Link
            href="/admin"
            className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white transition-colors"
          >
            <BarChart3 className="h-4 w-4 text-sky-600 dark:text-sky-400" />
            <span className="hidden lg:inline">Admin</span>
          </Link>

          {/* Day / Night Mode Toggle */}
          <div className="ml-1 sm:ml-2">
            <ThemeToggle />
          </div>

          <Link
            href="/chat"
            className="ml-1 sm:ml-2 inline-flex items-center justify-center rounded-lg bg-sky-600 px-3.5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-sky-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-600 transition-all active:scale-95"
          >
            Ask Sahayak
          </Link>
        </nav>
      </div>
    </header>
  );
}

