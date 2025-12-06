'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

type FoodResult = {
    id: number;
    item: string;
    dining_hall: string;
    calories: number | null;
    protein_g: number | null;
    availability_today: string[] | null;
};

const mealOptions = ['Breakfast', 'Lunch', 'Dinner', "Grab' n Go", 'Late Night'] as const;

export default function FoodLogPage() {
    const supabase = createClient();
    const router = useRouter();

    const [userId, setUserId] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [results, setResults] = useState<FoodResult[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [mealType, setMealType] = useState<string>('Dinner');
    const [logStatus, setLogStatus] = useState<string | null>(null);
    const [logDate, setLogDate] = useState<string>(new Date().toISOString().slice(0, 10));

    // Auth check
    useEffect(() => {
        const checkUser = async () => {
            const { data, error } = await supabase.auth.getUser();
            if (error || !data.user) {
                router.push('/login');
                return;
            }
            setUserId(data.user.id);
        };
        checkUser();
    }, [router, supabase]);

    const handleSearch = async (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!searchTerm.trim()) return;
        setLoading(true);
        setError(null);
        setLogStatus(null);
        try {
            const params = new URLSearchParams({ q: searchTerm, limit: '10' });
            if (userId) params.append('user_id', userId);
            const res = await fetch(`${BACKEND_URL}/api/food/search?${params.toString()}`);
            if (!res.ok) {
                throw new Error(await res.text());
            }
            const data = await res.json();
            setResults(data.results || []);
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : 'Search failed';
            setError(message);
        } finally {
            setLoading(false);
        }
    };

    const handleLog = async (item: FoodResult) => {
        if (!userId) {
            setError('Not signed in');
            return;
        }
        setLogStatus(null);
        setError(null);
        try {
            const payload = {
                item_name: item.item,
                calories: item.calories ?? 0,
                protein: item.protein_g ?? 0,
                meal_type: mealType.toLowerCase(),
                date: logDate,
            };
            const res = await fetch(`${BACKEND_URL}/api/users/${userId}/log-food`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            if (!res.ok) {
                throw new Error(await res.text());
            }
            setLogStatus(`Logged ${item.item} for ${mealType}`);
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : 'Failed to log food';
            setError(message);
        }
    };

    return (
        <main className="max-w-4xl mx-auto p-6 space-y-6">
            <header className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Food Log</h1>
                    <p className="text-sm text-gray-600">Search dining hall items and save them to your history.</p>
                </div>
                <button onClick={() => router.push('/chat')} className="px-4 py-2 rounded-md bg-[#881C1B] text-white hover:bg-[#6d1615]">
                    Back to Chat
                </button>
            </header>

            <form onSubmit={handleSearch} className="space-y-3">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                    <input
                        type="text"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        placeholder="Search for food (e.g., grilled cheese)"
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-[#881C1B] focus:border-[#881C1B]"
                    />
                    <button type="submit" disabled={loading} className="px-4 py-2 rounded-md bg-[#881C1B] text-white hover:bg-[#6d1615] disabled:opacity-50">
                        {loading ? 'Searching…' : 'Search'}
                    </button>
                </div>
                <div className="flex flex-wrap gap-3 items-center">
                    <label className="text-sm font-medium text-gray-700">Meal:</label>
                    <select value={mealType} onChange={(e) => setMealType(e.target.value)} className="px-3 py-2 border border-gray-300 rounded-md">
                        {mealOptions.map((m) => (
                            <option key={m} value={m}>
                                {m}
                            </option>
                        ))}
                    </select>
                    <label className="text-sm font-medium text-gray-700">Date:</label>
                    <input type="date" value={logDate} onChange={(e) => setLogDate(e.target.value)} className="px-3 py-2 border border-gray-300 rounded-md" />
                </div>
            </form>

            {error && <div className="text-red-600 text-sm">{error}</div>}
            {logStatus && <div className="text-green-700 text-sm">{logStatus}</div>}

            <section className="space-y-3">
                <h2 className="text-lg font-semibold text-gray-900">Results</h2>
                {results.length === 0 && <p className="text-sm text-gray-600">No results yet. Try a search.</p>}
                <div className="grid gap-3">
                    {results.map((item) => (
                        <div key={item.id} className="border rounded-md p-3 bg-white shadow-sm">
                            <div className="flex justify-between items-start gap-3">
                                <div>
                                    <p className="font-semibold text-gray-900">{item.item}</p>
                                    <p className="text-sm text-gray-600">{item.dining_hall}</p>
                                    <p className="text-sm text-gray-600">
                                        {item.calories ? `${item.calories} kcal` : 'Calories N/A'} · {item.protein_g ?? 0} g protein
                                    </p>
                                    {item.availability_today && <p className="text-xs text-gray-500">Meals: {item.availability_today.join(', ')}</p>}
                                </div>
                                <button onClick={() => handleLog(item)} className="px-3 py-2 rounded-md bg-gray-900 text-white hover:bg-gray-700 text-sm">
                                    Log
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </section>
        </main>
    );
}
