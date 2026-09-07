'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { BookOpen, ExternalLink, ShieldCheck, Search, Filter, Layers, FileText } from 'lucide-react';
import { fetchSources, fetchLaws } from '@/lib/api';
import { SourceItem, LawItem } from '@/types';

const DOMAINS = [
  { id: 'all', label: 'All Domains' },
  { id: 'patent', label: 'Patents' },
  { id: 'trademark', label: 'Trade Marks' },
  { id: 'copyright', label: 'Copyright' },
  { id: 'design', label: 'Designs' },
  { id: 'gi', label: 'GI' },
  { id: 'sicld', label: 'SICLD' },
  { id: 'startup', label: 'Startup India' },
  { id: 'data_protection', label: 'Data Protection' },
];

export default function SourcesPage() {
  const [sources, setSources] = useState<SourceItem[]>([]);
  const [selectedDomain, setSelectedDomain] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      try {
        const data = await fetchSources(selectedDomain !== 'all' ? selectedDomain : undefined);
        setSources(data);
      } catch (e) {
        console.error(e);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [selectedDomain]);

  const filteredSources = sources.filter((s) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return s.name.toLowerCase().includes(q) || s.authority.toLowerCase().includes(q) || s.domain.toLowerCase().includes(q);
  });

  return (
    <div className="py-10 bg-slate-50 dark:bg-slate-950 min-h-screen transition-colors">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-10">
          <div className="inline-flex items-center gap-2 rounded-full border border-sky-200 dark:border-sky-800 bg-sky-50 dark:bg-sky-950/60 px-3 py-1 text-xs font-semibold text-sky-800 dark:text-sky-300 mb-3">
            <BookOpen className="h-3.5 w-3.5 text-sky-600 dark:text-sky-400" />
            <span>Authoritative Statutory Registry</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            Official Indian Legal Knowledge Sources
          </h1>
          <p className="mt-3 text-sm sm:text-base text-slate-600 dark:text-slate-400">
            Controlled source registry containing official Government of India gazettes, acts, rules, and manuals indexed by IP-SAKTI Sahayak.
          </p>
        </div>

        {/* Filters and Search */}
        <div className="mb-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-1.5 overflow-x-auto w-full md:w-auto pb-2 md:pb-0 custom-scrollbar">
            {DOMAINS.map((d) => (
              <button
                key={d.id}
                onClick={() => setSelectedDomain(d.id)}
                className={`rounded-full px-3.5 py-1.5 text-xs whitespace-nowrap font-medium transition-all ${
                  selectedDomain === d.id
                    ? 'bg-sky-600 dark:bg-sky-500 text-white font-semibold shadow-sm'
                    : 'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
                }`}
              >
                {d.label}
              </button>
            ))}
          </div>

          <div className="relative w-full md:w-72">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400 dark:text-slate-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search source title or authority..."
              className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 py-2 pl-9 pr-3 text-xs text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-500/20"
            />
          </div>
        </div>

        {/* Source List */}
        {isLoading ? (
          <div className="text-center py-20 text-slate-400 dark:text-slate-500 text-xs">Loading official source registry...</div>
        ) : filteredSources.length === 0 ? (
          <div className="text-center py-16 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-8">
            <FileText className="h-10 w-10 text-slate-300 dark:text-slate-700 mx-auto mb-2" />
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">No sources found matching your criteria</p>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Try selecting &apos;All Domains&apos; or clearing your search query.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filteredSources.map((source) => (
              <div
                key={source.id}
                className="flex flex-col justify-between rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 shadow-sm hover:border-sky-300 dark:hover:border-sky-700 hover:shadow-md transition-all"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="rounded bg-sky-100 dark:bg-sky-950/80 px-2 py-0.5 text-[10px] font-bold text-sky-800 dark:text-sky-300 uppercase tracking-wide border border-sky-200/50 dark:border-sky-800/60">
                      {source.domain}
                    </span>
                    <span className="inline-flex items-center gap-1 rounded bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800/80 px-2 py-0.5 text-[10px] font-semibold text-emerald-800 dark:text-emerald-300">
                      <ShieldCheck className="h-3 w-3 text-emerald-600 dark:text-emerald-400" />
                      <span>{source.authority_tier}</span>
                    </span>
                  </div>

                  <h3 className="font-bold text-slate-900 dark:text-white text-sm leading-snug">
                    {source.name}
                  </h3>

                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    Authority: <span className="font-medium text-slate-700 dark:text-slate-300">{source.authority}</span>
                  </p>

                  {source.description && (
                    <p className="text-xs text-slate-600 dark:text-slate-400 mt-3 line-clamp-3 leading-relaxed">
                      {source.description}
                    </p>
                  )}
                </div>

                <div className="mt-5 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs">
                  <span className="text-[11px] text-slate-400 dark:text-slate-500 capitalize">Type: {source.document_type || 'Act'}</span>
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 font-semibold text-sky-600 dark:text-sky-400 hover:text-sky-800 dark:hover:text-sky-300"
                  >
                    <span>Official Portal</span>
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}

      </div>
    </div>
  );
}

