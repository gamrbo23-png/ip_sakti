'use client';

import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'next/navigation';
import { 
  Send, Bot, User, Scale, ShieldCheck, BookOpen, AlertCircle, 
  ExternalLink, ThumbsUp, ThumbsDown, Copy, Volume2, Sparkles, 
  ChevronRight, RefreshCw, Layers, Check, Info, FileText
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { sendChatMessage, submitFeedback } from '@/lib/api';
import { ChatMessage, Citation, EvidenceTrace } from '@/types';

const DOMAINS = [
  { id: 'all', label: 'All Domains' },
  { id: 'patent', label: 'Patents' },
  { id: 'trademark', label: 'Trade Marks' },
  { id: 'copyright', label: 'Copyright' },
  { id: 'design', label: 'Designs' },
  { id: 'gi', label: 'GI' },
  { id: 'startup', label: 'Startup / DPIIT' },
  { id: 'data_protection', label: 'Data Protection' },
];

export default function ChatPage() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get('q') || '';
  const initialLang = searchParams.get('lang') || 'en';

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedDomain, setSelectedDomain] = useState('all');
  const [sessionId, setSessionId] = useState<string>('');
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceTrace[]>([]);
  const [activeTab, setActiveTab] = useState<'chat' | 'evidence'>('chat');
  const [copiedId, setCopiedId] = useState<string | number | null>(null);
  const [feedbackSent, setFeedbackSent] = useState<Record<string | number, number>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Generate session ID if not set
    if (!sessionId) {
      setSessionId(`session_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`);
    }
  }, [sessionId]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Handle query passed from home page URL params
  useEffect(() => {
    if (initialQuery && messages.length === 0 && sessionId) {
      handleSendMessage(initialQuery, initialLang);
    }
  }, [initialQuery, sessionId]);

  const handleSendMessage = async (queryText?: string, queryLang?: string) => {
    const textToSend = queryText || input;
    if (!textToSend.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: textToSend,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    if (!queryText) setInput('');
    setIsLoading(true);

    try {
      const response = await sendChatMessage({
        query: textToSend,
        session_id: sessionId,
        language: queryLang || undefined,
        domain: selectedDomain !== 'all' ? selectedDomain : undefined,
      });

      setMessages((prev) => [...prev, response]);
      if (response.evidence && response.evidence.length > 0) {
        setSelectedEvidence(response.evidence);
      }
    } catch (err: any) {
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: `⚠️ **Service Notice**: ${err.message || 'Unable to complete request. Please ensure the backend is running.'}`,
        evidence_level: 'none',
        has_sufficient_evidence: false,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = (content: string, id?: string | number) => {
    navigator.clipboard.writeText(content);
    if (id) {
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    }
  };

  const handleSpeak = (content: string) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      // Strip markdown asterisks and hash marks for clean speech
      const plainText = content.replace(/[*#_`]/g, '');
      const utterance = new SpeechSynthesisUtterance(plainText);
      window.speechSynthesis.speak(utterance);
    }
  };

  const handleFeedback = async (message: ChatMessage, rating: number) => {
    if (!message.id) return;
    try {
      await submitFeedback({
        session_id: sessionId,
        message_id: typeof message.id === 'number' ? message.id : undefined,
        retrieval_trace_id: message.retrieval_trace_id,
        rating,
      });
      setFeedbackSent((prev) => ({ ...prev, [message.id!]: rating }));
    } catch (e) {
      console.error(e);
    }
  };

  const startNewChat = () => {
    setSessionId(`session_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`);
    setMessages([]);
    setSelectedEvidence([]);
  };

  return (
    <div className="flex h-[calc(100vh-61px)] flex-col md:flex-row overflow-hidden bg-slate-100 dark:bg-slate-950 transition-colors">
      
      {/* Left Sidebar */}
      <aside className="hidden md:flex w-64 flex-col border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 transition-colors">
        <button
          onClick={startNewChat}
          className="flex items-center justify-center gap-2 rounded-xl border border-sky-200 dark:border-sky-800 bg-sky-50 dark:bg-sky-950/60 px-4 py-2.5 text-sm font-semibold text-sky-800 dark:text-sky-300 hover:bg-sky-100 dark:hover:bg-sky-900/60 transition-colors shadow-sm"
        >
          <RefreshCw className="h-4 w-4 text-sky-600 dark:text-sky-400" />
          <span>New Conversation</span>
        </button>

        <div className="mt-6 flex-1 overflow-y-auto custom-scrollbar">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-2 px-2">
            IP Domains
          </h3>
          <div className="space-y-1">
            {DOMAINS.map((d) => (
              <button
                key={d.id}
                onClick={() => setSelectedDomain(d.id)}
                className={`w-full flex items-center justify-between rounded-lg px-3 py-2 text-xs font-medium transition-all ${
                  selectedDomain === d.id
                    ? 'bg-sky-600 dark:bg-sky-500 text-white font-semibold'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
                }`}
              >
                <span>{d.label}</span>
                {selectedDomain === d.id && <ChevronRight className="h-3.5 w-3.5" />}
              </button>
            ))}
          </div>

          <div className="mt-8 border-t border-slate-200 dark:border-slate-800 pt-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-2 px-2">
              Statutory Trust
            </h3>
            <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/50 p-3 text-[11px] text-slate-600 dark:text-slate-400 space-y-2">
              <div className="flex items-center gap-1.5 text-sky-800 dark:text-sky-300 font-semibold">
                <ShieldCheck className="h-4 w-4 text-sky-600 dark:text-sky-400" />
                <span>Tier-1 Sources Only</span>
              </div>
              <p className="text-slate-500 dark:text-slate-400">
                Answers generated strictly from indexed Indian government gazettes, acts, rules & manuals.
              </p>
            </div>
          </div>
        </div>
      </aside>

      {/* Center Chat Main Area */}
      <div className="flex flex-1 flex-col overflow-hidden bg-slate-50 dark:bg-slate-950 transition-colors">
        
        {/* Domain Filter Bar (Mobile / Compact) */}
        <div className="flex items-center gap-1.5 overflow-x-auto border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-4 py-2.5 custom-scrollbar transition-colors">
          <span className="text-xs font-medium text-slate-400 dark:text-slate-500 flex items-center gap-1 flex-shrink-0">
            <Layers className="h-3.5 w-3.5" /> Domain:
          </span>
          {DOMAINS.map((d) => (
            <button
              key={d.id}
              onClick={() => setSelectedDomain(d.id)}
              className={`rounded-full px-3 py-1 text-xs whitespace-nowrap transition-all ${
                selectedDomain === d.id
                  ? 'bg-sky-600 dark:bg-sky-500 text-white font-semibold'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              {d.label}
            </button>
          ))}
        </div>

        {/* Message Thread */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 custom-scrollbar space-y-6">
          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center text-center max-w-md mx-auto">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-sky-100 dark:bg-sky-950/80 text-sky-700 dark:text-sky-400 mb-4 shadow-sm">
                <Scale className="h-8 w-8" />
              </div>
              <h2 className="text-xl font-bold text-slate-800 dark:text-white">Welcome to IP-SAKTI Sahayak</h2>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                Ask any question regarding Indian Patent, Trademark, Copyright, Design, GI, or Startup regulatory procedures in any Indian language.
              </p>
              <div className="mt-6 flex flex-wrap justify-center gap-2">
                <button
                  onClick={() => handleSendMessage('How do I register a trademark in India?')}
                  className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-1.5 text-xs text-slate-700 dark:text-slate-300 hover:border-sky-300 dark:hover:border-sky-700 hover:bg-sky-50 dark:hover:bg-slate-800 transition-all"
                >
                  How do I register a trademark?
                </button>
                <button
                  onClick={() => handleSendMessage('What is non-patentable under Section 3 of Patents Act?')}
                  className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-1.5 text-xs text-slate-700 dark:text-slate-300 hover:border-sky-300 dark:hover:border-sky-700 hover:bg-sky-50 dark:hover:bg-slate-800 transition-all"
                >
                  What is non-patentable under Section 3?
                </button>
                <button
                  onClick={() => handleSendMessage('पेटेंट और ट्रेडमार्क में क्या अंतर है?', 'hi')}
                  className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-1.5 text-xs text-slate-700 dark:text-slate-300 hover:border-sky-300 dark:hover:border-sky-700 hover:bg-sky-50 dark:hover:bg-slate-800 transition-all"
                >
                  पेटेंट और ट्रेडमार्क में अंतर
                </button>
              </div>
            </div>
          ) : (
            messages.map((m, idx) => (
              <div
                key={idx}
                className={`flex gap-3 sm:gap-4 ${
                  m.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {m.role === 'assistant' && (
                  <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-sky-700 to-indigo-700 text-white shadow-sm mt-1">
                    <Bot className="h-5 w-5" />
                  </div>
                )}

                <div
                  className={`max-w-3xl rounded-2xl p-4 sm:p-5 text-sm leading-relaxed shadow-sm ${
                    m.role === 'user'
                      ? 'bg-sky-600 text-white rounded-br-none'
                      : 'bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 text-slate-900 dark:text-slate-100 rounded-bl-none'
                  }`}
                >
                  {/* Assistant Header & Evidence Badge */}
                  {m.role === 'assistant' && (
                    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-800 pb-2.5 mb-3 text-xs">
                      <div className="flex items-center gap-2">
                        {m.evidence_level === 'high' && (
                          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 dark:bg-emerald-950/80 px-2.5 py-0.5 font-semibold text-emerald-800 dark:text-emerald-300">
                            <ShieldCheck className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                            <span>High Evidence</span>
                          </span>
                        )}
                        {m.evidence_level === 'moderate' && (
                          <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 dark:bg-amber-950/80 px-2.5 py-0.5 font-semibold text-amber-800 dark:text-amber-300">
                            <Info className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
                            <span>Moderate Evidence</span>
                          </span>
                        )}
                        {m.evidence_level === 'low' && (
                          <span className="inline-flex items-center gap-1 rounded-full bg-rose-100 dark:bg-rose-950/80 px-2.5 py-0.5 font-semibold text-rose-800 dark:text-rose-300">
                            <AlertCircle className="h-3.5 w-3.5 text-rose-600 dark:text-rose-400" />
                            <span>Limited Evidence</span>
                          </span>
                        )}
                        {m.domain && (
                          <span className="rounded bg-slate-100 dark:bg-slate-800 px-2 py-0.5 text-[11px] font-medium text-slate-600 dark:text-slate-400 uppercase tracking-wide">
                            {m.domain}
                          </span>
                        )}
                      </div>

                      {m.evidence && m.evidence.length > 0 && (
                        <button
                          onClick={() => {
                            setSelectedEvidence(m.evidence || []);
                            setActiveTab('evidence');
                          }}
                          className="text-xs font-semibold text-sky-700 dark:text-sky-400 hover:text-sky-900 dark:hover:text-sky-300 underline flex items-center gap-1"
                        >
                          <BookOpen className="h-3 w-3" />
                          <span>View {m.evidence.length} Evidence Sources</span>
                        </button>
                      )}
                    </div>
                  )}

                  {/* Main Content Markdown */}
                  <div className="prose prose-sm max-w-none prose-slate dark:prose-invert prose-headings:font-bold prose-headings:text-slate-900 dark:prose-headings:text-white prose-a:text-sky-700 dark:prose-a:text-sky-400 prose-strong:text-slate-900 dark:prose-strong:text-white">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {m.content}
                    </ReactMarkdown>
                  </div>

                  {/* Citation Pills */}
                  {m.citations && m.citations.length > 0 && (
                    <div className="mt-4 border-t border-slate-100 dark:border-slate-800 pt-3">
                      <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-2">
                        Official Citations
                      </h4>
                      <div className="flex flex-wrap gap-1.5">
                        {m.citations.map((c, cIdx) => (
                          <a
                            key={cIdx}
                            href={c.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 rounded-lg border border-sky-200 dark:border-sky-800/80 bg-sky-50 dark:bg-sky-950/60 px-2.5 py-1 text-xs text-sky-900 dark:text-sky-200 hover:bg-sky-100 dark:hover:bg-sky-900/60 transition-colors"
                          >
                            <span className="font-semibold">[{c.citation_number}]</span>
                            <span>{c.document_title}</span>
                            {c.section_no && <span className="font-medium">• Sec {c.section_no}</span>}
                            {c.rule_no && <span className="font-medium">• Rule {c.rule_no}</span>}
                            <ExternalLink className="h-2.5 w-2.5 opacity-60" />
                          </a>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Action Buttons */}
                  {m.role === 'assistant' && (
                    <div className="mt-4 flex items-center justify-between border-t border-slate-100 dark:border-slate-800 pt-2.5 text-xs text-slate-400 dark:text-slate-500">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleCopy(m.content, m.id || idx)}
                          className="flex items-center gap-1 rounded px-2 py-1 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 transition-colors"
                          title="Copy Answer"
                        >
                          {copiedId === (m.id || idx) ? (
                            <Check className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                          ) : (
                            <Copy className="h-3.5 w-3.5" />
                          )}
                          <span className="text-[11px]">{copiedId === (m.id || idx) ? 'Copied' : 'Copy'}</span>
                        </button>

                        <button
                          onClick={() => handleSpeak(m.content)}
                          className="flex items-center gap-1 rounded px-2 py-1 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 transition-colors"
                          title="Listen via Text-to-Speech"
                        >
                          <Volume2 className="h-3.5 w-3.5" />
                          <span className="text-[11px]">Listen</span>
                        </button>
                      </div>

                      {/* Feedback buttons */}
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleFeedback(m, 1)}
                          className={`rounded p-1 transition-colors ${
                            feedbackSent[m.id || idx] === 1 ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/60' : 'hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 dark:text-slate-400'
                          }`}
                          title="Helpful"
                        >
                          <ThumbsUp className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={() => handleFeedback(m, -1)}
                          className={`rounded p-1 transition-colors ${
                            feedbackSent[m.id || idx] === -1 ? 'text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/60' : 'hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 dark:text-slate-400'
                          }`}
                          title="Not Helpful"
                        >
                          <ThumbsDown className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {m.role === 'user' && (
                  <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl bg-slate-800 dark:bg-slate-700 text-white shadow-sm mt-1">
                    <User className="h-5 w-5" />
                  </div>
                )}
              </div>
            ))
          )}

          {isLoading && (
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-sky-700 to-indigo-700 text-white animate-pulse">
                <Bot className="h-5 w-5" />
              </div>
              <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-4 py-3 text-xs text-slate-600 dark:text-slate-300 shadow-sm flex items-center gap-2">
                <RefreshCw className="h-3.5 w-3.5 animate-spin text-sky-600 dark:text-sky-400" />
                <span>Searching official Indian statutes & generating grounded guidance...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3 sm:p-4 transition-colors">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center gap-2 max-w-4xl mx-auto"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about patent, trademark, copyright, design rules in any Indian language..."
              disabled={isLoading}
              className="flex-1 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-950 px-4 py-3 text-sm text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:border-sky-500 focus:bg-white dark:focus:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-sky-500/20 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="rounded-xl bg-sky-600 dark:bg-sky-500 px-4 py-3 text-white shadow-sm hover:bg-sky-500 dark:hover:bg-sky-400 disabled:opacity-50 transition-all"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      </div>

      {/* Right Sidebar: "Why this answer?" & Source Evidence Panel */}
      <aside className="hidden lg:flex w-80 flex-col border-l border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 overflow-y-auto custom-scrollbar transition-colors">
        <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3 mb-4">
          <div className="flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-sky-600 dark:text-sky-400" />
            <h3 className="font-bold text-sm text-slate-800 dark:text-white">Source Evidence</h3>
          </div>
          <span className="rounded bg-sky-100 dark:bg-sky-950/80 px-2 py-0.5 text-[10px] font-bold text-sky-800 dark:text-sky-300 border border-sky-200/50 dark:border-sky-800/60">
            {selectedEvidence.length} Chunks
          </span>
        </div>

        {selectedEvidence.length === 0 ? (
          <div className="flex flex-col items-center justify-center text-center p-6 text-slate-400 dark:text-slate-500 my-auto">
            <FileText className="h-10 w-10 text-slate-300 dark:text-slate-700 mb-2" />
            <p className="text-xs">Ask a question to inspect retrieved legal provisions, authority tiers, and direct links.</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 p-3 text-xs">
              <h4 className="font-semibold text-slate-800 dark:text-white flex items-center gap-1.5">
                <ShieldCheck className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                <span>Why this answer?</span>
              </h4>
              <ul className="mt-2 space-y-1 text-[11px] text-slate-600 dark:text-slate-400">
                <li>✓ Government source verified</li>
                <li>✓ Current version preferred</li>
                <li>✓ Cross-lingual match confirmed</li>
                <li>✓ Citation mapped to statutory provision</li>
              </ul>
            </div>

            {selectedEvidence.map((ev, i) => (
              <div
                key={i}
                className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 p-3.5 shadow-sm text-xs space-y-2 hover:border-sky-300 dark:hover:border-sky-700 transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <h5 className="font-bold text-slate-900 dark:text-white leading-tight">
                    {ev.document_title || 'Statutory Source'}
                  </h5>
                  <span className="rounded bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 text-[10px] font-semibold text-slate-600 dark:text-slate-400">
                    {ev.status || 'CURRENT'}
                  </span>
                </div>

                <div className="flex flex-wrap gap-1.5 text-[11px] text-slate-600 dark:text-slate-400 font-medium">
                  {ev.section_no && (
                    <span className="rounded bg-sky-50 dark:bg-sky-950/80 border border-sky-200 dark:border-sky-800 px-1.5 py-0.5 text-sky-800 dark:text-sky-300">
                      Section {ev.section_no}
                    </span>
                  )}
                  {ev.rule_no && (
                    <span className="rounded bg-sky-50 dark:bg-sky-950/80 border border-sky-200 dark:border-sky-800 px-1.5 py-0.5 text-sky-800 dark:text-sky-300">
                      Rule {ev.rule_no}
                    </span>
                  )}
                  {ev.chapter && (
                    <span className="rounded bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 text-slate-600 dark:text-slate-400">
                      Chapter {ev.chapter}
                    </span>
                  )}
                </div>

                <p className="text-[11px] text-slate-600 dark:text-slate-300 leading-relaxed bg-slate-50 dark:bg-slate-900 p-2 rounded-lg border border-slate-100 dark:border-slate-800 italic">
                  &ldquo;{ev.content_preview}...&rdquo;
                </p>

                <div className="flex items-center justify-between text-[10px] text-slate-500 dark:text-slate-400 pt-1 border-t border-slate-100 dark:border-slate-800">
                  <span>Authority: {ev.authority || 'IP India'}</span>
                  {ev.source_url && (
                    <a
                      href={ev.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sky-600 dark:text-sky-400 hover:text-sky-800 dark:hover:text-sky-300 font-semibold flex items-center gap-0.5"
                    >
                      <span>Official PDF</span>
                      <ExternalLink className="h-2.5 w-2.5" />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </aside>

    </div>
  );

}
