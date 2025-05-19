# cli/context/context_docs.py
from rich.console import Console
from rich.markdown import Markdown

console = Console()

def show_init_output():
    console.print("\n✅ [bold green]Project initialized using the 'starter-rag' template[/bold green]")
    console.print("📁 Created directory: [bold]./my-rag-pipeline/[/bold]")
    console.print("📄 Generated files: config.yaml, .env.example, run_rag_pipeline.py")
    console.print("\n🧪 Evaluation engine: Ragas (faithfulness, relevance)")
    console.print("🔐 Security: PII redaction enabled (spaCy-based)")
    console.print("\n▶️ [bold]Next:[/bold] run your pipeline with:")
    console.print("    cd my-rag-pipeline && nai run --query \"What is NnennaAI?\"")
    console.print("\n💡 Tip: Customize your pipeline via config.yaml")
    console.print("📚 Learn more: https://nnenn.ai/docs/templates/starter-rag\n")

def show_run_output():
    console.print("\n📥 Loading config: config.yaml")
    console.print("🔗 Using vector DB: Qdrant | Embeddings: text-embedding-3-small")
    console.print("📚 Retrieved 5 relevant chunks (top-k=5)")
    console.print("🤖 Generating response using GPT-4...\n")
    console.print("✅ [bold green]Done![/bold green] Output saved to: outputs/response.json")
    console.print("\n📄 Response (truncated):")
    console.print("    \"The API security doc emphasizes...\"")
    console.print("\n▶️ [bold]Next:[/bold] Assess this output:")
    console.print("    nai assess outputs/response.json")
    console.print("\n💡 Tip: Add --verbose to see token usage and costs\n")

def show_assess_output():
    console.print("\n📈 Running assessment using Ragas...")
    console.print("✅ [bold green]Assessment complete![/bold green]\n")
    console.print("📊 Ragas Score: 0.82")
    console.print("   - Faithfulness: 92%")
    console.print("   - Completeness: 71%")
    console.print("   - Context Precision: 88%\n")
    console.print("📄 Assessment report saved to: eval/assessment.md")
    console.print("\n💡 Tip: Improve your retriever config to boost completeness")
    console.print("🔗 Learn more about evaluation: https://nnenn.ai/docs/eval\n")

def show_scan_output():
    console.print("\n🔍 Scanning 12 files for PII (emails, names, IDs, etc)...")
    console.print("✅ [bold green]Scan complete[/bold green]\n")
    console.print("🔐 PII Found: 4 matches in 3 files")
    console.print("✂️ Redacted outputs saved to: ./cleaned/")
    console.print("📄 Redaction log: scan/report.json\n")
    console.print("💡 Tip: Add --report markdown to generate an audit summary")
    console.print("📚 Secure-by-default: https://nnenn.ai/docs/security\n")

def show_report_output():
    console.print("\n📊 Report Summary: Evaluation Trends\n")
    console.print("🧪 Most Recent Run:")
    console.print("   - Score: 0.82 | Faithfulness: 92% | Completeness: 71%")
    console.print("\n📈 Change vs Previous:")
    console.print("   - Completeness improved (+12%)")
    console.print("   - Context precision stable\n")
    console.print("📄 Full report saved to: eval/trends.md\n")
    console.print("💡 Tip: Include eval history in team reviews for model performance")
    console.print("📚 Docs: https://nnenn.ai/docs/reporting\n")
