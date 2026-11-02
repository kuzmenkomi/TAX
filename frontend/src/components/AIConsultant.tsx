import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bot,
  Send,
  Loader2,
  Sparkles,
  User,
  MessageSquare,
  ChevronRight,
} from 'lucide-react';
import { useAppContext } from '../context/AppContext';
import { apiFetch } from '../api/v1';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  metadata?: {
    provider?: string;
    model?: string;
    tokens_used?: number;
  };
}

interface Preset {
  id: string;
  question: string;
}

const FALLBACK_PRESETS: Preset[] = [
  { id: 'portfolio_summary', question: "What's my overall portfolio status?" },
  { id: 'tax_liability', question: "What's my total tax liability?" },
  { id: 'loss_harvest', question: 'Which positions should I harvest losses from?' },
  { id: 'optimization', question: 'How can I reduce my tax bill?' },
  { id: 'income_tax', question: "What's my income from staking/airdrops?" },
];

function formatMarkdown(text: string): string {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong style="color: var(--text)">$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/^### (.*$)/gm, '<h4 class="font-bold text-sm mt-3 mb-1" style="color: var(--text)">$1</h4>')
    .replace(/^## (.*$)/gm, '<h3 class="font-bold text-base mt-3 mb-1" style="color: var(--text)">$1</h3>')
    .replace(/^# (.*$)/gm, '<h2 class="font-semibold text-lg mt-3 mb-2" style="color: var(--text)">$1</h2>')
    .replace(/^\| (.*) \|$/gm, (_, row) => {
      const cells = row.split('|').map((c: string) => c.trim());
      return `<tr>${cells.map((c: string) => `<td class="px-3 py-1 border text-xs" style="border-color: var(--border); color: var(--text2)">${c}</td>`).join('')}</tr>`;
    })
    .replace(/^\|[-|]+\|$/gm, '')
    .replace(/^- (.*$)/gm, '<li class="ml-4 text-sm" style="color: var(--text2)">• $1</li>')
    .replace(/^\d+\. (.*$)/gm, '<li class="ml-4 text-sm" style="color: var(--text2)">$1</li>')
    .replace(/\n/g, '<br/>');
}

export function AIConsultant() {
  const { analyzeResult, currentJurisdiction } = useAppContext();
  const runId = analyzeResult?.analysis_run_id;

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [presets, setPresets] = useState<Preset[]>(FALLBACK_PRESETS);
  const [providerInfo, setProviderInfo] = useState<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    (async () => {
      try {
        const res = await apiFetch('/ai/presets');
        if (res.ok) {
          const data = await res.json();
          setPresets(data.presets || FALLBACK_PRESETS);
        }
      } catch { /* use fallbacks */ }
    })();
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const res = await apiFetch('/ai/provider-info');
        if (res.ok) setProviderInfo(await res.json());
      } catch { /* ignore */ }
    })();
  }, []);

  const sendMessage = async (question: string) => {
    if (!question.trim() || !runId) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: question.trim(),
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await apiFetch('/ai/ask', {
        method: 'POST',
        body: JSON.stringify({
          question: question.trim(),
          run_id: runId,
          country_code: currentJurisdiction,
        }),
      });
      const data = await res.json();

      const aiMsg: ChatMessage = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: data.answer || 'Sorry, I could not generate a response.',
        timestamp: new Date(),
        metadata: {
          provider: data.provider,
          model: data.model,
          tokens_used: data.tokens_used,
        },
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: '⚠️ Failed to connect to AI service. Please ensure the backend is running.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  // No run loaded
  if (!runId) {
    return (
      <div className="text-center py-24">
        <div className="w-20 h-20 mx-auto mb-5 rounded-2xl border flex items-center justify-center p-4 transition-colors" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
          <Bot className="w-full h-full text-[#a78bfa]" />
        </div>
        <h2 className="text-2xl font-syne font-bold mb-2" style={{ color: 'var(--text)' }}>AI Tax Advisor</h2>
        <p className="text-[14px] max-w-md mx-auto" style={{ color: 'var(--text3)' }}>
          Upload and analyze your transactions first. The AI advisor uses your real portfolio data to provide personalized tax insights.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-200px)]">

      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-gradient-to-br from-[#a78bfa]/20 to-brand-green-500/10 border rounded-xl" style={{ borderColor: 'var(--border)' }}>
            <Bot className="w-5 h-5 text-[#a78bfa]" />
          </div>
          <div>
            <h1 className="text-lg font-syne font-bold tracking-tight" style={{ color: 'var(--text)' }}>AI Tax Advisor</h1>
            <div className="text-[11px] flex items-center gap-1.5" style={{ color: 'var(--text3)' }}>
              {providerInfo ? (
                <>
                  <span className={`w-1.5 h-1.5 rounded-full ${providerInfo.available ? 'bg-[var(--accent)]' : 'bg-[#f06a6a]'}`} />
                  Provider: <strong style={{ color: 'var(--text2)' }}>{providerInfo.provider}</strong>
                  {providerInfo.provider === 'mock' && (
                    <span className="text-[#f0a86a]">(Free mode)</span>
                  )}
                </>
              ) : (
                'Connecting...'
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto border rounded-[14px] p-5 space-y-4 mb-3 shadow-inner" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>

        {/* Welcome */}
        {messages.length === 0 && (
          <div className="text-center py-10 space-y-5">
            <Sparkles className="w-10 h-10 text-[#a78bfa] mx-auto animate-pulse" />
            <div>
              <h3 className="text-lg font-syne font-semibold mb-1.5" style={{ color: 'var(--text)' }}>Ask me anything about your taxes</h3>
              <p className="text-[13px] max-w-md mx-auto" style={{ color: 'var(--text3)' }}>
                I have access to your portfolio data and know the tax rules for your jurisdiction ({currentJurisdiction}).
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-lg mx-auto">
              {presets.slice(0, 6).map((preset) => (
                <button
                  key={preset.id}
                  onClick={() => sendMessage(preset.question)}
                  className="flex items-center gap-2 px-3.5 py-2.5 border rounded-lg text-[12px] text-left transition-all group hover:bg-brand-green-500/5"
                  style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text2)' }}
                >
                  <MessageSquare className="w-3.5 h-3.5 flex-shrink-0" style={{ color: 'var(--text3)' }} />
                  <span className="line-clamp-1 flex-1">{preset.question}</span>
                  <ChevronRight className="w-3 h-3 ml-auto flex-shrink-0" style={{ color: 'var(--text3)' }} />
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Messages */}
        <AnimatePresence>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className={`flex gap-2.5 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'assistant' && (
                <div className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center mt-1 border" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
                  <Bot className="w-4 h-4 text-[#a78bfa]" />
                </div>
              )}
              <div
                className={`max-w-[85%] rounded-xl px-4 py-3 shadow-sm ${
                  msg.role === 'user'
                    ? 'bg-brand-green-500/10 border border-brand-green-500/20 rounded-br-md'
                    : 'bg-surface2 border rounded-bl-md'
                }`}
                style={msg.role === 'assistant' ? { background: 'var(--bg2)', borderColor: 'var(--border)' } : undefined}
              >
                {msg.role === 'assistant' ? (
                  <div
                    className="text-[13px] leading-relaxed"
                    style={{ color: 'var(--text)' }}
                    dangerouslySetInnerHTML={{ __html: formatMarkdown(msg.content) }}
                  />
                ) : (
                  <p className="text-[13px]" style={{ color: 'var(--text)' }}>{msg.content}</p>
                )}
                {msg.metadata?.provider && (
                  <p className="text-[9px] mt-2 font-mono uppercase tracking-wider" style={{ color: 'var(--text3)' }}>
                    {msg.metadata.provider} · {msg.metadata.model}
                  </p>
                )}
              </div>
              {msg.role === 'user' && (
                <div className="flex-shrink-0 w-8 h-8 bg-brand-green-500/10 border border-brand-green-500/20 rounded-lg flex items-center justify-center mt-1">
                  <User className="w-4 h-4 text-brand-green-500" />
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Typing */}
        {loading && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-2.5">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center border" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
              <Bot className="w-4 h-4 text-[#a78bfa]" />
            </div>
            <div className="bg-surface2 border rounded-xl rounded-bl-md px-4 py-3" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
              <div className="flex items-center gap-1.5 p-1">
                <span className="w-1.5 h-1.5 bg-[#a78bfa] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 bg-[#a78bfa] rounded-full animate-bounce" style={{ animationDelay: '200ms' }} />
                <span className="w-1.5 h-1.5 bg-[#a78bfa] rounded-full animate-bounce" style={{ animationDelay: '400ms' }} />
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="border rounded-xl p-3 flex items-end gap-3 shadow-lg" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your crypto tax report..."
          rows={1}
          className="flex-1 resize-none border-0 bg-transparent text-[13px] focus:outline-none focus:ring-0 py-1 px-2"
          style={{ color: 'var(--text)' }}
          disabled={loading}
        />
        <button
          onClick={() => sendMessage(input)}
          disabled={loading || !input.trim()}
          className="flex-shrink-0 p-2.5 bg-brand-green-500 text-brand-dark rounded-lg hover:bg-brand-green-400 transition-all disabled:opacity-40 active:scale-95 shadow-md shadow-brand-green-500/20"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
        </button>
      </div>
    </div>
  );
}
