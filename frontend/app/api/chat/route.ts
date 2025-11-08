// frontend/app/api/chat/route.ts
export const runtime = 'edge';

const FASTAPI_URL = 'http://localhost:8000/api/chat';

type ChatMessage = { id?: string; role: 'user' | 'assistant' | 'system'; content: string };

export async function POST(req: Request) {
  try {
    const { messages } = await req.json();

    const lastUserMessage: ChatMessage | undefined = (messages as ChatMessage[])
      .slice()
      .reverse()
      .find((m) => m.role === 'user');

    if (!lastUserMessage) {
      return new Response('No user message found', { status: 400 });
    }

    const response = await fetch(FASTAPI_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: lastUserMessage.content, user_id: null }),
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
    const errorStream = new ReadableStream({
      start(controller) {
        controller.enqueue(`An error occurred: ${message}`);
        controller.close();
      },
    });
    return new Response(errorStream, { status: 500, headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
  }
}
