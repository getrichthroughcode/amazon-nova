# Excalidraw Diagram Agent

> **Originally built for the [Amazon Nova Global Hackathon](https://amazonnovahackathon.devpost.com/), then extended to support multiple LLM providers.**

A "prompt in, diagram out" agent that draws directly on an [Excalidraw](https://excalidraw.com) canvas in real time. Describe any system, flow, or concept in plain text and watch the diagram appear element by element as the model generates it.

---

## Demo

1. Type a prompt — e.g. _"Microservices architecture for an e-commerce platform"_
2. Pick a model (free Groq, OpenRouter, or local Ollama)
3. Watch the diagram stream live onto the canvas
4. Edit it manually on top, or prompt again

---

## How it works

```
Prompt (browser)
     │
     ▼
FastAPI backend  ──── LiteLLM ────▶  LLM (Groq / OpenRouter / Ollama / …)
     │                                         │
     │  WebSocket                              │ streams NDJSON elements
     │  (one element per line)                 │
     ▼                                         ▼
Browser frontend  ◀───────────────────────────
  Excalidraw (CDN)
  updated live
```

The backend calls the LLM with a system prompt that instructs it to output raw Excalidraw JSON elements, one per line (NDJSON). Each line is immediately forwarded to the frontend via WebSocket and added to the canvas — no waiting for the full response.

---

## Stack

| Layer           | Technology                                                                  |
| --------------- | --------------------------------------------------------------------------- |
| Backend         | Python, FastAPI, Uvicorn                                                    |
| LLM routing     | [LiteLLM](https://github.com/BerriAI/litellm) — unified API for 100+ models |
| Real-time       | WebSocket (native FastAPI)                                                  |
| Frontend        | Vanilla JS + Excalidraw via CDN (no build step)                             |
| Package manager | [uv](https://github.com/astral-sh/uv)                                       |

---

## Supported models

### Free (cloud)

| Provider       | Models                                                | API key                                      |
| -------------- | ----------------------------------------------------- | -------------------------------------------- |
| **Groq**       | Llama 3.3 70B, Llama 3.1 8B, Mixtral 8x7B             | [console.groq.com](https://console.groq.com) |
| **OpenRouter** | Llama 3.3 70B, Mistral 7B, Gemma 3 27B (`:free` tier) | [openrouter.ai](https://openrouter.ai)       |

### Local (free, no API key)

| Tool       | Models                                                            |
| ---------- | ----------------------------------------------------------------- |
| **Ollama** | Any model — `ollama pull llama3.2`, `mistral`, `qwen2.5-coder`, … |

### Paid (optional)

| Provider  | Models            |
| --------- | ----------------- |
| Anthropic | Claude Sonnet 4.6 |
| OpenAI    | GPT-4o Mini, etc. |

---

## Getting started

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- A free [Groq API key](https://console.groq.com) (or any other supported provider)

### Install

```bash
git clone https://github.com/getrichthroughcode/amazon-nova
cd amazon-nova
uv sync
```

### Configure

Copy `.env` and fill in your keys:

```bash
cp .env .env.local   # or just edit .env directly
```

```env
# Minimum required for the default model (Groq — free)
GROQ_API_KEY=your_key_here

# Optional
OPENROUTER_API_KEY=your_key_here
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

For Ollama, no key is needed — just make sure the Ollama daemon is running (`ollama serve`).

### Run

```bash
uv run python main.py
```

Open [http://localhost:8000](http://localhost:8000).

---

## Project structure

```
.
├── main.py          # FastAPI app — serves the UI and handles WebSocket connections
├── agent.py         # LiteLLM streaming — prompt → NDJSON Excalidraw elements
├── static/
│   └── index.html   # Frontend — Excalidraw canvas + WebSocket client
├── pyproject.toml
└── .env             # API keys (not committed)
```

---

## Origin

This project started as a submission to the **Amazon Nova Global Hackathon**, where the original goal was to explore [Amazon Nova Act](https://aws.amazon.com/ai/nova/) for agentic UI automation on Excalidraw. It has since been refactored to use a more direct approach — generating Excalidraw's JSON format directly from LLMs — and extended with [LiteLLM](https://github.com/BerriAI/litellm) to support any model, including free and open-source alternatives.
