import { ShieldAlert, ExternalLink } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900/80 py-8 text-xs text-slate-500 dark:text-slate-400 transition-colors">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="rounded-xl border border-amber-200 bg-amber-50/70 dark:border-amber-900/50 dark:bg-amber-950/30 p-4 mb-6">
          <div className="flex items-start gap-3">
            <ShieldAlert className="h-5 w-5 text-amber-700 dark:text-amber-500 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-amber-900 dark:text-amber-300 text-sm">Official Legal Disclaimer</h4>
              <p className="text-amber-800/90 dark:text-amber-300/80 mt-1 leading-relaxed">
                IP-SAKTI Sahayak is an AI guidance system powered by authoritative Government of India legal sources (IP India, CGPDTM, Copyright Office, DPIIT, MeitY). It provides educational and informational assistance, not legal representation or professional legal advice.
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-700 dark:text-slate-300">IP-SAKTI Sahayak</span>
            <span>•</span>
            <span>Multilingual Citation-First Legal RAG</span>
          </div>

          <div className="flex items-center gap-4 text-slate-600 dark:text-slate-400">
            <a href="https://ipindia.gov.in" target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 hover:text-sky-700 dark:hover:text-sky-400 transition-colors">
              <span>IP India</span>
              <ExternalLink className="h-3 w-3" />
            </a>
            <a href="https://copyright.gov.in" target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 hover:text-sky-700 dark:hover:text-sky-400 transition-colors">
              <span>Copyright Office</span>
              <ExternalLink className="h-3 w-3" />
            </a>
            <a href="https://startupindia.gov.in" target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 hover:text-sky-700 dark:hover:text-sky-400 transition-colors">
              <span>Startup India</span>
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}

