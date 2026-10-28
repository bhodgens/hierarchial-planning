# Lllm provider message format quirks
When to use: provider message formats.
Lesson: quirks that break tool calls or system prompts per provider.

# LLM Provider Message-Format Quirks

Providers differ in what message roles they accept. When building an LLM
client that must work across providers, these rules prevent silent failures.

## Known quirks (2026-07)

| Provider | System role | Assistant role | Fix |
|----------|-------------|----------------|-----|
| Cohere (north-mini-code) | Rejects | Rejects | Merge everything into single user message |
| OpenRouter (Gemini Flash Lite) | Accepts | Accepts | Standard system+user works |
| OpenRouter (DeepSeek Chat) | Accepts | Accepts | Standard |
| llama.cpp (local) | Accepts | Accepts | Standard |

## Universal-safe format

When provisioning for unknown providers, use a single user message:

```
System prompt text...\n\n---\n\nUser-specific instruction...
```

This works with every provider tested. The tradeoff is that some models
(ChatGPT-class) perform better with separated system/user roles — but for
adversarial/generation tasks where the prompt is a combined instruction,
the single-message format is more portable.

## Retry messages

Avoid assistant-role messages in retry chains (e.g. "your previous response
was X, please fix"). Instead, inline the previous response into the user
message:

```
Original prompt...\n\nYour previous response was:\n{previous output}\n\nThat was invalid. Please fix it.
```

This avoids the Cohere-class "invalid message at index 1" error where the
assistant role is rejected.
