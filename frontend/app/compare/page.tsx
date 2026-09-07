'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Layers, ArrowRight, ShieldCheck, Scale, Check, HelpCircle } from 'lucide-react';

const COMPARISON_DATA = [
  {
    category: "What it protects",
    patent: "New inventions, technological processes, machines, compositions of matter having industrial application.",
    trademark: "Brand names, logos, slogans, stylized devices, sounds, and distinct trade dress distinguishing goods/services.",
    copyright: "Original literary, dramatic, musical, artistic works, cinematographic films, sound recordings, and computer code.",
    design: "Novel aesthetic visual features: shape, configuration, pattern, ornament applied to an article by industrial process."
  },
  {
    category: "Governing Indian Statute",
    patent: "The Patents Act, 1970 (as amended) & Patents Rules, 2003",
    trademark: "The Trade Marks Act, 1999 & Trade Marks Rules, 2017",
    copyright: "The Copyright Act, 1957 (as amended) & Copyright Rules, 2013",
    design: "The Designs Act, 2000 & Designs Rules, 2001"
  },
  {
    category: "Term of Protection",
    patent: "20 years from the date of filing (subject to annual renewal fees).",
    trademark: "10 years from filing date, perpetually renewable every 10 years.",
    copyright: "Author's lifetime + 60 years after death (for published literary/artistic works).",
    design: "10 years initially, extendable by 5 additional years (maximum 15 years)."
  },
  {
    category: "Registration Mandatory?",
    patent: "Yes — No protection exists without an official patent grant.",
    trademark: "Recommended — Unregistered marks receive limited common-law 'passing off' protection.",
    copyright: "Automatic upon creation — Registration provides prima facie evidence in court.",
    design: "Yes — Industrial design rights exist only upon registration."
  },
  {
    category: "Regulatory Authority",
    patent: "Controller General of Patents, Designs & Trade Marks (CGPDTM / IP India)",
    trademark: "Trade Marks Registry under CGPDTM (IP India)",
    copyright: "Copyright Office, Department for Promotion of Industry and Internal Trade (DPIIT)",
    design: "Patent Office (Designs Wing), Kolkata under CGPDTM"
  },
  {
    category: "Startup / SME Benefits",
    patent: "80% rebate on filing fees & expedited examination under Rule 24C.",
    trademark: "50% rebate on official filing fees for DPIIT-recognized startups.",
    copyright: "Standard statutory fee schedules apply.",
    design: "Substantial official fee reduction for startups & small entities."
  }
];

export default function ComparePage() {
  return (
    <div className="py-10 bg-slate-50 dark:bg-slate-950 min-h-screen transition-colors">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-10">
          <div className="inline-flex items-center gap-2 rounded-full border border-sky-200 dark:border-sky-800 bg-sky-50 dark:bg-sky-950/60 px-3 py-1 text-xs font-semibold text-sky-800 dark:text-sky-300 mb-3">
            <Layers className="h-3.5 w-3.5 text-sky-600 dark:text-sky-400" />
            <span>Statutory Comparison Matrix</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            Indian Intellectual Property Comparison
          </h1>
          <p className="mt-3 text-sm sm:text-base text-slate-600 dark:text-slate-400">
            Compare key statutory attributes across Patents, Trademarks, Copyrights, and Industrial Designs under Indian law.
          </p>
        </div>

        {/* Matrix Table */}
        <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm custom-scrollbar mb-10">
          <table className="w-full text-left text-xs sm:text-sm">
            <thead className="bg-slate-100/80 dark:bg-slate-800/80 border-b border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white font-bold">
              <tr>
                <th className="p-4 sm:p-5 w-1/5 min-w-[140px]">Dimension</th>
                <th className="p-4 sm:p-5 w-1/5 min-w-[200px] text-sky-900 dark:text-sky-300 bg-sky-50/50 dark:bg-sky-950/30">Patent</th>
                <th className="p-4 sm:p-5 w-1/5 min-w-[200px] text-indigo-900 dark:text-indigo-300">Trade Mark</th>
                <th className="p-4 sm:p-5 w-1/5 min-w-[200px] text-emerald-900 dark:text-emerald-300">Copyright</th>
                <th className="p-4 sm:p-5 w-1/5 min-w-[200px] text-purple-900 dark:text-purple-300">Industrial Design</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {COMPARISON_DATA.map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors">
                  <td className="p-4 sm:p-5 font-semibold text-slate-900 dark:text-white bg-slate-50/50 dark:bg-slate-800/40">
                    {row.category}
                  </td>
                  <td className="p-4 sm:p-5 text-slate-700 dark:text-slate-300 leading-relaxed bg-sky-50/20 dark:bg-sky-950/10">
                    {row.patent}
                  </td>
                  <td className="p-4 sm:p-5 text-slate-700 dark:text-slate-300 leading-relaxed">
                    {row.trademark}
                  </td>
                  <td className="p-4 sm:p-5 text-slate-700 dark:text-slate-300 leading-relaxed">
                    {row.copyright}
                  </td>
                  <td className="p-4 sm:p-5 text-slate-700 dark:text-slate-300 leading-relaxed">
                    {row.design}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Action Callout */}
        <div className="rounded-2xl border border-sky-200 dark:border-sky-800 bg-gradient-to-r from-sky-50 to-indigo-50 dark:from-slate-900 dark:to-slate-850 p-6 sm:p-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">Unsure which protection fits your startup?</h3>
            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 mt-1">
              Ask IP-SAKTI Sahayak in natural language (or your mother tongue) to analyze your specific assets.
            </p>
          </div>
          <Link
            href="/chat?q=Which IP protection is best for my startup product?"
            className="rounded-xl bg-sky-600 dark:bg-sky-500 px-5 py-3 text-xs sm:text-sm font-semibold text-white shadow hover:bg-sky-500 dark:hover:bg-sky-400 transition-all whitespace-nowrap flex items-center gap-1.5"
          >
            <span>Ask in Chat</span>
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

      </div>
    </div>
  );
}

