import { createServerClient, type CookieOptions } from '@supabase/ssr';
import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get('code');
  const origin = requestUrl.origin;

  if (code) {
    // Add 'await' here to resolve the promise
    const cookieStore = await cookies(); 
    
    const supabase = createServerClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
      {
        cookies: {
          get(name: string) {
            return cookieStore.get(name)?.value;
          },
          set(name: string, value: string, options: CookieOptions) {
            // Now cookieStore is the resolved object, so .set() exists
            cookieStore.set({ name, value, ...options });
          },
          remove(name: string, options: CookieOptions) {
            // And .delete() exists
            cookieStore.delete({ name, ...options });
          },
        },
      }
    );
    
    // Exchange the code for a session
    const { error } = await supabase.auth.exchangeCodeForSession(code);

    if (!error) {
      // URL to redirect to after sign-in completes
      // This will take the user back to the home page.
      // You can change this to '/onboarding' or any other page.
      return NextResponse.redirect(`${origin}/login-check`);
    }
  }

  // If there's no code or an error, redirect to an error page or home
  // It's good practice to have an error page
  console.error('Error exchanging code for session in auth callback');
  return NextResponse.redirect(`${origin}/?error=auth_failed`);
}