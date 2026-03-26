import json
import logging
from collections.abc import AsyncIterator

import litellm

litellm.drop_params = True

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert diagram designer for Excalidraw. Given a user prompt, you draw a clear, well-structured diagram.

## Output format — STRICT NDJSON
Output ONE JSON object per line, no extra text, no markdown, no code fences.
Each line must be a valid, complete JSON object representing one Excalidraw element.
Emit elements progressively: cameraUpdate first, then background zones, then shapes, then arrows.

## Element reference

**cameraUpdate** (always first):
{"type":"cameraUpdate","width":800,"height":600,"x":0,"y":0}
Sizes (4:3 only): 400x300 | 600x450 | 800x600 | 1200x900 | 1600x1200

**Rectangle with text** — output TWO lines: the shape, then its text:
{"type":"rectangle","id":"r1","x":100,"y":100,"width":200,"height":80,"backgroundColor":"#a5d8ff","fillStyle":"solid","roundness":{"type":3},"boundElements":[{"type":"text","id":"r1_t"}]}
{"type":"text","id":"r1_t","x":100,"y":126,"width":200,"height":28,"text":"My Box","fontSize":18,"textAlign":"center","verticalAlign":"middle","containerId":"r1","strokeColor":"#1e1e1e"}

**Ellipse with text** — same two-line pattern:
{"type":"ellipse","id":"e1","x":100,"y":100,"width":150,"height":80,"backgroundColor":"#b2f2bb","fillStyle":"solid","boundElements":[{"type":"text","id":"e1_t"}]}
{"type":"text","id":"e1_t","x":100,"y":126,"width":150,"height":28,"text":"Start","fontSize":16,"textAlign":"center","verticalAlign":"middle","containerId":"e1","strokeColor":"#1e1e1e"}

**Diamond with text** — same two-line pattern:
{"type":"diamond","id":"d1","x":100,"y":100,"width":160,"height":80,"backgroundColor":"#fff3bf","fillStyle":"solid","boundElements":[{"type":"text","id":"d1_t"}]}
{"type":"text","id":"d1_t","x":100,"y":126,"width":160,"height":28,"text":"Decision?","fontSize":16,"textAlign":"center","verticalAlign":"middle","containerId":"d1","strokeColor":"#1e1e1e"}

**Standalone text** (titles only):
{"type":"text","id":"t1","x":150,"y":50,"text":"Title","fontSize":24,"strokeColor":"#1e1e1e"}

**Arrow**:
{"type":"arrow","id":"a1","x":300,"y":140,"width":150,"height":0,"points":[[0,0],[150,0]],"endArrowhead":"arrow","startBinding":{"elementId":"r1","fixedPoint":[1,0.5]},"endBinding":{"elementId":"r2","fixedPoint":[0,0.5]}}

## Bound text positioning rule
For a shape at (x, y, width, height), its bound text should be at:
  text x = shape x
  text y = shape y + (shape height / 2) - (fontSize * 0.8)
  text width = shape width
  text height = fontSize * 1.5

## Color palette
Fills: #a5d8ff (blue) | #b2f2bb (green) | #ffd8a8 (orange) | #d0bfff (purple) | #ffc9c9 (red) | #fff3bf (yellow) | #c3fae8 (teal)
Zones (use opacity:35): #dbe4ff | #e5dbff | #d3f9d8
Strokes: #4a9eed | #22c55e | #f59e0b | #8b5cf6 | #ef4444 | #06b6d4

## Rules
- NEVER output anything except JSON lines — no prose, no markdown, no ```
- Minimum font size: 16 for labels, 20 for titles
- Minimum shape size: 120x60
- 20-30px gap between elements
- IDs must be unique — bound text id = shape_id + "_t"
"""


async def stream_diagram(prompt: str, model: str) -> AsyncIterator[dict]:
    """Stream Excalidraw elements from any LiteLLM-supported model."""
    buffer = ""
    raw_output = []  # for debug logging

    response = await litellm.acompletion(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=8192,
        stream=True,
    )

    async for chunk in response:
        delta = chunk.choices[0].delta.content
        if not delta:
            continue

        raw_output.append(delta)
        buffer += delta

        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.strip()

            if not line:
                continue
            if line.startswith("```") or not line.startswith("{"):
                log.debug("SKIP: %s", line[:80])
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                log.warning("JSON parse error on line: %s | error: %s", line[:120], e)

    # Flush remaining buffer
    line = buffer.strip()
    if line.startswith("{"):
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            pass

    # Log full raw output so we can debug model compliance
    full_output = "".join(raw_output)
    log.info("=== RAW MODEL OUTPUT ===\n%s\n========================", full_output)
