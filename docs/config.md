# `config.yaml`

> ⚙️ Configuration is the key to composability.

We use a single config system to dynamically wire together every pipeline component—no hardcoded logic, no monolithic scripts. Whether you're using the CLI or Python, the config file controls what modules run and how they’re initialized.

## 🧠 Why Config Matters

In NnennaAI, configuration is more than setup. It’s the foundation for:

- 🔄 Swapping modules (e.g. `retriever=faiss`, `generator=llama-cpp`)
- 🧪 Reproducible experiments
- 📦 Portable environments
- ⚡ Minimal CLI flags

## 🗂️ Config Structure

Configs are defined using [Pydantic](https://docs.pydantic.dev/) models and support both Python and YAML usage.

```python
from pydantic import BaseModel
from pathlib import Path
from typing import Literal

class EmbeddingSettings(BaseModel):
    provider: Literal["openai"] = "openai"
    model: str = "text-embedding-3-small"

class RetrieverSettings(BaseModel):
    provider: Literal["chroma"] = "chroma"
    persist_dir: Path = Path(".nai/chroma")
    collection: str = "nai_docs"

class GeneratorSettings(BaseModel):
    provider: Literal["openai"] = "openai"
    model: str = "gpt-4o-mini"

class EvalSettings(BaseModel):
    metric: Literal["exact_match", "ragas"] = "exact_match"

class Settings(BaseModel):
    embeddings: EmbeddingSettings = EmbeddingSettings()
    retriever: RetrieverSettings = RetrieverSettings()
    generator: GeneratorSettings = GeneratorSettings()
    eval: EvalSettings = EvalSettings()
```

## 📄 YAML Config Example

You can optionally use a `.nai.yaml` file in your project root or home directory:

```yaml
embeddings:
  provider: openai
  model: text-embedding-3-small

retriever:
  provider: chroma
  persist_dir: .nai/chroma
  collection: nai_docs

generator:
  provider: openai
  model: gpt-4o-mini

eval:
  metric: ragas
```

To use it:

```bash
nai run --config .nai.yaml --q "What is NnennaAI?"
```

## 🧠 CLI Integration

Use `nai config` to inspect or modify the active config from the terminal:

```bash
nai config show                # display active config
nai config set retriever=faiss # hot-swap a module
nai config reset               # restore defaults
```

Config is always loaded and validated before pipeline execution.

## 🔁 Runtime Behavior

On startup, NnennaAI looks for config in the following order:

1. `--config` flag (explicit path)
2. `.nai.yaml` in project root
3. `~/.nai.yaml` in home directory
4. Defaults baked into `Settings()`

This makes it easy to:

- Share configs with your team
- Version control pipeline settings
- Override for one-off runs without changing files

## 🧩 Extending Configs

To add a new module type (e.g. a reranker):

1. Define a new `BaseModel` in `config.py`
2. Add it to the main `Settings` class
3. Reference `settings.reranker` in your custom logic

Because config objects are fully typed and validated, new fields are safe to add without breaking other parts of the pipeline.

NnennaAI makes composability a first-class citizen—and config is how it all fits together.
