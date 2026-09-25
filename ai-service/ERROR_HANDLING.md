# AI assistant error handling

The chat API uses one safe error shape for ordinary HTTP failures and terminal
SSE failures:

```json
{
  "request_id": "...",
  "status": "error",
  "error": {
    "code": "MODEL_TIMEOUT",
    "stage": "generate_query",
    "message": "The assistant took too long to respond. Please try again.",
    "retryable": true
  }
}
```

For an SSE response that has already started, the same fields are delivered in
an event with `type: "error"`; a `done` event is never emitted afterwards.
Failed turns are stored with status `error`, so they are excluded from future
conversation context.

Configuration:

- `OPENROUTER_TIMEOUT_SECONDS` controls one model call; it defaults to `30`.
- `VITE_CHAT_TIMEOUT_MS` controls the browser request timeout; it defaults to
  `180000` and should remain longer than the maximum expected multi-step agent
  request.

LangSmith continues to receive the existing request and graph traces. Failure
metadata adds `error_code` and `failed_stage`, correlated through `request_id`.
