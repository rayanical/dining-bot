'use client';
import { useState, useEffect } from 'react';

// Define a type for our chat messages
type Message = {
    id: number;
    text: string;
    sender: 'user' | 'bot';
};

export default function ChatPage() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');

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

    const handleSend = () => {
        if (input.trim() === '') return;

        // Add user's message
        const userMessage: Message = {
            id: messages.length + 1,
            text: input,
            sender: 'user',
        };

        // Add a placeholder bot response
        const botMessage: Message = {
            id: messages.length + 2,
            text: `Thinking about "${input}"...`, // Placeholder
            sender: 'bot',
        };

        setMessages([...messages, userMessage, botMessage]);
        setInput('');

        // In a real app, you would send `input` to your backend API here
        // and replace the bot's placeholder message with the real response.
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
