'use client';
import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';
import Link from 'next/link';
import { useChat } from '@ai-sdk/react';
import { TextStreamChatTransport } from 'ai';

// Local UI typing helpers (AI SDK uses message.parts)
type TextPart = { type: 'text'; text: string };
type ChatRole = 'user' | 'assistant' | 'system';
type ChatUIMessage = { id?: string; role: ChatRole; parts: TextPart[] };

export default function ChatPage() {
    const supabase = createClient();
    const router = useRouter();
    const [userId, setUserId] = useState<string | null>(null);
    const inputRef = useRef<HTMLInputElement>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const [input, setInput] = useState('');

    // Initialize chat hook using TextStream transport to consume plain text streams from our edge route
    const { messages, sendMessage, status, error, stop } = useChat({
        messages: [
            {
                id: 'welcome',
                role: 'assistant',
                parts: [{ type: 'text', text: "Hello! I'm your Dining Bot. How can I help you find food today?" }],
            },
        ],
        transport: new TextStreamChatTransport({
            api: '/api/ai-chat',
            headers: () => ({ 'X-User-ID': userId || '' }),
        }),
        onFinish() {
            // Refocus input after streaming completes.
            inputRef.current?.focus();
        },
    });

    // Auth check and initial focus.
    useEffect(() => {
        const checkUserSession = async () => {
            const { data, error } = await supabase.auth.getUser();
            if (error || !data.user) {
                router.push('/');
            } else {
                setUserId(data.user.id);
                inputRef.current?.focus();
            }
        };
        checkUserSession();
    }, [supabase, router]);

    // Auto-scroll to latest message on update.
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
        <main className="flex flex-col h-screen">
            <header className="p-4 border-b shadow-sm bg-white">
                <div className="flex items-center justify-between">
                    <h1 className="text-xl font-bold text-gray-900">Dining Bot</h1>
                    <Link href="/profile" className="text-[#881C1B] hover:underline font-medium">
                        Profile
                    </Link>
                </div>
            </header>
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
                {messages.map((m: ChatUIMessage) => (
                    <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg whitespace-pre-wrap ${m.role === 'user' ? 'bg-[#881C1B] text-white' : 'bg-gray-200 text-gray-900'}`}>
                            {m.parts?.map((part, i) => (part.type === 'text' ? <span key={`${m.id}-${i}`}>{part.text}</span> : null))}
                            {m.id === messages[messages.length - 1]?.id && status === 'streaming' && m.role === 'assistant' && <span className="ml-1 animate-pulse">▍</span>}
                        </div>
                    </div>
                ))}

                {error && (
                    <div className="flex justify-start">
                        <div className="max-w-xs lg:max-w-md px-4 py-2 rounded-lg bg-red-100 text-red-700">
                            <p>
                                <strong>Error:</strong> {String(error)}
                            </p>
                            <p className="text-sm">Ensure backend at http://localhost:8000 is running.</p>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>
            <form
                onSubmit={(e) => {
                    e.preventDefault();
                    if (!input.trim()) return;
                    sendMessage({ text: input });
                    setInput('');
                }}
                className="p-4 border-t bg-white"
            >
                <div className="flex space-x-2">
                    <input
                        ref={inputRef}
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        readOnly={status === 'submitted' || status === 'streaming'}
                        className={`flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-[#881C1B] focus:border-[#881C1B] text-gray-900 ${
                            status === 'submitted' || status === 'streaming' ? 'opacity-50' : ''
                        }`}
                        placeholder="Ask for meal plans, calories, or dining hall menus..."
                    />
                    <button
                        type="submit"
                        disabled={!input.trim() || status === 'submitted' || status === 'streaming'}
                        className="px-4 py-2 font-semibold text-white bg-[#881C1B] rounded-md hover:bg-[#6d1615] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#881C1B] disabled:opacity-50"
                    >
                        {status === 'submitted' || status === 'streaming' ? 'Streaming...' : 'Send'}
                    </button>
                    {(status === 'submitted' || status === 'streaming') && (
                        <button
                            type="button"
                            onClick={() => stop()}
                            className="px-4 py-2 font-semibold text-[#881C1B] border border-[#881C1B] rounded-md hover:bg-[#881C1B] hover:text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#881C1B]"
                        >
                            Abort
                        </button>
                    )}
                </div>
            </form>
        </main>
    );
}
