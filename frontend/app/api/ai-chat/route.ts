// AI chat streaming proxy route (Edge runtime)
export const runtime = 'edge';

// 1. Get the URL from the environment (or fallback). Avoid direct `process` typing in Edge.
interface GlobalWithProcess {
    process?: { env?: { BACKEND_URL?: string } };
}
const FASTAPI_URL = (globalThis as unknown as GlobalWithProcess).process?.env?.BACKEND_URL || 'http://localhost:8000/api/chat';

export async function POST(req: Request) {
    try {
        const { prompt, user_id } = await req.json();

        if (!prompt) {
            return new Response('No prompt found', { status: 400 });
        }

        const response = await fetch(FASTAPI_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: prompt,
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

        return new Response(response.body, {
            headers: { 'Content-Type': 'text/plain; charset=utf-8' },
        });
    } catch (error) {
        const message = error instanceof Error ? error.message : 'Unknown error';
        return new Response(`An error occurred: ${message}`, { status: 500 });
    }
}
