// Chat route that connects to Autonomica OWL backend with tool-enabled agents

export async function POST(req: Request) {
  try {
    console.log('Chat API called - routing to Autonomica OWL backend');
    const { messages, agentContext } = await req.json();
    console.log('Messages:', messages?.length);
    console.log('Agent Context:', agentContext?.name, agentContext?.type);

    // Get the last user message to send to our backend
    const lastMessage = messages[messages.length - 1];
    
    if (!lastMessage || lastMessage.role !== 'user') {
      return new Response('Invalid message format', { status: 400 });
    }

    console.log('Sending to Autonomica OWL API backend...');
    
    // Call our FastAPI backend with new endpoint
    const response = await fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: lastMessage.content,
        context: messages.slice(0, -1), // Previous conversation context
        agent_type: agentContext?.type || 'ceo_agent',
        agent_name: agentContext?.name || 'CEO Agent',
      }),
    });

    if (!response.ok) {
      console.error('Backend response error:', response.status, response.statusText);
      return new Response(JSON.stringify({ error: 'Backend service unavailable' }), { 
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Handle JSON response from tool-enabled agents
    const data = await response.json();
    console.log('Agent response:', {
      agent: data.agent_name,
      type: data.agent_type,
      tools_used: data.metadata?.tools_used?.length || 0,
      status: data.metadata?.status
    });
    
    // Convert to Vercel AI SDK streaming format
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        try {
          // Get response content
          const content = data.message || 'No response from agents';
          
          // Create agent info header
          const agentInfo = `[${data.agent_name} - ${data.agent_type.replace('_', ' ').toUpperCase()}]`;
          const toolsInfo = data.metadata?.tools_used?.length > 0 
            ? ` (Used ${data.metadata.tools_used.length} tools)` 
            : '';
          
          const fullContent = `${agentInfo}${toolsInfo}\n\n${content}`;
          const chunks = fullContent.split(' ');
          
          // Send initial message ID
          controller.enqueue(encoder.encode(`f:{"messageId":"msg-${Date.now()}"}\n`));
          
          // Send content in chunks for streaming effect
          chunks.forEach((chunk: string, index: number) => {
            const text = index === 0 ? chunk : ` ${chunk}`;
            controller.enqueue(encoder.encode(`0:${JSON.stringify(text)}\n`));
          });
          
          // Add tool usage summary if tools were used
          if (data.metadata?.tools_used?.length > 0) {
            const toolsSummary = `\n\n🔧 Tools Used: ${data.metadata.tools_used.map((t: { function: string }) => t.function).join(', ')}`;
            controller.enqueue(encoder.encode(`0:${JSON.stringify(toolsSummary)}\n`));
          }
          
          // End the stream
          const usage = {
            promptTokens: 50,
            completionTokens: chunks.length + (data.metadata?.tools_used?.length || 0) * 10
          };
          
          controller.enqueue(encoder.encode(`e:{"finishReason":"stop","usage":${JSON.stringify(usage)},"isContinued":false}\n`));
          controller.enqueue(encoder.encode(`d:{"finishReason":"stop","usage":${JSON.stringify(usage)}}\n`));
          controller.close();
          
          console.log('OWL Agent response stream completed');
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
    
  } catch (error) {
    console.error('Chat error:', error);
    return new Response(JSON.stringify({ error: error instanceof Error ? error.message : 'Unknown error' }), { 
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
} 