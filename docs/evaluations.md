# Evaluations

> 📊 Evaluation is GenAI testing and measurement in GenAI systems. At NnennaAI, evals is also **infrastructure**.

NnennaAI makes quality, correctness, and confidence measurable from day one. Whether you're using exact-match for simple checks or RAGAS for deeper QA evaluation, our goal is the same: plug in any evaluator and understand your system's behavior before scaling it.

## 🧠 Why Evaluation Matters

In traditional software, we write tests before shipping code.
In GenAI systems, evaluation _is_ testing—because outcomes aren’t deterministic.

You can’t improve what you can’t measure. Evaluation in NnennaAI helps you:

- Track quality over time
- Compare prompt strategies
- Understand failure cases
- Align model outputs to business goals

## 🧪 Evaluator Module Interface

Evaluators are fully modular. Any scoring logic just needs to implement:

```python
class BaseEvaluator:
    def __init__(self, config: dict):
        self.config = config

    def evaluate(self, prediction: str, ground_truth: str) -> dict:
        raise NotImplementedError
```

This interface is used in `RunEngine.score()` to produce a metrics dictionary.

## ✅ Built-in Evaluators

NnennaAI v0.1.0 ships with:

| Name             | Metric Type   | Description                                                        |
| ---------------- | ------------- | ------------------------------------------------------------------ |
| `ExactMatch`     | Boolean / 0-1 | Returns `1.0` if prediction == truth                               |
| `RAGASEvaluator` | Composite     | Uses RAGAS for answer correctness, faithfulness, context precision |

To use RAGAS, set:

```bash
nai config set eval=ragas
```

Or specify in YAML config:

```yaml
eval:
  metric: ragas
```

## 🛠️ Adding Custom Evaluators

To create your own:

1. Subclass `BaseEvaluator`
2. Implement `evaluate(prediction, ground_truth)`
3. Add `implements = "nai.module.evaluator@1.0.0"`
4. Register in your config (`eval.metric = your-evaluator-name`)

🔗 Template repo: [`nnennaai/module-template`](https://github.com/nnennaai/module-template)

## 📊 Example Usage (Python)

```python
from modules.config import Settings
from modules.engine import RunEngine

cfg = Settings()
pipeline = RunEngine(cfg)

metrics = pipeline.score(
    query="What is NnennaAI?",
    ground_truth="A modular GenAI orchestration framework."
)
print(metrics)
```

## 🧼 Output Format

Evaluators must return a flat dictionary of scores:

```python
{
  "score": 0.88,
  "faithfulness": 1.0,
  "context_precision": 0.7
}
```

This standard format makes it easy to:

- Log to a file
- Visualize over time
- Compare between runs

## 🧭 Roadmap Considerations

Future support may include:

- ⚖️ Cost/latency tradeoff metrics
- 🎯 Goal-alignment or user-feedback scoring
- 🧩 Composite scoring strategies
- 🪞 Eval dashboards for inspecting runs

Evaluation is how you turn intuition into iteration.
It’s how you stop guessing and start improving.
