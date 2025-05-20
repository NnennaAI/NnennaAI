# Modules

> ✫️ NnennaAI is built on **modules**—swappable components that make every part of the GenAI pipeline composable.

## 🧩 What is a Module?

A **module** in NnennaAI is a self-contained, plug-and-play component that powers a step in your pipeline—whether that's embedding, retrieval, generation, or evaluation. Each module follows a common interface, supports lifecycle hooks (`setup`, `__call__`, `teardown`), and can be swapped using a single config command. This unlocks rapid experimentation, local-first iteration, and customization.

## 🔢 Core Module Types

| Module Type     | Purpose                                      | Interface Method                                 |
| --------------- | -------------------------------------------- | ------------------------------------------------ |
| **Embedder**    | Converts text into vectors                   | `__call__(texts: List[str]) → List[List[float]]` |
| **Retriever**   | Looks up relevant documents from a vector DB | `__call__(query: str, k: int) → List[str]`       |
| **Agent (LLM)** | Generates answers from query + context       | `__call__(prompt: str) → str`                    |
| **Evaluator**   | Scores generated answers vs ground truth     | `evaluate(pred, truth) → Dict[str, float]`       |

## 🧱 Module Interface

All modules subclass a shared abstract base class:

```python
# modules/base.py
from abc import ABC, abstractmethod

class BaseModule(ABC):
    def __init__(self, config: dict):
        self.config = config

    def setup(self):
        """Optional hook: prepare resources."""
        pass

    @abstractmethod
    def __call__(self, *args, **kwargs):
        """Main execution hook."""
        pass

    def teardown(self):
        """Optional hook: release resources."""
        pass
```

Each module should also include a version tag like:

```python
implements = "nai.module.retriever@1.0.0"
```

This supports future compatibility checks and dynamic loading.

## 🚀 Default Modules (v0.1.0)

NnennaAI ships with the following built-in modules for fast local prototyping:

| Type      | Name              | Backend          |
| --------- | ----------------- | ---------------- |
| Embedder  | `OpenAIEmbedder`  | OpenAI           |
| Retriever | `ChromaRetriever` | ChromaDB         |
| Agent     | `GPT4oAgent`      | OpenAI GPT-4o    |
| Evaluator | `RAGASEvaluator`  | RAGAS (optional) |

These modules require no setup—just run `nai ingest`, `nai run`, or `nai score` to use them.

## 🔄 Swapping Modules via CLI

You can change a module by updating the active config:

```bash
nai config set retriever=faiss
nai config set embedder=sentence-transformers
```

Run `nai config show` to view the current pipeline components.

## 🛠️ Writing Your Own Module

To create a new module:

1. Inherit from `BaseModule`
2. Implement `__call__()` (and optionally `setup()` / `teardown()`)
3. Add a version tag (e.g. `nai.module.generator@1.1.0`)
4. Make it pip-installable (or drop into `modules/`)
5. Register it via CLI or YAML config
6. ✅ Done—your module is now composable

🔗 Template repo: [`nnennaai/module-template`](https://github.com/nnennaai/module-template)

## 🧪 Testing a Module

Use `pytest` fixtures to load your module with test data:

```python
import pytest
from my_module import MyRetriever

@pytest.fixture
def retriever():
    return MyRetriever(config={"path": "tests/fixtures"})

def test_retrieval(retriever):
    docs = retriever("What is NnennaAI?", k=3)
    assert isinstance(docs, list)
```

Run all tests locally with:

```bash
pytest tests/
```

## 🧽 Versioning & Compatibility

Modules must include a version tag using this pattern:

```python
implements = "nai.module.TYPE@X.Y.Z"
```

This allows:

- Future compatibility checks
- Future module registry support
- Safer hot-swapping across pipeline steps
