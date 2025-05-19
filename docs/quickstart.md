# ⚡ Quick Start: Build Your First GenAI Pipeline in 10 Minutes

Welcome to **NnennaAI**—the plug‑and‑play GenAI framework that turns glue‑code headaches into a single CLI command. This guide walks you through the _happiest path_ so you can ingest docs, run a Retrieval‑Augmented Generation (RAG) pipeline, and score its quality—without writing a line of Python.

**You’ll do all of this in ≈10 minutes:**

1. Install the `nai` CLI
2. Scaffold a starter project
3. Ingest a folder of Markdown docs
4. Run the pipeline & get an answer
5. Score the run (quality, cost, latency)
6. Launch a shareable dashboard

## 1. Install the CLI

First, install the `nai` CLI globally or per-project. This will allow you to run the CLI from anywhere in your project directory. You can also use a virtual environment to manage dependencies.

```bash
# Global install (recommended)
pipx install nai
# ‑‑or per‑project
python -m venv .venv && source .venv/bin/activate
pip install nai
```

_Success check:_ `nai --version` prints the current release (e.g. `0.1.0`).

## 2.  Scaffold a RAG project

Create a new project directory and initialize it with the `nai init` command. This will generate a starter project with a pipeline and evaluation stubs.

```bash
mkdir my‑rag‑bot && cd $_
nai init rag‑starter          # creates pipeline & eval stubs
```

Generated files:

| File            | Purpose                                                  |
| --------------- | -------------------------------------------------------- |
| `pipeline.yaml` | Declarative modules: loader → embedder → retriever → llm |
| `score.yaml`    | Metric set: faithfulness, answer‑quality, latency, cost  |
| `.nai/`         | Local run history & traces                               |

---

## 3. Ingest your documents

Ingest your Markdown docs into ChromaDB. This step is crucial for the pipeline to work efficiently. The CLI will chunk, embed, and index your documents.

```bash
nai ingest ./docs/**/*.md   # chunk, embed, and index into ChromaDB
```

_Success check:_ the CLI prints `✅ indexed … chunks`.

## 4. Run the pipeline

To run the pipeline, use the `run` command. The CLI will execute the pipeline in a single pass, logging every step.

```bash
nai run "What does the scaling section say about vector sharding?"
```

Behind the scenes:

```
loader → embedder → retriever → llm
           ↓                  ↑
        (traces)    ← hooks (latency, token usage)
```

## 5. Evaluate the run

Use the `score` command for running evaluations. Use the `--save` flag to save results to a database for later analysis.

```bash
nai score --save run‑history.db
```

Console output:

```
Answer‑Quality: 0.91 | Faithfulness: 0.88 | Latency: 2.3 s | Cost: $0.0006
Saved results → run‑history.db (SQLite)
```

## 6. Share a dashboard

```bash
nai dashboard --serve   # opens http://localhost:8888
```

You’ll see interactive charts of every run—ready to drop into a PR or slide deck.

Congratulations! You’ve successfully built your first GenAI pipeline in 10 minutes. Now, dive into the docs for more advanced features and best practices.

## Next Steps

| Goal                           | Command                                             | Docs                      |
| ------------------------------ | --------------------------------------------------- | ------------------------- |
| Swap the LLM for a local model | `nai config set llm=modelscope/yi‑34b‑chat‑q4`      | `docs/pipeline-config.md` |
| Add a custom evaluator         | Create a module `my‑eval/` & `pip install -e .`     | `docs/modules.md`         |
| CI testing                     | Use our GitHub Action template invoking `nai score` | `docs/score.md`           |

Ready to explore further? Check the full CLI reference at [**docs/cli.md**](cli.md).

Happy building — and remember: _own your evaluations before you own your AI._
