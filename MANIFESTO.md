# 🧠 NnennaAI Manifesto

---

## ✨ Why This Exists

Generative AI is too powerful—and too chaotic—to be left to hype and guesswork.
The existing landscape is fragmented, unintuitive, and often optimized for demos, not developers.

**NnennaAI exists to fix that.**

We’re building the **developer-first GenAI framework** for orchestrating pipelines, agents, and evaluations—designed with minimal lift and maximal clarity.

This isn’t just another tool.
It’s a shared foundation for those who believe GenAI infrastructure should be **composable, inspectable, and trustworthy** from day one.

---

## 🧠 What We Believe

We are engineers, researchers, builders, and explorers.
And this is what we believe:

- 🧩 **Modularity unlocks power.** GenAI workflows should be composable, swappable, and transparent—not monolithic black boxes.

- 🔍 **You can’t own your AI if you don’t own your evaluations.** Reproducible metrics and feedback loops should come first, not last.

- 🛠️ **CLI-first is developer-first.** Local-first tooling gives engineers superpowers. You shouldn’t need a dashboard to prototype intelligence.

- 🧠 **Simplicity is strength.** We simplify the orchestration layer so developers can focus on logic, not glue code.

- 🚀 **Start fast, iterate faster.** Developer experience should feel fast, safe, and empowering at every stage of the GenAI lifecycle.

- 🤝 **AI should extend human agency, not replace it.** Our tools help people build with AI—not surrender control to it.

---

## 🧭 Core Principles

### 1. 🔓 Default to Open

> _Open-source is a principle, not a distribution model._

We believe AI infrastructure must be inspectable, forkable, and community-owned. Every module, decision, and CLI command invites contribution and clarity.

💡 _Example: All modules live in versioned directories with editable configs and test coverage._

---

### 2. 🧩 Modular, Not Monolithic

> _Flexibility is power._

Each component in NnennaAI works alone or together. You can build a full pipeline—or just swap in the embedder, retriever, or evaluator.

💡 _Example: You can drop in ChromaDB or use your own vector store via config._

---

### 3. 🧪 Evaluation is Infrastructure

> _Build measurement into the system, not on top of it._

Every pipeline supports built-in quality, latency, and cost metrics—because evaluation is a foundational layer, not an afterthought.

💡 _Example: Run `nai eval` to compare prompt strategies across runs using RAGAS metrics._

---

### 4. 🧠 Simple > Clever

> _Intelligence isn’t complexity. It’s clarity._

We write readable code with sane defaults and smart flags—so engineers can grok what’s happening without scrolling through docs.

💡 _Example: `nai run` supports `--dry-run` to preview execution plans._

---

### 5. 🤖 AI Agents Are Systems, Not Magic

> _You should be able to see every decision an agent makes._

Our orchestration tools log, trace, and step through agent decisions—so you understand behavior before scaling risk.

💡 _Example: Agents ship with observable context protocol (MCP) and deterministic fallback modes._

---

## 🌐 Community Commitments

We’re building this framework in public—with everyone from tinkerers to teams in mind.

- 🤝 **Transparent Roadmaps:** Major features are decided collaboratively and published in `decisions/`.

- 🛟 **Developer Empathy:** We invest in docs, examples, and onboarding flows—because friction kills adoption.

- 💬 **Conversation, Not Commands:** We welcome dissent, feedback, and vision. If you disagree with something in here—we want to hear why.

---

## 🔭 What Comes Next

We're not done. We're just getting started.

### On our near-term horizon:

- `modules/` expansion: more plug-and-play evals, retrievers, and agents
- `templates/`: opinionated scaffolds for common GenAI use cases
- `nai test`: a native test harness for GenAI flows
- Evaluation dashboards + run history inspection
- Multi-agent protocol experimentation (MCP++)

You can follow along in our [GitHub Project Board](https://github.com/NnennaAI/NnennaAI/projects).

---

## 🧪 Contribute to the Future

We believe the best GenAI infrastructure will be built in the open—by the builders using it.

If this resonates:

- 📥 Fork the repo
- 🧪 Try out a module
- ✍🏾 Suggest an improvement
- 📢 Share your use case

### 🔗 Useful Links

- [README.md](./README.md) – Project overview
- [CONTRIBUTING.md](./CONTRIBUTING.md) – How to contribute
- [decisions/](./decisions/) – Architecture and tradeoff records

---

## 🧬 Final Word

This manifesto is a **living document**.
We review and revise it regularly—just like code.

If you're building GenAI infrastructure that puts developers first, we’re building it with you.

**Welcome to NnennaAI. Let’s orchestrate the future.**

— _Team NnennaAI_
