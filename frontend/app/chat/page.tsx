'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';
// Define a type for our chat messages
type Message = {
    id: number;
    text: string;
    sender: 'user' | 'bot';
};

export default function ChatPage() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');

    const supabase = createClient();
    const router = useRouter();
    useEffect(() => {
        const checkUserSession = async () => {
            const { data, error } = await supabase.auth.getUser();

            if (error || !data.user) {
                console.log('No user session found. Redirecting to login.');
                router.push('/'); // Redirect to login if not authenticated
            } else {
                console.log('User session verified:', data.user.id);
            }
        };

        checkUserSession();
    }, [supabase, router]); 

    // Greet the user on page load
    useEffect(() => {
        setMessages([
            {
                id: 1,
                text: "Hello! I'm your Dining Bot. How can I help you find food today?",
                sender: 'bot',
            },
        ]);
    }, []);

    const handleSend = async () => {
        if (input.trim() === '') return;

        const userMessage: Message = {
            id: messages.length + 1,
            text: input,
            sender: 'user',
        };

        // Add loading message
        const loadingMessage: Message = {
            id: messages.length + 2,
            text: "Thinking...",
            sender: 'bot',
        };

        setMessages([...messages, userMessage, loadingMessage]);
        const currentInput = input;
        setInput('');

        try {
            const response = await fetch('http://localhost:8000/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: currentInput }),
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();

            // Replace loading message with real answer
            setMessages(prev => [
                ...prev.slice(0, prev.length - 1),
                {
                    id: prev.length,
                    text: data.answer || "Sorry, I couldn't generate a response.",
                    sender: 'bot',
                },
            ]);
        } catch (error: any) {
            console.error('Error:', error);
            const errorMessage = error.message || "Sorry, I encountered an error. Please try again.";
            setMessages(prev => [
                ...prev.slice(0, prev.length - 1),
                {
                    id: prev.length,
                    text: `Error: ${errorMessage}. Make sure the backend is running on http://localhost:8000`,
                    sender: 'bot',
                },
            ]);
        }
    };

    return (
        <main className="flex flex-col h-screen">
            {/* Header */}
            <header className="p-4 border-b shadow-sm bg-white">
                <h1 className="text-xl font-bold text-gray-900">Dining Bot</h1>
            </header>

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
                {messages.map((message) => (
                    <div key={message.id} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${message.sender === 'user' ? 'bg-[#881C1B] text-white' : 'bg-gray-200 text-gray-900'}`}>
                            {message.text}
                        </div>
                    </div>
                ))}
            </div>

            {/* Message Input */}
            <div className="p-4 border-t bg-white">
                <div className="flex space-x-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-[#881C1B] focus:border-[#881C1B] text-gray-900"
                        placeholder="Ask for meal plans, calories, or dining hall menus..."
                    />
                    <button
                        onClick={handleSend}
                        className="px-4 py-2 font-semibold text-white bg-[#881C1B] rounded-md hover:bg-[#6d1615] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#881C1B]"
                    >
                        Send
                    </button>
                </div>
            </div>
        </main>
    );
}
