
// In admin-interface/src/services/ai/index.ts
import { StreamingTextResponse, LangChainStream } from 'ai';
import { OpenAI } from 'langchain/llms/openai';

export async function POST(req) {
  const { prompt } = await req.json();
  const { stream, handlers } = LangChainStream();
  
  const llm = new OpenAI({
    streaming: true,
    callbacks: [handlers],
    modelName: "gpt-4",
  });

  llm.call(prompt);
  
  return new StreamingTextResponse(stream);
}
