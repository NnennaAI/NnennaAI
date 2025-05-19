# Architectural Decision: CLI Language for `nai`

## Decision Summary

We will implement the initial version of the `nai` CLI using **Python**, with the [Typer](https://typer.tiangolo.com) framework.

## Context

The `nai` CLI is the primary developer interface to the NnennaAI framework. It must:

- Be intuitive and fast to use
- Support potential commands like `run`, `eval`, `scan`, and `report`
- Integrate smoothly with GenAI tools like OpenAI, Ragas, and Galileo
- Serve developers across notebooks, terminal workflows, and CI/CD pipelines

This decision evaluates the optimal language and ecosystem for the CLI.

## Options Considered

### 1. Python (Typer)

- ✅ First-class support for GenAI tools (OpenAI, Ragas, spaCy, etc.)
- ✅ Rapid development and iteration
- ✅ Familiar to most AI/ML engineers
- ✅ Excellent community support
- ⚠️ Slightly slower runtime vs. compiled alternatives

### 2. Go

- ✅ Extremely fast and portable (binary distribution)
- ✅ Great for future SaaS integrations or enterprise adoption
- ⚠️ Limited out-of-the-box GenAI tool support
- ⚠️ Higher onboarding friction for AI engineers

### 3. Rust

- ✅ High-performance and secure
- ✅ Great for long-term system-level observability tools
- ⚠️ Complex syntax and steep learning curve
- ⚠️ Ecosystem not yet optimized for GenAI

### 4. Node.js

- ✅ Fast prototyping, good DX
- ⚠️ Weak alignment with Python-based GenAI stacks
- ⚠️ Limited value for a Python-first audience

## Decision

**We chose Python with the Typer framework** for the initial implementation of the `nai` CLI.

This allows us to:

- Move fast and build the CLI in tandem with the GenAI templates
- Reuse existing Python modules for evaluation and security
- Support contributors who are already working in the GenAI Python ecosystem

## Future Considerations

- We may reimplement performance-critical subcommands (e.g. `scan`, `eval`) in Go or Rust for portability and binary deployment
- A rewrite in Go could be scoped for `nai v1.0` depending on adoption and integration needs
- We will design `nai` to be language-agnostic: CLI reads from config files and writes to open formats (YAML, JSON)

## Status

✅ **Accepted**  
📅 Date: `2025-05-18`  
✍️ Author: [Nnenna Ndukwe](https://github.com/nnennandukwe/)
