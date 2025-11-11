// frontend/app/api/ai-chat/route.ts
export const runtime = 'edge';

// 1. Get the URL from the environment (or fallback)
const FASTAPI_URL = process.env.BACKEND_URL || 'http://localhost:8000/api/chat';

export async function POST(req: Request) {
    try {
        // 2. useCompletion sends 'prompt' and our custom 'user_id'
        const { prompt, user_id } = await req.json();

        if (!prompt) {
            return new Response('No prompt found', { status: 400 });
        }

        // 3. Call the Python backend, passing 'query' and 'user_id'
        const response = await fetch(FASTAPI_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: prompt, // useCompletion sends 'prompt'
                user_id: user_id,
            }),
        });

        if (!response.ok) {
            const errorText = await response.text();
            return new Response(`FastAPI backend error: ${response.status} ${errorText}`, { status: 502 });
        }

        if (!response.body) {
            return new Response('FastAPI backend returned an empty response body', { status: 502 });
        }

        // 4. Return the raw text stream directly. useCompletion understands this.
        return new Response(response.body, {
            headers: { 'Content-Type': 'text/plain; charset=utf-8' },
        });
    } catch (error) {
        const message = error instanceof Error ? error.message : 'Unknown error';
        return new Response(`An error occurred: ${message}`, { status: 500 });
    }
}
