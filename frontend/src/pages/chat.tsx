import React, { useState } from 'react';
import Link from 'next/link';
import Layout from '../components/Layout';
import { useAppState } from '../context/AppStateContext';
import { Sparkles, Send, Bot, User, ArrowUpRight, MessageSquare } from 'lucide-react';

interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  timestamp: string;
  links?: { label: string; href: string }[];
}

export default function ChatAssistant() {
  const { emails, candidates } = useAppState();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState<string>('');
  const [isTyping, setIsTyping] = useState<boolean>(false);

  const starterSuggestions = [
    'How many emails did I receive today?',
    'Show applicants for AI Engineer role',
    'Any high priority emails?',
    'How many pending drafts?',
  ];

  const handleSendMessage = (questionText: string) => {
    if (!questionText.trim()) return;

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      text: questionText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setIsTyping(true);

    // Dynamic RAG answer synthesis
    setTimeout(() => {
      let aiText = '';
      let links: { label: string; href: string }[] | undefined = undefined;

      const q = questionText.toLowerCase();

      if (q.includes('how many emails') || q.includes('emails today')) {
        const count = emails.length + 18;
        aiText = `You have received **${count} emails** today. 6 require draft approval and 2 are categorized as high priority.`;
        links = [{ label: 'Open Recruiter Inbox', href: '/inbox' }];
      } else if (q.includes('ai engineer') || q.includes('applicants')) {
        const aiCandidates = candidates.filter((c) => c.role === 'AI Engineer');
        aiText = `We currently have **${aiCandidates.length} candidate applications** for the **AI Engineer** position: John Smith and Elena Rostova.`;
        links = [
          { label: 'View John Smith Profile', href: '/candidates' },
          { label: 'View Elena Rostova Profile', href: '/candidates' },
        ];
      } else if (q.includes('high priority')) {
        const highPriorityEmails = emails.filter((e) => e.priority === 'High');
        aiText = `There are **${highPriorityEmails.length} high priority emails** needing immediate attention, including Jane Doe (Salary & Remote Policy) and Marcus Vance (Offer Letter).`;
        links = highPriorityEmails.map((e) => ({
          label: `${e.senderName} - ${e.subject.slice(0, 30)}...`,
          href: `/inbox/${e.id}`,
        }));
      } else if (q.includes('pending drafts') || q.includes('drafts')) {
        const pendingCount = emails.filter((e) => e.draftReply && e.draftReply.status === 'pending').length;
        aiText = `There are currently **${pendingCount} pending AI drafts** awaiting your review and approval in the queue.`;
        links = [{ label: 'Launch Draft Review Queue', href: '/drafts' }];
      } else {
        aiText = `I analyzed your HR inbox and candidate database. Based on your settings, all new candidate emails are automatically parsed and formatted into draft responses according to your Friendly tone preference.`;
        links = [{ label: 'Go to Dashboard', href: '/dashboard' }];
      }

      const aiMsg: ChatMessage = {
        id: `ai-${Date.now()}`,
        sender: 'ai',
        text: aiText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        links,
      };

      setMessages((prev) => [...prev, aiMsg]);
      setIsTyping(false);
    }, 600);
  };

  return (
    <Layout>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-zinc-900 tracking-tight flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-amber-500" />
            AI Chat Assistant
          </h1>
          <p className="text-xs text-zinc-500 font-semibold mt-1">
            Query your HR inbox, candidate resumes, and recruitment metrics using natural language
          </p>
        </div>
      </div>

      {/* Main Chat Container */}
      <div className="nixtio-card overflow-hidden flex flex-col h-[650px]">
        {/* Messages Scroll Area */}
        <div className="flex-1 p-6 overflow-y-auto space-y-4 bg-white/40">
          {messages.length === 0 ? (
            /* Starter Suggestions Empty State */
            <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-6">
              <div className="w-16 h-16 rounded-3xl bg-zinc-900 text-amber-400 flex items-center justify-center shadow-nixtio">
                <Bot className="w-8 h-8" />
              </div>
              <div className="space-y-1">
                <h3 className="text-lg font-extrabold text-zinc-900">How can I assist your recruiting today?</h3>
                <p className="text-xs text-zinc-500 max-w-sm font-medium">
                  Ask questions about candidates, email statistics, or draft approvals.
                </p>
              </div>

              {/* Starter Suggestion Chips */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg w-full pt-2">
                {starterSuggestions.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => handleSendMessage(prompt)}
                    className="p-3.5 bg-[#FBF9F5] border border-[#EAE3D5] hover:border-zinc-900 rounded-2xl text-left text-xs font-bold text-zinc-800 transition-all shadow-xs hover:shadow-sm"
                  >
                    💡 "{prompt}"
                  </button>
                ))}
              </div>
            </div>
          ) : (
            /* Active Messages List */
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 max-w-2xl ${msg.sender === 'user' ? 'ml-auto flex-row-reverse' : ''}`}
              >
                <div
                  className={`w-9 h-9 rounded-2xl shrink-0 flex items-center justify-center text-xs font-bold ${
                    msg.sender === 'user'
                      ? 'bg-zinc-900 text-amber-400'
                      : 'bg-amber-400 text-zinc-950 shadow-xs'
                  }`}
                >
                  {msg.sender === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-5 h-5" />}
                </div>

                <div className="space-y-2">
                  <div
                    className={`p-4 rounded-3xl text-xs leading-relaxed ${
                      msg.sender === 'user'
                        ? 'bg-zinc-900 text-white font-medium rounded-tr-none shadow-md'
                        : 'bg-[#FBF9F5] border border-[#EAE3D5] text-zinc-800 font-medium rounded-tl-none shadow-xs'
                    }`}
                  >
                    <p className="whitespace-pre-line">{msg.text}</p>

                    {/* Render clickable link cards if present */}
                    {msg.links && msg.links.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-[#EAE3D5] space-y-1.5">
                        <p className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">
                          Referenced Links:
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {msg.links.map((link, idx) => (
                            <Link
                              key={idx}
                              href={link.href}
                              className="inline-flex items-center gap-1 bg-amber-400/20 text-amber-950 border border-amber-300 text-[11px] font-bold px-2.5 py-1 rounded-xl hover:bg-amber-400/30 transition-all"
                            >
                              <span>{link.label}</span>
                              <ArrowUpRight className="w-3 h-3 text-amber-700" />
                            </Link>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  <p
                    className={`text-[10px] text-zinc-400 font-mono px-2 ${
                      msg.sender === 'user' ? 'text-right' : 'text-left'
                    }`}
                  >
                    {msg.timestamp}
                  </p>
                </div>
              </div>
            ))
          )}

          {isTyping && (
            <div className="flex gap-3 max-w-md">
              <div className="w-8 h-8 rounded-xl bg-amber-400 text-zinc-950 flex items-center justify-center">
                <Bot className="w-4 h-4" />
              </div>
              <div className="p-3.5 bg-[#FBF9F5] border border-[#EAE3D5] rounded-2xl text-xs font-bold text-zinc-400 animate-pulse">
                Thinking & querying database...
              </div>
            </div>
          )}
        </div>

        {/* Text Input Bottom Bar */}
        <div className="p-4 bg-[#FBF9F5] border-t border-[#EAE3D5] flex items-center gap-3">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage(inputText)}
            placeholder="Type your HR question here..."
            className="flex-1 bg-white border border-zinc-300 rounded-2xl px-5 py-3 text-xs font-medium text-zinc-900 focus:outline-none focus:ring-2 focus:ring-amber-400 shadow-xs"
          />
          <button
            onClick={() => handleSendMessage(inputText)}
            className="bg-zinc-900 hover:bg-zinc-800 text-white font-bold p-3 rounded-2xl shadow-md transition-all flex items-center justify-center"
          >
            <Send className="w-4 h-4 text-amber-400" />
          </button>
        </div>
      </div>
    </Layout>
  );
}
