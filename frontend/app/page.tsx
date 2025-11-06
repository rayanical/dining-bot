/*'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const router = useRouter();

    const handleLogin = (e: React.FormEvent) => {
        e.preventDefault();
        // Handle authentication here
        router.push('/onboarding');
    };

    return (
        <main className="flex flex-col items-center justify-center h-screen bg-gray-50">
            <div className="w-full max-w-md p-8 space-y-6 bg-white shadow-md rounded-lg">
                <h1 className="text-3xl font-bold text-center text-gray-900">Dining Bot Login</h1>
                <form onSubmit={handleLogin} className="space-y-6">
                    <div>
                        <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                            Email Address
                        </label>
                        <input
                            id="email"
                            name="email"
                            type="email"
                            autoComplete="email"
                            required
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-[#881C1B] focus:border-[#881C1B] text-gray-900"
                            placeholder="you@umass.edu"
                        />
                    </div>
                    <div>
                        <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                            Password
                        </label>
                        <input
                            id="password"
                            name="password"
                            type="password"
                            autoComplete="current-password"
                            required
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-[#881C1B] focus:border-[#881C1B] text-gray-900"
                            placeholder="••••••••"
                        />
                    </div>
                    <button
                        type="submit"
                        className="w-full px-4 py-2 font-semibold text-white bg-[#881C1B] rounded-md hover:bg-[#6d1615] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#881C1B]"
                    >
                        Sign In
                    </button>
                </form>
            </div>
        </main>
    );
}
*/


'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
// 1. Import your client helper (assuming it's in 'lib/supabase/client')
import { createClient } from '@/lib/supabase/client'; 

export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const router = useRouter();
    // 2. Initialize the Supabase client
    const supabase = createClient();

    const handleLogin = (e: React.FormEvent) => {
        e.preventDefault();
        // Handle email/password auth here
        router.push('/onboarding');
    };

    // 3. Add the Google Sign-In handler
    const handleGoogleSignIn = async () => {
        await supabase.auth.signInWithOAuth({
            provider: 'google',
            options: {
                // This must be an absolute URL
                // It points to the callback route you'll create in Step 2
                redirectTo: `${location.origin}/auth/callback`,
            },
        });
    };

    return (
        <main className="flex flex-col items-center justify-center h-screen bg-gray-50">
            <div className="w-full max-w-md p-8 space-y-6 bg-white shadow-md rounded-lg">
                <h1 className="text-3xl font-bold text-center text-gray-900">Dining Bot Login</h1>
                
                {/* Email/Password Form 
                <form onSubmit={handleLogin} className="space-y-6">
                    {/* ... (your email and password inputs) ... 
                    <button
                        type="submit"
                        className="w-full px-4 py-2 font-semibold text-white bg-[#881C1B] rounded-md hover:bg-[#6d1615] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#881C1B]"
                    >
                        Sign In
                    </button>
                </form>*/}

                {/* "OR" Divider 
                <div className="relative my-4">
                    <div className="absolute inset-0 flex items-center">
                        <span className="w-full border-t border-gray-300"></span>
                    </div>
                    <div className="relative flex justify-center text-sm">
                        <span className="px-2 bg-white text-gray-500">
                            Or continue with
                        </span>
                    </div>
                </div>*/}

                {/* 4. Add the Google Sign-In Button */}
                <button
                    type="button" 
                    onClick={handleGoogleSignIn}
                    className="w-full flex items-center justify-center px-4 py-2 font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#881C1B]"
                >
                    <svg className="w-5 h-5 mr-3" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid" viewBox="0 0 256 262">
                        <path fill="#4285F4" d="M255.878 133.451c0-10.734-.871-18.567-2.756-26.69H130.55v48.448h71.045c-2.88 15.423-12.016 29.192-25.99 38.369v31.33h38.656c22.6-20.73 35.84-51.084 35.84-86.87Z"/>
                        <path fill="#34A853" d="M130.55 261.1c35.24 0 64.8-11.666 86.4-31.33l-38.656-31.33c-11.666 7.8-26.69 12.016-47.744 12.016-36.602 0-67.8-24.86-78.89-58.064H12.016v31.33C34.33 234.8 79.18 261.1 130.55 261.1Z"/>
                        <path fill="#FBBC05" d="M51.66 154.064c-4.75-14.24-7.4-29.19-7.4-44.18s2.65-29.94 7.4-44.18V34.42H12.016C4.24 53.04 0 77.29 0 104.88s4.24 51.84 12.016 70.46l39.644-31.28Z"/>
                        <path fill="#EB4335" d="M130.55 50.88c19.12 0 36.602 6.55 50.48 19.66l34.42-34.42C195.35 15.96 165.79 0 130.55 0 79.18 0 34.33 26.3 12.016 65.58l39.644 31.28c11.09-33.204 42.288-58.064 78.89-58.064Z"/>
                    </svg>
                    Sign in with Google
                </button>
            </div>
        </main>
    );
}