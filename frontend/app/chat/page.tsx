// frontend/app/chat/page.tsx
'use client';
import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';
import Link from 'next/link';
// 1. Import useCompletion
import { useCompletion } from '@ai-sdk/react';

// 2. Define our Message type
type ChatMessage = { id: string; role: 'user' | 'assistant'; content: string };

export default function ChatPage() {
    const supabase = createClient();
    const router = useRouter();
    const [userId, setUserId] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // 3. We now MANUALLY manage the messages list, just like your original code
    const [messages, setMessages] = useState<ChatMessage[]>([{ id: 'welcome', role: 'assistant', content: "Hello! I'm your Dining Bot. How can I help you find food today?" }]);

    // 4. This auth check is correct
    useEffect(() => {
        const checkUserSession = async () => {
            const { data, error } = await supabase.auth.getUser();
            if (error || !data.user) {
                router.push('/');
            } else {
                setUserId(data.user.id);
            }
        };
        checkUserSession();
    }, [supabase, router]);

    // 5. This is the CORRECT hook: useCompletion
    const {
        completion, // This is the INCOMING AI message
        input,
        handleInputChange, // This exists!
        handleSubmit, // This exists!
        error,
        isLoading,
        stop, // We'll use this to set messages on finish
    } = useCompletion({
        api: '/api/ai-chat', // Points to our new route
        // This callback is the key:
        onFinish: (prompt, completion) => {
            // When the AI is done, add the user's prompt and the AI's final response to our list
            const userMsg: ChatMessage = { id: crypto.randomUUID(), role: 'user', content: prompt };
            const assistantMsg: ChatMessage = { id: crypto.randomUUID(), role: 'assistant', content: completion };
            setMessages((prev) => [...prev, userMsg, assistantMsg]);
        },
        // We pass the user_id in the body
        body: {
            user_id: userId,
        },
    });

    // 6. This auto-scroll is correct
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, completion]); // Also scroll as new completion chunks arrive

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
                {/* 7. Render our manual message list */}
                {messages.map((m) => (
                    <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg whitespace-pre-wrap ${m.role === 'user' ? 'bg-[#881C1B] text-white' : 'bg-gray-200 text-gray-900'}`}>
                            {m.content}
                        </div>
                    </div>
                ))}

                {/* 8. Render the LIVE streaming completion (if not loading) */}
                {isLoading && (
                    <div className="flex justify-start">
                        <div className="max-w-xs lg:max-w-md px-4 py-2 rounded-lg bg-gray-200 text-gray-900 whitespace-pre-wrap">
                            {completion}
                            <span className="ml-1 animate-pulse">▍</span>
                        </div>
                    </div>
                )}

                {error && (
                    <div className="flex justify-start">
                        <div className="max-w-xs lg:max-w-md px-4 py-2 rounded-lg bg-red-100 text-red-700">
                            <p>
                                <strong>Error:</strong> {error.message}
                            </p>
                            <p className="text-sm">Ensure backend at http://localhost:8000 is running.</p>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* 9. Use the hook's native handleSubmit */}
            <form onSubmit={handleSubmit} className="p-4 border-t bg-white">
                <div className="flex flex-col gap-2 max-w-3xl mx-auto">
                    <label htmlFor="chat-input" className="sr-only">
                        Your message
                    </label>
                    <textarea
                        id="chat-input"
                        name="prompt"
                        value={input}
                        onChange={handleInputChange}
                        placeholder="Ask me for restaurant ideas, cuisines, locations..."
                        className="w-full resize-none rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#881C1B] bg-white disabled:opacity-50"
                        rows={3}
                        disabled={isLoading}
                    />
                    <div className="flex items-center gap-2">
                        <button
                            type="submit"
                            disabled={isLoading || !input.trim()}
                            className="px-4 py-2 rounded-md bg-[#881C1B] text-white text-sm font-medium hover:bg-[#6d1615] disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isLoading ? 'Sending...' : 'Send'}
                        </button>
                        {isLoading && (
                            <button type="button" onClick={() => stop()} className="px-3 py-2 rounded-md bg-gray-200 text-gray-800 text-sm hover:bg-gray-300">
                                Stop
                            </button>
                        )}
                    </div>
                    <p className="text-xs text-gray-500">Dining Bot can suggest nearby restaurants, cuisines, budgets, and more.</p>
                </div>
            </form>
        </main>
    );
}
