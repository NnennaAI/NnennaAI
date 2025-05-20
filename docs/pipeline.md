# GenAI Pipeline

> 🔁 The GenAI pipeline is the backbone of every NnennaAI run—it wires together modules into a clean, inspectable flow.

## 🧠 `RunEngine` as the GenAI Pipeline

The `RunEngine` is the orchestrator that runs your GenAI workflow from start to finish. It doesn’t implement embedding, retrieval, generation, or evaluation itself—it delegates those steps to modules you configure.

This separation of concerns keeps logic clean, makes testing easy, and allows you to swap components without rewriting glue code.

## 🔄 Lifecycle Steps

A typical pipeline call moves through three core phases:

```text
nai ingest  →  nai run  →  nai score
```

| Step       | Description                                                                                        |
| ---------- | -------------------------------------------------------------------------------------------------- |
| `ingest()` | Takes a list of documents, embeds them, and stores vectors in your chosen retriever (e.g. Chroma). |
| `run()`    | Accepts a query, retrieves context, builds a prompt, and generates an answer.                      |
| `score()`  | Runs `run()` under the hood, then compares the output to ground truth using an evaluator module.   |

## 🧱 Pipeline Entrypoint (Code)

```python
from modules.config import Settings
from modules.pipeline import RunEngine

cfg = Settings()
pipeline = RunEngine(cfg)

pipeline.ingest(["NnennaAI is a modular GenAI framework."])
print(pipeline.run("What is NnennaAI?"))
```

Each step internally delegates to a module:

- `embedder = cfg.embeddings.provider`
- `retriever = cfg.retriever.provider`
- `generator = cfg.generator.provider`
- `evaluator = cfg.eval.metric`

These values are auto-wired from config—no hardcoding.

## 🔌 Swappable by Design

RunEngine dynamically loads modules based on your configuration. For example:

```bash
nai config set retriever=faiss
nai config set generator=llama-cpp
```

There’s no need to touch pipeline logic—every swap happens behind the scenes via the `Settings` object.

## ➕ Extending the Pipeline

You can safely extend the pipeline in the following ways:

- 🔍 **Observability** – Add tracing or logging hooks inside each step.
- 🔄 **Reranking** – Plug in post-retrieval reranking logic.
- 🧵 **Streaming** – Stream LLM output token-by-token.
- 🛡️ **Fallbacks** – Add retry/fallback logic if modules fail.
- 🧪 **Branching** – Route through different evaluators depending on prompt type.

Each of these can be layered in without modifying module code.

## 🧰 Execution Modes

You can run the pipeline via:

### 1. CLI-first (default)

```bash
nai ingest --path data.txt
nai run --q "What is NnennaAI?"
nai score --q "What is NnennaAI?" --truth "A modular GenAI framework."
```

### 2. Python API

```python
from modules.pipeline import RunEngine
from modules.config import Settings

pipeline = RunEngine(Settings())
result = pipeline.run("What is NnennaAI?")
```

The pipeline exists to glue—not to control. It’s inspectable, swappable, and minimal by design.
