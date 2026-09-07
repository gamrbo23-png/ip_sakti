'use client';

import { useState, useEffect } from 'react';
import { 
  BarChart3, RefreshCw, Database, Layers, CheckCircle2, 
  AlertCircle, ShieldCheck, Clock, FileText, Play, Server
} from 'lucide-react';
import { fetchAdminStats, triggerIngestion } from '@/lib/api';
import { AdminStats } from '@/types';

export default function AdminPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isTriggering, setIsTriggering] = useState(false);
  const [triggerMsg, setTriggerMsg] = useState<string | null>(null);

  const loadStats = async () => {
    setIsLoading(true);
    try {
      const data = await fetchAdminStats();
      setStats(data);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  const handleIngest = async (force: boolean) => {
    setIsTriggering(true);
    setTriggerMsg(null);
    try {
      const res = await triggerIngestion({ force_refresh: force });
      setTriggerMsg(res.message || 'Ingestion initiated successfully in background.');
      setTimeout(loadStats, 3000);
    } catch (err: any) {
      setTriggerMsg(`Error: ${err.message}`);
    } finally {
      setIsTriggering(false);
    }
  };

  return (
    <div className="py-10 bg-slate-50 dark:bg-slate-950 min-h-screen transition-colors">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-sky-200 dark:border-sky-800 bg-sky-50 dark:bg-sky-950/60 px-3 py-1 text-xs font-semibold text-sky-800 dark:text-sky-300 mb-2">
              <BarChart3 className="h-3.5 w-3.5 text-sky-600 dark:text-sky-400" />
              <span>Admin & Evaluation Hub</span>
            </div>
            <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
              Knowledge Base & RAG Observability
            </h1>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => handleIngest(false)}
              disabled={isTriggering}
              className="flex items-center gap-1.5 rounded-xl bg-sky-600 dark:bg-sky-500 px-4 py-2 text-xs font-semibold text-white shadow hover:bg-sky-500 dark:hover:bg-sky-400 disabled:opacity-50 transition-all"
            >
              <Play className="h-3.5 w-3.5" />
              <span>Ingest Unchanged</span>
            </button>
            <button
              onClick={() => handleIngest(true)}
              disabled={isTriggering}
              className="flex items-center gap-1.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-4 py-2 text-xs font-semibold text-slate-700 dark:text-slate-300 shadow-sm hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-50 transition-all"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isTriggering ? 'animate-spin' : ''}`} />
              <span>Force Re-Index</span>
            </button>
          </div>
        </div>

        {triggerMsg && (
          <div className="mb-6 rounded-xl border border-sky-200 dark:border-sky-800 bg-sky-50 dark:bg-sky-950/60 p-4 text-xs font-medium text-sky-900 dark:text-sky-200">
            {triggerMsg}
          </div>
        )}

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 shadow-sm">
            <div className="flex items-center justify-between text-slate-400 dark:text-slate-500">
              <span className="text-xs font-medium uppercase tracking-wider">Indexed Documents</span>
              <FileText className="h-5 w-5 text-sky-600 dark:text-sky-400" />
            </div>
            <p className="mt-3 text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
              {stats ? stats.total_documents : '--'}
            </p>
            <span className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 block">Across Tier-1 Statutory Registries</span>
          </div>

          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 shadow-sm">
            <div className="flex items-center justify-between text-slate-400 dark:text-slate-500">
              <span className="text-xs font-medium uppercase tracking-wider">Legal Chunks (pgvector)</span>
              <Database className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
            </div>
            <p className="mt-3 text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
              {stats ? stats.total_chunks : '--'}
            </p>
            <span className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 block">BGE-M3 1024-dim dense vectors</span>
          </div>

          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 shadow-sm">
            <div className="flex items-center justify-between text-slate-400 dark:text-slate-500">
              <span className="text-xs font-medium uppercase tracking-wider">Avg Response Time</span>
              <Clock className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
            </div>
            <p className="mt-3 text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
              {stats ? `${stats.avg_total_latency_ms} ms` : '--'}
            </p>
            <span className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 block">Retrieval + Rerank + LLM</span>
          </div>

          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 shadow-sm">
            <div className="flex items-center justify-between text-slate-400 dark:text-slate-500">
              <span className="text-xs font-medium uppercase tracking-wider">Helpful Feedback Rate</span>
              <CheckCircle2 className="h-5 w-5 text-purple-600 dark:text-purple-400" />
            </div>
            <p className="mt-3 text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
              {stats ? `${(stats.helpful_feedback_rate * 100).toFixed(1)}%` : '--'}
            </p>
            <span className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 block">From verified user queries</span>
          </div>
        </div>

        {/* Domain Coverage & Recent Ingestion Jobs */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Domain Breakdown */}
          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
            <h3 className="font-bold text-slate-900 dark:text-white text-sm mb-4 flex items-center gap-2">
              <Layers className="h-4 w-4 text-sky-600 dark:text-sky-400" />
              <span>Domain Chunk Distribution</span>
            </h3>

            {stats && stats.domains_coverage ? (
              <div className="space-y-3 text-xs">
                {Object.entries(stats.domains_coverage).map(([domain, count]) => (
                  <div key={domain} className="flex items-center justify-between">
                    <span className="font-medium text-slate-700 dark:text-slate-300 capitalize">{domain.replace('_', ' ')}</span>
                    <span className="rounded-full bg-slate-100 dark:bg-slate-800 px-2.5 py-0.5 font-bold text-slate-800 dark:text-slate-200">
                      {count} chunks
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 dark:text-slate-500">No domain coverage stats available yet.</p>
            )}
          </div>

          {/* Ingestion Jobs Log */}
          <div className="lg:col-span-2 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
            <h3 className="font-bold text-slate-900 dark:text-white text-sm mb-4 flex items-center gap-2">
              <Server className="h-4 w-4 text-sky-600 dark:text-sky-400" />
              <span>Recent Ingestion Pipelines</span>
            </h3>

            {stats && stats.recent_jobs && stats.recent_jobs.length > 0 ? (
              <div className="overflow-x-auto custom-scrollbar">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 dark:bg-slate-800/80 text-slate-600 dark:text-slate-300 font-semibold border-b border-slate-200 dark:border-slate-700">
                    <tr>
                      <th className="p-2.5">Source URL</th>
                      <th className="p-2.5">Status</th>
                      <th className="p-2.5">Chunks</th>
                      <th className="p-2.5">Duplicates</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {stats.recent_jobs.map((job) => (
                      <tr key={job.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                        <td className="p-2.5 font-mono text-[11px] max-w-xs truncate text-slate-800 dark:text-slate-200">
                          {job.source_url}
                        </td>
                        <td className="p-2.5">
                          <span className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase ${
                            job.status === 'completed'
                              ? 'bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300'
                              : job.status === 'failed'
                              ? 'bg-rose-100 dark:bg-rose-950/80 text-rose-800 dark:text-rose-300'
                              : 'bg-amber-100 dark:bg-amber-950/80 text-amber-800 dark:text-amber-300'
                          }`}>
                            {job.status}
                          </span>
                        </td>
                        <td className="p-2.5 text-slate-700 dark:text-slate-300">{job.chunks_created}</td>
                        <td className="p-2.5 text-slate-500 dark:text-slate-400">{job.duplicates_skipped}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-10 text-slate-400 dark:text-slate-500 text-xs">
                No recent ingestion jobs recorded. Trigger ingestion to populate the statutory index.
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}

