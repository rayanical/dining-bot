"use client";
import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';

type ChatMessage = { id: string; role: 'user' | 'assistant'; content: string };

export default function ChatPage() {
    const supabase = createClient();
    const router = useRouter();
    const [messages, setMessages] = useState<ChatMessage[]>([
        { id: 'welcome', role: 'assistant', content: "Hello! I'm your Dining Bot. How can I help you find food today?" }
    ]);
    const [input, setInput] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [isStreaming, setIsStreaming] = useState(false);

    useEffect(() => {
        const checkUserSession = async () => {
            const { data, error } = await supabase.auth.getUser();
            if (error || !data.user) {
                router.push('/');
            }
        };
        checkUserSession();
    }, [supabase, router]);

    const startStream = useCallback(async () => {
        const trimmed = input.trim();
        if (!trimmed || isStreaming) return;
        setError(null);
        setIsStreaming(true);
        const userMsg: ChatMessage = { id: crypto.randomUUID(), role: 'user', content: trimmed };
        const assistantMsg: ChatMessage = { id: crypto.randomUUID(), role: 'assistant', content: '' };
        setMessages(prev => [...prev, userMsg, assistantMsg]);
        setInput('');
        try {
            const resp = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ messages: [{ role: 'user', content: trimmed }] })
            });
            if (!resp.body) throw new Error('No response body');
            if (!resp.ok) {
                const t = await resp.text();
                throw new Error(t || `HTTP ${resp.status}`);
            }
            const reader = resp.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let done = false;
            while (!done) {
                const { value, done: doneReading } = await reader.read();
                done = doneReading;
                if (value) {
                    const chunk = decoder.decode(value, { stream: true });
                        if (chunk) {
                            setMessages(prev => prev.map(m => m.id === assistantMsg.id ? { ...m, content: m.content + chunk } : m));
                        }
                }
            }
            } catch (e) {
                const message = e instanceof Error ? e.message : 'Streaming error';
                setError(message);
        } finally {
            setIsStreaming(false);
        }
    }, [input, isStreaming]);

    return (
        <main className="flex flex-col h-screen">
            <header className="p-4 border-b shadow-sm bg-white">
                <h1 className="text-xl font-bold text-gray-900">Dining Bot</h1>
            </header>
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
                {messages.map(m => (
                    <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg whitespace-pre-wrap ${m.role === 'user' ? 'bg-[#881C1B] text-white' : 'bg-gray-200 text-gray-900'}`}>
                            {m.content}
                            {m.id === messages[messages.length - 1].id && isStreaming && m.role === 'assistant' && <span className="ml-1 animate-pulse">▍</span>}
                        </div>
                    </div>
                ))}
                {error && (
                    <div className="flex justify-start">
                        <div className="max-w-xs lg:max-w-md px-4 py-2 rounded-lg bg-red-100 text-red-700">
                            <p><strong>Error:</strong> {error}</p>
                            <p className="text-sm">Ensure backend at http://localhost:8000 is running.</p>
                        </div>
                    </div>
                )}
            </div>
            <form onSubmit={e => { e.preventDefault(); startStream(); }} className="p-4 border-t bg-white">
                <div className="flex space-x-2">
                    <input
                        type="text"
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        disabled={isStreaming}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-[#881C1B] focus:border-[#881C1B] text-gray-900 disabled:opacity-50"
                        placeholder="Ask for meal plans, calories, or dining hall menus..."
                    />
                    <button
                        type="submit"
                        disabled={isStreaming}
                        className="px-4 py-2 font-semibold text-white bg-[#881C1B] rounded-md hover:bg-[#6d1615] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#881C1B] disabled:opacity-50"
                    >
                        {isStreaming ? 'Streaming...' : 'Send'}
                    </button>
                </div>
            </form>
        </main>
    );
}
