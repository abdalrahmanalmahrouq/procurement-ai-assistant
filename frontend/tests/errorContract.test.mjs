import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const source = (await readFile(new URL('../src/services/chatService.ts', import.meta.url), 'utf8'))
  .replace("import.meta.env.VITE_AI_API_URL ?? ''", "''");
const { outputText } = ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ES2022 },
});
const { ChatServiceError, consumeChatStream, streamChat } = await import(
  `data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`
);

test('preserves structured SSE errors for safe retry decisions', async () => {
  const payload = {
    type: 'error',
    request_id: 'request-1',
    message: 'The assistant took too long to respond. Please try again.',
    error: {
      code: 'MODEL_TIMEOUT',
      stage: 'generate_query',
      message: 'The assistant took too long to respond. Please try again.',
      retryable: true,
    },
  };
  const body = new ReadableStream({
    start(controller) {
      controller.enqueue(new TextEncoder().encode(`data: ${JSON.stringify(payload)}\n\n`));
    },
  });

  await assert.rejects(
    consumeChatStream(body, () => undefined),
    (error) => {
      assert.ok(error instanceof ChatServiceError);
      assert.equal(error.details.code, 'MODEL_TIMEOUT');
      assert.equal(error.details.stage, 'generate_query');
      assert.equal(error.details.retryable, true);
      return true;
    },
  );
});

test('normalizes an AI service connection failure into a safe retryable error', async (context) => {
  context.mock.method(globalThis, 'fetch', async () => {
    throw new TypeError('private network failure details');
  });

  await assert.rejects(
    streamChat('How much was spent?', undefined, () => undefined, new AbortController().signal),
    (error) => {
      assert.ok(error instanceof ChatServiceError);
      assert.equal(error.details.code, 'AI_SERVICE_UNAVAILABLE');
      assert.equal(error.details.stage, 'connection');
      assert.equal(error.details.retryable, true);
      assert.equal(error.message.includes("private network"), false);
      return true;
    },
  );
});
