'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { 
  Scale, ArrowRight, ShieldCheck, Languages, CheckCircle2, 
  Sparkles, BookOpen, Layers, Lightbulb, Compass, Search, Award
} from 'lucide-react';

const LANGUAGES = [
  { code: 'en', label: 'English', native: 'English' },
  { code: 'hi', label: 'Hindi', native: 'हिंदी' },
  { code: 'bn', label: 'Bengali', native: 'বাংলা' },
  { code: 'ta', label: 'Tamil', native: 'தமிழ்' },
  { code: 'te', label: 'Telugu', native: 'తెలుగు' },
  { code: 'mixed', label: 'Hinglish', native: 'Hinglish' },
];

const SUGGESTED_QUERIES = [
  {
    title: "Patent vs Trademark",
    query: "What is the difference between a patent and a trademark for my startup?",
    lang: "en",
    domain: "patent"
  },
  {
    title: "Brand Name Protection",
    query: "मैं अपने स्टार्टअप के ब्रांड नाम को कैसे सुरक्षित कर सकता हूँ?",
    lang: "hi",
    domain: "trademark"
  },
  {
    title: "Logo & Product Design",
    query: "Mere startup ke logo aur product design ko kaise protect karein?",
    lang: "mixed",
    domain: "design"
  },
  {
    title: "Rule 23 Trademark",
    query: "What does Rule 23 of Trade Marks Rules 2017 say?",
    lang: "en",
    domain: "trademark"
  },
  {
    title: "Software Copyright",
    query: "ট্রেডমার্ক রেজিস্ট্রেশন কীভাবে করতে হয়?",
    lang: "bn",
    domain: "trademark"
  }
];

export default function HomePage() {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const [wizardIdea, setWizardIdea] = useState('');
  const [wizardResult, setWizardResult] = useState<string | null>(null);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    router.push(`/chat?q=${encodeURIComponent(query)}&lang=${selectedLanguage}`);
  };

  const handleSuggest = (q: string, lang: string) => {
    router.push(`/chat?q=${encodeURIComponent(q)}&lang=${lang}`);
  };

  const analyzeIdea = () => {
    if (!wizardIdea.trim()) return;
    const lower = wizardIdea.toLowerCase();
    let res = "";
    if (lower.includes('software') || lower.includes('code') || lower.includes('book') || lower.includes('music')) {
      res = "💡 Your creation likely involves Copyright (protects original software code/literary expression) and Trademark (for the application or platform brand).";
    } else if (lower.includes('machine') || lower.includes('algorithm') || lower.includes('hardware') || lower.includes('device') || lower.includes('technical')) {
      res = "⚙️ This may fall within the Patent framework for novel technical functioning, along with Industrial Design protection for the aesthetic physical shape.";
    } else if (lower.includes('brand') || lower.includes('logo') || lower.includes('name') || lower.includes('slogan')) {
      res = "🏷️ This is primarily protected via Trade Mark registration under the Trade Marks Act 1999.";
    } else {
      res = "🛡️ This may involve a combination of Patent (novel function), Industrial Design (outer visual appearance), and Trademark (market branding). Ask Sahayak in detail to cross-verify against statutes!";
    }
    setWizardResult(res);
  };

  return (
    <div className="relative overflow-hidden transition-colors duration-200">
      {/* Hero Section */}
      <section className="relative pt-12 pb-20 md:pt-20 md:pb-28 bg-gradient-to-b from-sky-50/70 via-white to-slate-50 dark:from-slate-900 dark:via-slate-950 dark:to-slate-900 border-b border-slate-200 dark:border-slate-800">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 text-center">
          
          <div className="inline-flex items-center gap-2 rounded-full border border-sky-200 bg-sky-50 dark:border-sky-800/80 dark:bg-sky-950/50 px-3.5 py-1.5 text-xs font-semibold text-sky-800 dark:text-sky-300 mb-6 shadow-sm">
            <Sparkles className="h-3.5 w-3.5 text-sky-600 dark:text-sky-400" />
            <span>Citation-First Multilingual Legal Guidance System</span>
          </div>

          <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight text-slate-900 dark:text-white leading-[1.15]">
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-700 via-sky-600 to-indigo-700 dark:from-sky-400 dark:via-sky-300 dark:to-indigo-400">
              IP-SAKTI Sahayak
            </span>
          </h1>

          <p className="mt-4 text-lg sm:text-xl text-slate-600 dark:text-slate-300 max-w-3xl mx-auto font-normal leading-relaxed">
            Authoritative, citation-backed AI guidance for India&apos;s Intellectual Property laws and regulatory requirements grounded in official statutory sources.
          </p>

          {/* Language Selector */}
          <div className="mt-8 flex flex-wrap items-center justify-center gap-2">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400 mr-1 flex items-center gap-1">
              <Languages className="h-3.5 w-3.5" /> Language:
            </span>
            {LANGUAGES.map((lang) => (
              <button
                key={lang.code}
                onClick={() => setSelectedLanguage(lang.code)}
                className={`rounded-full px-3 py-1 text-xs font-medium transition-all ${
                  selectedLanguage === lang.code
                    ? 'bg-sky-700 dark:bg-sky-600 text-white shadow-sm'
                    : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
                }`}
              >
                {lang.native} ({lang.label})
              </button>
            ))}
          </div>

          {/* Search Query Form */}
          <form onSubmit={handleSearch} className="mt-8 max-w-2xl mx-auto">
            <div className="relative flex items-center">
              <Search className="absolute left-4 h-5 w-5 text-slate-400 dark:text-slate-500" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask anything about patents, trademarks, copyright, designs, or DPIIT..."
                className="w-full rounded-2xl border border-slate-300/80 dark:border-slate-700 bg-white dark:bg-slate-900 py-4 pl-12 pr-32 text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 shadow-lg shadow-sky-900/5 dark:shadow-none focus:border-sky-500 focus:outline-none focus:ring-4 focus:ring-sky-500/15 sm:text-base transition-all"
              />
              <button
                type="submit"
                className="absolute right-2 rounded-xl bg-sky-600 dark:bg-sky-500 px-5 py-2.5 text-sm font-semibold text-white shadow-md hover:bg-sky-500 dark:hover:bg-sky-400 transition-all flex items-center gap-1.5"
              >
                <span>Ask</span>
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </form>

          {/* Suggested Queries */}
          <div className="mt-6 flex flex-wrap items-center justify-center gap-2 max-w-3xl mx-auto">
            <span className="text-xs font-medium text-slate-400 dark:text-slate-500">Try asking:</span>
            {SUGGESTED_QUERIES.map((s, idx) => (
              <button
                key={idx}
                onClick={() => handleSuggest(s.query, s.lang)}
                className="rounded-lg bg-slate-100/80 dark:bg-slate-800/80 border border-slate-200/60 dark:border-slate-700/60 px-2.5 py-1 text-xs text-slate-700 dark:text-slate-300 hover:bg-sky-50 hover:border-sky-200 hover:text-sky-800 dark:hover:bg-sky-950/60 dark:hover:border-sky-800 dark:hover:text-sky-300 transition-all"
              >
                {s.title}
              </button>
            ))}
          </div>

        </div>
      </section>

      {/* "What Protects My Idea?" Guided Tool */}
      <section className="py-14 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 transition-colors">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
          <div className="rounded-3xl border border-sky-100 dark:border-slate-800 bg-gradient-to-br from-sky-50/50 via-indigo-50/30 to-white dark:from-slate-800/60 dark:via-slate-800/30 dark:to-slate-900 p-6 sm:p-10 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-600 text-white">
                <Lightbulb className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white">What Protects My Idea?</h2>
                <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400">
                  Describe what you created, and our legal discovery system will map out relevant IP frameworks.
                </p>
              </div>
            </div>

            <div className="mt-4 flex flex-col sm:flex-row gap-3">
              <input
                type="text"
                value={wizardIdea}
                onChange={(e) => setWizardIdea(e.target.value)}
                placeholder="e.g., I built an IoT device with custom hardware, software algorithm, and brand name..."
                className="flex-1 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 px-4 py-3 text-sm text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-500/20"
              />
              <button
                type="button"
                onClick={analyzeIdea}
                className="rounded-xl bg-indigo-600 dark:bg-indigo-500 px-6 py-3 text-sm font-semibold text-white shadow hover:bg-indigo-500 dark:hover:bg-indigo-400 transition-all sm:w-auto"
              >
                Analyze Idea
              </button>
            </div>

            {wizardResult && (
              <div className="mt-4 rounded-xl border border-indigo-200 dark:border-indigo-900/60 bg-indigo-50/80 dark:bg-indigo-950/40 p-4 text-sm text-indigo-950 dark:text-indigo-200 flex items-start gap-3">
                <ShieldCheck className="h-5 w-5 text-indigo-600 dark:text-indigo-400 flex-shrink-0 mt-0.5" />
                <div className="space-y-2">
                  <p>{wizardResult}</p>
                  <Link
                    href={`/chat?q=${encodeURIComponent(`What IP protection is relevant for: ${wizardIdea}`)}`}
                    className="inline-flex items-center gap-1 font-semibold text-indigo-700 dark:text-indigo-400 hover:text-indigo-900 dark:hover:text-indigo-300 text-xs"
                  >
                    <span>Get complete statutory breakdown in Chat</span>
                    <ArrowRight className="h-3 w-3" />
                  </Link>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Core Pillars / Features */}
      <section className="py-16 bg-slate-50 dark:bg-slate-950 transition-colors">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">
              Why IP-SAKTI Sahayak?
            </h2>
            <p className="mt-2 text-sm sm:text-base text-slate-600 dark:text-slate-400">
              The LLM explains. The verified statutory knowledge base provides the evidence.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-sky-100 dark:bg-sky-950/80 text-sky-700 dark:text-sky-400 mb-4">
                <CheckCircle2 className="h-6 w-6" />
              </div>
              <h3 className="font-semibold text-lg text-slate-900 dark:text-white">Official Source Grounding</h3>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                Indexed directly from IP India, CGPDTM, Copyright Office, and Gazette notifications. Every legal claim maps to a verified chunk with Act, Section, and Rule citation.
              </p>
            </div>

            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-100 dark:bg-indigo-950/80 text-indigo-700 dark:text-indigo-400 mb-4">
                <Languages className="h-6 w-6" />
              </div>
              <h3 className="font-semibold text-lg text-slate-900 dark:text-white">Multilingual Retrieval</h3>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                Ask in English, Hindi, Bengali, Tamil, Telugu, or Hinglish. Powered by BGE-M3 multilingual embeddings and cross-lingual reranking.
              </p>
            </div>

            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-100 dark:bg-emerald-950/80 text-emerald-700 dark:text-emerald-400 mb-4">
                <Award className="h-6 w-6" />
              </div>
              <h3 className="font-semibold text-lg text-slate-900 dark:text-white">Transparent Confidence</h3>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                The model is never more confident than the retrieved evidence. Automatic low-evidence fallback prevents legal hallucinations.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Quick Access Grid */}
      <section className="py-14 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 transition-colors">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Link
              href="/compare"
              className="group rounded-2xl border border-slate-200 dark:border-slate-800 p-5 hover:border-sky-300 dark:hover:border-sky-700 hover:bg-sky-50/40 dark:hover:bg-slate-800/60 transition-all"
            >
              <div className="flex items-center justify-between">
                <Layers className="h-6 w-6 text-sky-600 dark:text-sky-400" />
                <ArrowRight className="h-4 w-4 text-slate-400 group-hover:translate-x-1 group-hover:text-sky-600 dark:group-hover:text-sky-400 transition-all" />
              </div>
              <h4 className="mt-3 font-semibold text-slate-900 dark:text-white">IP Comparison Matrix</h4>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Side-by-side comparison of Patents, Trademarks, Copyrights & Designs.</p>
            </Link>

            <Link
              href="/sources"
              className="group rounded-2xl border border-slate-200 dark:border-slate-800 p-5 hover:border-sky-300 dark:hover:border-sky-700 hover:bg-sky-50/40 dark:hover:bg-slate-800/60 transition-all"
            >
              <div className="flex items-center justify-between">
                <BookOpen className="h-6 w-6 text-sky-600 dark:text-sky-400" />
                <ArrowRight className="h-4 w-4 text-slate-400 group-hover:translate-x-1 group-hover:text-sky-600 dark:group-hover:text-sky-400 transition-all" />
              </div>
              <h4 className="mt-3 font-semibold text-slate-900 dark:text-white">Official Source Explorer</h4>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Search indexed Indian Acts, Rules, Manuals, and Gazette documents.</p>
            </Link>

            <Link
              href="/upload"
              className="group rounded-2xl border border-slate-200 dark:border-slate-800 p-5 hover:border-sky-300 dark:hover:border-sky-700 hover:bg-sky-50/40 dark:hover:bg-slate-800/60 transition-all"
            >
              <div className="flex items-center justify-between">
                <ShieldCheck className="h-6 w-6 text-sky-600 dark:text-sky-400" />
                <ArrowRight className="h-4 w-4 text-slate-400 group-hover:translate-x-1 group-hover:text-sky-600 dark:group-hover:text-sky-400 transition-all" />
              </div>
              <h4 className="mt-3 font-semibold text-slate-900 dark:text-white">Analyze Document</h4>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Cross-reference your IP notice or draft against official statutes.</p>
            </Link>

            <Link
              href="/admin"
              className="group rounded-2xl border border-slate-200 dark:border-slate-800 p-5 hover:border-sky-300 dark:hover:border-sky-700 hover:bg-sky-50/40 dark:hover:bg-slate-800/60 transition-all"
            >
              <div className="flex items-center justify-between">
                <Scale className="h-6 w-6 text-sky-600 dark:text-sky-400" />
                <ArrowRight className="h-4 w-4 text-slate-400 group-hover:translate-x-1 group-hover:text-sky-600 dark:group-hover:text-sky-400 transition-all" />
              </div>
              <h4 className="mt-3 font-semibold text-slate-900 dark:text-white">Evaluation & Admin</h4>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">View RAG evaluation metrics, corpus stats, and ingestion traces.</p>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );

}
