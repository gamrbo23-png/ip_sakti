'use client';

import { useState } from 'react';
import { Upload, FileText, ShieldAlert, CheckCircle2, RefreshCw, ExternalLink, ArrowRight } from 'lucide-react';
import { uploadDocument } from '@/lib/api';

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setResult(null);
      setError(null);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      const data = await uploadDocument(file);
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Failed to process document');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="py-10 bg-slate-50 dark:bg-slate-950 min-h-screen transition-colors">
      <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
        
        {/* Header */}
        <div className="text-center max-w-2xl mx-auto mb-10">
          <div className="inline-flex items-center gap-2 rounded-full border border-sky-200 dark:border-sky-800 bg-sky-50 dark:bg-sky-950/60 px-3 py-1 text-xs font-semibold text-sky-800 dark:text-sky-300 mb-3">
            <Upload className="h-3.5 w-3.5 text-sky-600 dark:text-sky-400" />
            <span>Document Cross-Analysis</span>
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            Analyze IP Notice or Draft
          </h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
            Upload your IP document or examination report to extract key themes and cross-reference related official Indian statutory provisions.
          </p>
        </div>

        {/* Privacy & Legal Guardrail Banner */}
        <div className="rounded-2xl border border-amber-200 dark:border-amber-900/60 bg-amber-50/80 dark:bg-amber-950/40 p-4 mb-8 text-xs text-amber-900 dark:text-amber-300">
          <div className="flex items-start gap-3">
            <ShieldAlert className="h-5 w-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h4 className="font-bold">Crucial Privacy & Authority Guardrail</h4>
              <p className="leading-relaxed">
                1. <strong>Privacy by Design:</strong> Your uploaded file is processed temporarily in-memory and is NOT stored permanently or used to train external models.
              </p>
              <p className="leading-relaxed">
                2. <strong>Legal Status:</strong> The uploaded file is treated as a <em>user artifact</em>, NEVER as an authoritative legal source. All legal guidance is retrieved exclusively from verified statutory databases.
              </p>
            </div>
          </div>
        </div>

        {/* Upload Form */}
        <form onSubmit={handleUpload} className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 sm:p-8 shadow-sm">
          <div className="flex flex-col items-center justify-center border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-xl p-8 hover:border-sky-400 dark:hover:border-sky-500 transition-colors bg-slate-50/50 dark:bg-slate-950/50">
            <FileText className="h-12 w-12 text-slate-400 dark:text-slate-500 mb-3" />
            <label className="cursor-pointer font-semibold text-sm text-sky-600 dark:text-sky-400 hover:text-sky-700 dark:hover:text-sky-300">
              <span>Choose a PDF or Text file</span>
              <input
                type="file"
                accept=".pdf,.txt"
                onChange={handleFileChange}
                className="hidden"
              />
            </label>
            <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">PDF or TXT up to 50MB</p>
            {file && (
              <div className="mt-4 rounded-lg bg-sky-50 dark:bg-sky-950/80 border border-sky-200 dark:border-sky-800 px-3 py-1.5 text-xs text-sky-800 dark:text-sky-300 font-medium flex items-center gap-2">
                <span>Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)</span>
              </div>
            )}
          </div>

          {error && (
            <div className="mt-4 rounded-xl border border-rose-200 dark:border-rose-900/60 bg-rose-50 dark:bg-rose-950/50 p-3 text-xs text-rose-800 dark:text-rose-300">
              {error}
            </div>
          )}

          <div className="mt-6 flex justify-end">
            <button
              type="submit"
              disabled={!file || isLoading}
              className="rounded-xl bg-sky-600 dark:bg-sky-500 px-6 py-2.5 text-sm font-semibold text-white shadow hover:bg-sky-500 dark:hover:bg-sky-400 disabled:opacity-50 transition-all flex items-center gap-2"
            >
              {isLoading && <RefreshCw className="h-4 w-4 animate-spin" />}
              <span>{isLoading ? 'Analyzing...' : 'Analyze Document'}</span>
            </button>
          </div>
        </form>

        {/* Results */}
        {result && (
          <div className="mt-8 space-y-6">
            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
              <h3 className="font-bold text-slate-900 dark:text-white text-base mb-2">Document Preview</h3>
              <p className="text-xs text-slate-600 dark:text-slate-300 bg-slate-50 dark:bg-slate-950 p-3 rounded-xl border border-slate-100 dark:border-slate-800 font-mono whitespace-pre-wrap">
                {result.content_preview}...
              </p>
            </div>

            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
              <h3 className="font-bold text-slate-900 dark:text-white text-base mb-4 flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
                <span>Related Official Statutory References</span>
              </h3>

              <div className="space-y-3">
                {result.related_official_sources?.map((s: any, idx: number) => (
                  <div key={idx} className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 p-4 text-xs space-y-1.5">
                    <div className="flex items-center justify-between font-bold text-slate-900 dark:text-white">
                      <span>{s.document_title}</span>
                      {s.section_no && <span className="text-sky-700 dark:text-sky-400">Section {s.section_no}</span>}
                    </div>
                    <p className="text-slate-600 dark:text-slate-300 italic">&ldquo;{s.content_preview}...&rdquo;</p>
                    <div className="pt-2 flex items-center justify-between border-t border-slate-100 dark:border-slate-800 text-[11px] text-slate-500 dark:text-slate-400">
                      <span>Authority: {s.authority}</span>
                      {s.source_url && (
                        <a
                          href={s.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-semibold text-sky-600 dark:text-sky-400 hover:text-sky-800 dark:hover:text-sky-300 flex items-center gap-1"
                        >
                          <span>Official Link</span>
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

