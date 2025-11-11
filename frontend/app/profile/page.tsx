'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';

interface ConstraintDTO {
    constraint: string;
    constraint_type: string;
}

export default function ProfilePage() {
    /**
     * ProfilePage displays the authenticated user's saved dietary profile.
     *
     * Fetches the profile from the backend; if not found redirects to onboarding.
     * Provides logout and navigation back to chat.
     *
     * State:
     * - loading: Indicates initial fetch in progress.
     * - userEmail: Email derived from Supabase auth session.
     * - diets: List of diet preference strings.
     * - allergies: List of allergy constraint strings.
     * - goal: User's nutrition/health goal string or null.
     * - error: Error message if profile fetch fails.
     */
    const supabase = createClient();
    const router = useRouter();

    const [loading, setLoading] = useState(true);
    const [userEmail, setUserEmail] = useState<string>('');
    const [diets, setDiets] = useState<string[]>([]);
    const [allergies, setAllergies] = useState<string[]>([]);
    const [goal, setGoal] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const loadProfile = async () => {
            try {
                const { data, error } = await supabase.auth.getUser();
                if (error) {
                    router.push('/');
                    return;
                }
                if (!data.user) {
                    router.push('/');
                    return;
                }
                setUserEmail(data.user.email || '');

                // Fetch profile from backend
                const resp = await fetch(`http://localhost:8000/api/users/profile/${data.user.id}`);
                if (resp.status === 404) {
                    // No profile yet -> send them to onboarding
                    router.push('/onboarding');
                    return;
                }
                if (!resp.ok) {
                    setError(`Failed to load profile (status ${resp.status})`);
                    return;
                }
                const json = await resp.json();
                // Separate diets vs allergies based on constraint_type
                const constraints: ConstraintDTO[] = json.dietary_constraints || [];
                setDiets(constraints.filter((c) => c.constraint_type === 'preference').map((c) => c.constraint));
                setAllergies(constraints.filter((c) => c.constraint_type === 'allergy').map((c) => c.constraint));
                setGoal(json.goal || null);
            } catch {
                setError('Unexpected error loading profile');
            } finally {
                setLoading(false);
            }
        };
        loadProfile();
    }, [supabase, router]);

    const handleLogout = async () => {
        await supabase.auth.signOut();
        router.push('/');
    };

    if (loading) {
        return (
            <main className="flex items-center justify-center h-screen bg-gray-50">
                <p className="text-gray-600">Loading...</p>
            </main>
        );
    }

    return (
        <main className="min-h-screen bg-gray-50 p-6">
            <div className="max-w-2xl mx-auto bg-white shadow-sm rounded-lg p-6 space-y-6">
                <div className="flex items-center justify-between">
                    <h1 className="text-2xl font-bold text-gray-900">Your Profile</h1>
                    <button onClick={handleLogout} className="px-4 py-2 text-sm font-medium bg-red-600 text-white rounded-md hover:bg-red-700">
                        Log Out
                    </button>
                </div>
                {error && <div className="p-4 rounded-md bg-red-100 text-red-700 text-sm">{error}</div>}
                <section className="space-y-2">
                    <h2 className="text-lg font-semibold text-gray-800">Account</h2>
                    <p className="text-gray-700">
                        <span className="font-medium">Email:</span> {userEmail}
                    </p>
                </section>
                <section className="space-y-2">
                    <h2 className="text-lg font-semibold text-gray-800">Goal</h2>
                    <p className="text-gray-700">{goal || '—'}</p>
                </section>
                <section className="space-y-2">
                    <h2 className="text-lg font-semibold text-gray-800">Dietary Preferences</h2>
                    {diets.length ? (
                        <ul className="list-disc list-inside text-gray-700 space-y-1">
                            {diets.map((d) => (
                                <li key={d}>{d}</li>
                            ))}
                        </ul>
                    ) : (
                        <p className="text-gray-500 text-sm">None set.</p>
                    )}
                </section>
                <section className="space-y-2">
                    <h2 className="text-lg font-semibold text-gray-800">Allergies</h2>
                    {allergies.length ? (
                        <ul className="list-disc list-inside text-gray-700 space-y-1">
                            {allergies.map((a) => (
                                <li key={a}>{a}</li>
                            ))}
                        </ul>
                    ) : (
                        <p className="text-gray-500 text-sm">None recorded.</p>
                    )}
                </section>
                <div>
                    <button onClick={() => router.push('/chat')} className="mt-4 inline-block px-5 py-2 bg-[#881C1B] text-white rounded-md hover:bg-[#6d1615]">
                        Back to Chat
                    </button>
                </div>
            </div>
        </main>
    );
}
