import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

// Exercise the production parser without adding a test framework dependency.
const source = (await readFile(new URL('../src/services/chatService.ts', import.meta.url), 'utf8'))
  .replace("import.meta.env.VITE_AI_API_URL ?? ''", "''");
const { outputText } = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ES2022 } });
const { consumeChatStream, fetchConversation, fetchConversations, streamChat } = await import(`data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`);
const encode = (value) => new TextEncoder().encode(value);
const frame = (event) => `data: ${JSON.stringify(event)}\n\n`;
const done = { type: 'done', conversation_id: 'thread-1', answer: 'Hello', pipeline: [], query_description: '', result_count: 0, retry_count: 0 };
function stream(chunks) {
  return new ReadableStream({ start(controller) { chunks.forEach((chunk) => controller.enqueue(chunk)); controller.close(); } });
}

test('handles one-byte chunks, UTF-8, CRLF, heartbeats, and multiple events', async () => {
  const expected = [{ type: 'start', conversation_id: 'thread-1' }, { type: 'answer_delta', text: 'Hello 🌍 مرحبا' }, done];
  const bytes = encode((': keep-alive\n\n' + expected.map(frame).join('')).replaceAll('\n', '\r\n'));
  const received = [];
  await consumeChatStream(stream(Array.from(bytes, (byte) => new Uint8Array([byte]))), (event) => received.push(event));
  assert.deepEqual(received, expected);
});

test('treats a truncated stream as failure and preserves preceding deltas', async () => {
  const received = [];
  await assert.rejects(consumeChatStream(stream([encode(frame({ type: 'answer_delta', text: 'Partial' }))]), (event) => received.push(event)), /before the response finished/);
  assert.equal(received[0].text, 'Partial');
});

test('surfaces server errors and cancels the reader', async () => {
  let cancelled = false;
  const body = new ReadableStream({ start(controller) { controller.enqueue(encode(frame({ type: 'error', message: 'Please retry' }))); }, cancel() { cancelled = true; } });
  await assert.rejects(consumeChatStream(body, () => {}), /Please retry/);
  assert.equal(cancelled, true);
});

test('stops at done even if the server has not closed the connection', async () => {
  let cancelled = false;
  const body = new ReadableStream({ start(controller) { controller.enqueue(encode(frame(done))); }, cancel() { cancelled = true; } });
  await consumeChatStream(body, () => {});
  assert.equal(cancelled, true);
});

test('sends conversation context and handles HTTP validation errors', async (context) => {
  context.mock.method(globalThis, 'fetch', async (url, options) => {
    assert.equal(url, '/api/chat/stream');
    assert.deepEqual(JSON.parse(options.body), { message: 'Follow up', conversation_id: 'thread-1' });
    assert.equal(options.method, 'POST');
    assert.ok(options.signal);
    return new Response(JSON.stringify({ detail: [{ msg: 'invalid' }] }), { status: 422 });
  });
  await assert.rejects(streamChat('Follow up', 'thread-1', () => {}, new AbortController().signal), /failed \(422\)/);
});

test('loads the conversation list and an encoded conversation id', async (context) => {
  const responses = [
    [{ id: 'thread-1', title: 'First chat', created_at: '2026-01-01', updated_at: '2026-01-01' }],
    { conversation: { id: 'thread/1' }, messages: [] },
  ];
  let call = 0;
  context.mock.method(globalThis, 'fetch', async (url) => {
    assert.equal(url, call === 0 ? '/api/chat/conversations' : '/api/chat/conversations/thread%2F1');
    return Response.json(responses[call++]);
  });
  assert.equal((await fetchConversations())[0].title, 'First chat');
  assert.equal((await fetchConversation('thread/1')).conversation.id, 'thread/1');
});
