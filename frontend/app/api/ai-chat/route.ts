// AI chat streaming proxy route (Edge runtime)
export const runtime = 'edge';

// 1. Get the URL from the environment (or fallback). Avoid direct `process` typing in Edge.
interface GlobalWithProcess {
    process?: { env?: { BACKEND_URL?: string } };
}
const FASTAPI_URL = (globalThis as unknown as GlobalWithProcess).process?.env?.BACKEND_URL || 'http://localhost:8000/api/chat';

export async function POST(req: Request) {
    try {
        const body = await req.json();
        let response: Response;

        // Prefer forwarding full messages (for memory). Fallback to single prompt format.
        if (body.messages && Array.isArray(body.messages)) {
            const user_id = req.headers.get('X-User-ID') || null;
            response = await fetch(FASTAPI_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    messages: body.messages,
                    user_id,
                }),
            });
        } else if (body.prompt) {
            response = await fetch(FASTAPI_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: body.prompt,
                    user_id: body.user_id || null,
                }),
            });
        } else {
            return new Response('No prompt found', { status: 400 });
        }

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
