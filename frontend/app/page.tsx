'use client';
import { useEffect, useState } from 'react';

export default function Home() {
    const [message, setMessage] = useState('Loading...');

    useEffect(() => {
        fetch('http://localhost:8000/api/test/')
            .then((res) => res.json())
            .then((data) => setMessage(data.message))
            .catch(() => setMessage('Backend not running'));
    }, []);

    return (
        <main className="flex flex-col items-center justify-center h-screen">
            <h1 className="text-3xl font-bold mb-4">Dining Bot</h1>
            <p>{message}</p>
        </main>
    );
}
