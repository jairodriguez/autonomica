// Chat route that connects to Autonomica OWL backend

export async function POST(req: Request) {
  try {
    console.log('Chat API called - routing to Autonomica backend');
    const { messages } = await req.json();
    console.log('Messages:', messages?.length);

    // Get the last user message to send to our backend
    const lastMessage = messages[messages.length - 1];
    
    if (!lastMessage || lastMessage.role !== 'user') {
      return new Response('Invalid message format', { status: 400 });
    }

    console.log('Sending to Autonomica API backend...');
    
    // Call our FastAPI backend
    const response = await fetch('http://localhost:8000/api/workflows/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: lastMessage.content,
        context: messages.slice(0, -1), // Previous conversation context
      }),
    });

    if (!response.ok) {
      console.error('Backend response error:', response.status, response.statusText);
      return new Response(JSON.stringify({ error: 'Backend service unavailable' }), { 
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Check if the response is a stream
    if (response.headers.get('content-type')?.includes('text/stream')) {
      // Forward the stream from backend
      return new Response(response.body, {
        headers: {
          'Content-Type': 'text/plain; charset=utf-8',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        },
      });
    } else {
      // Handle JSON response
      const data = await response.json();
      
      // Convert to Vercel AI SDK streaming format
      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        start(controller) {
          try {
            // Send the response content as chunks
            const content = data.response || data.message || 'No response from agents';
            const chunks = content.split(' ');
            
            // Send initial message ID
            controller.enqueue(encoder.encode(`f:{"messageId":"msg-${Date.now()}"}\n`));
            
            // Send content in chunks
            chunks.forEach((chunk: string, index: number) => {
              const text = index === 0 ? chunk : ` ${chunk}`;
              controller.enqueue(encoder.encode(`0:"${text.replace(/"/g, '\\"')}"\n`));
            });
            
            // End the stream
            controller.enqueue(encoder.encode(`e:{"finishReason":"stop","usage":{"promptTokens":50,"completionTokens":${chunks.length}},"isContinued":false}\n`));
            controller.enqueue(encoder.encode(`d:{"finishReason":"stop","usage":{"promptTokens":50,"completionTokens":${chunks.length}}}\n`));
            controller.close();
            
            console.log('Response stream completed');
          } catch (error) {
            console.error('Stream processing error:', error);
            controller.error(error);
          }
        },
      });

      return new Response(stream, {
        headers: {
          'Content-Type': 'text/plain; charset=utf-8',
          'Cache-Control': 'no-cache',
          'x-vercel-ai-data-stream': 'v1',
        },
      });
    }
  } catch (error) {
    console.error('Chat error:', error);
    return new Response(JSON.stringify({ error: error instanceof Error ? error.message : 'Unknown error' }), { 
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
} 