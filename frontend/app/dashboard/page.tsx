'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

type MacroSummary = {
    total: number;
    target: number;
};

type DailySummary = {
    status: string;
    date: string;
    goal: string | null;
    calories: MacroSummary;
    protein: MacroSummary;
};

function ProgressBar({ label, summary }: { label: string; summary: MacroSummary }) {
    const pct = summary.target > 0 ? Math.min(100, Math.round((summary.total / summary.target) * 100)) : 0;
    return (
        <div className="space-y-1">
            <div className="flex items-center justify-between text-sm text-gray-700">
                <span className="font-medium">{label}</span>
                <span>
                    {Math.round(summary.total)} / {Math.round(summary.target)}
                </span>
            </div>
            <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
                <div className="h-full bg-[#881C1B]" style={{ width: `${pct}%` }} />
            </div>
            <p className="text-xs text-gray-500">{pct}% of target</p>
        </div>
    );
}

export default function DashboardPage() {
    const supabase = createClient();
    const router = useRouter();

    const [userId, setUserId] = useState<string | null>(null);
    const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().slice(0, 10));
    const [summary, setSummary] = useState<DailySummary | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const checkAuth = async () => {
            const { data, error } = await supabase.auth.getUser();
            if (error || !data.user) {
                router.push('/login');
                return;
            }
            setUserId(data.user.id);
        };
        checkAuth();
    }, [router, supabase]);

    useEffect(() => {
        const fetchSummary = async () => {
            if (!userId) return;
            setLoading(true);
            setError(null);
            try {
                const res = await fetch(`${BACKEND_URL}/api/users/${userId}/daily-summary?date=${selectedDate}`);
                if (!res.ok) {
                    throw new Error(`Failed to load summary (status ${res.status})`);
                }
                const json: DailySummary = await res.json();
                setSummary(json);
            } catch (err: unknown) {
                const message = err instanceof Error ? err.message : 'Failed to load summary';
                setError(message);
                setSummary(null);
            } finally {
                setLoading(false);
            }
        };
        fetchSummary();
    }, [selectedDate, userId]);

    if (!userId) {
        return (
            <main className="flex items-center justify-center h-screen bg-gray-50">
                <p className="text-gray-600">Checking session...</p>
            </main>
        );
    }

    return (
        <main className="min-h-screen bg-gray-50 p-6">
            <div className="max-w-3xl mx-auto bg-white shadow-sm rounded-lg p-6 space-y-6">
                <header className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">Nutrition Dashboard</h1>
                        <p className="text-sm text-gray-600">Daily intake vs targets</p>
                    </div>
                    <div className="flex gap-2">
                        <button onClick={() => router.push('/chat')} className="px-4 py-2 rounded-md bg-gray-900 text-white hover:bg-gray-700 text-sm">
                            Chat
                        </button>
                        <button onClick={() => router.push('/dashboard/log')} className="px-4 py-2 rounded-md bg-[#881C1B] text-white hover:bg-[#6d1615] text-sm">
                            Log Food
                        </button>
                    </div>
                </header>

                <div className="flex flex-wrap items-center gap-3">
                    <label className="text-sm font-medium text-gray-700">Date:</label>
                    <input type="date" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)} className="px-3 py-2 border border-gray-300 rounded-md" />
                </div>

                {loading && <p className="text-gray-600 text-sm">Loading summary...</p>}
                {error && <p className="text-red-600 text-sm">{error}</p>}

                {summary && !loading && !error && (
                    <section className="space-y-4">
                        <div className="flex items-center justify-between text-sm text-gray-700">
                            <div>
                                <p className="font-semibold text-gray-900">Goal</p>
                                <p className="text-gray-600">{summary.goal || 'Not set'}</p>
                            </div>
                            <p className="text-gray-500">{summary.date}</p>
                        </div>
                        <ProgressBar label="Calories" summary={summary.calories} />
                        <ProgressBar label="Protein" summary={summary.protein} />
                    </section>
                )}
            </div>
        </main>
    );
}
