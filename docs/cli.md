# 🖥️ NnennaAI CLI Reference

> **CLI‑first is developer‑first.** Every feature in NnennaAI is exposed through the `nai` command so you can automate, script, and debug without leaving your terminal.
>
> **Six verbs, one flag, zero confusion.** Everything else ships as a plugin so the core stays lean and learnable.

## 📜 Cheat‑Sheet

| Verb        | One‑liner                                 | High‑value flags                      |
| ----------- | ----------------------------------------- | ------------------------------------- |
| `init`      | Scaffold a starter project                | `--template rag-starter`              |
| `ingest`    | Load & index files into the vector store  | `--chunk 500`, `--metadata key=value` |
| `run`       | Execute a pipeline (interactive or batch) | `--dry-run`, `--trace`                |
| `score`     | Compute quality / latency / cost metrics  | `--baseline <RUN_ID>`                 |
| `config`    | View / set runtime overrides              | `set`, `get`, `list`                  |
| `dashboard` | Launch or export HTML report              | `--serve`, `--export`                 |

Universal flag: **`--trace`** (works with any verb for step‑by‑step logs).

## 🚀 Verb Details & Examples

### `nai init`

Scaffold the suggested directory layout and default YAML configs.

```bash
nai init rag-starter
```

### `nai ingest`

Index your knowledge base.

```bash
# Ingest all Markdown docs under ./docs
nai ingest ./docs/**/*.md --chunk 400 --metadata tier=docs project=nnennaai
```

#### Metadata Tags — _Simple but Powerful_

- `--metadata` accepts **any** `key=value` pairs you invent.
- Tags are stored alongside each chunk in the vector store.
- Use them later to **filter** retrieval or slice evaluation metrics.

```bash
# Only retrieve chunks labeled tier=docs
nai run "Explain the architecture" \
  --filter "tier=docs"

# Compare scores between two tag groups
nai score --where "tier=docs"  # vs tier=specs
```

> Think of metadata tags like Git branches for your data: lightweight, flexible, and optional.

### `nai run`

Execute the pipeline defined in `pipeline.yaml`.

```bash
nai run "What is the purpose of NnennaAI?" --trace
```

### `nai score`

Measure quality, latency, and cost for one or more runs.

```bash
nai score latest --baseline prod-0429 --save run-history.db
```

### `nai config`

Swap modules or override settings without editing YAML.

```bash
nai config set llm=modelscope/yi-34b-chat-q4
nai config get llm
```

### `nai dashboard`

Open an interactive metrics & trace UI.

```bash
nai dashboard --serve
```

## 🔌 Plugins

Extra verbs (e.g. `nai deploy`, `nai tune`) land from external packages:

```bash
pip install nai-deploy-aws
nai deploy --cluster my-eks
```

The plugin appears automatically—no config edits required.

## 🛠️ Need help?

```bash
nai --help
nai <verb> --help   # e.g. nai ingest --help
```

Join the discussion at **GitHub Discussions** if you get stuck. We keep the CLI surface tiny so discovery is instant and developer delight stays high.
