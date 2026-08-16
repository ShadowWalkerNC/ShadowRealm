"""
Interactive Learning Engine for ShadowRealm.
Parses local codebases using AST analysis, generates study guides,
explains architectural patterns, and tests developer knowledge without heavy AI token usage.
"""

from pathlib import Path
from typing import Dict, Any, List
from src.ast_indexer import index_file_symbols, get_ast_outline

def generate_repository_study_guide(repo_name: str) -> Dict[str, Any]:
    """Generate a token-minimal interactive study guide for a target codebase."""
    projects_dir = Path("C:/Users/white/OneDrive/Documents/GitHub")
    target_repo = projects_dir / repo_name
    
    if not target_repo.exists() or not target_repo.is_dir():
        return {"ok": False, "error": f"Repository '{repo_name}' not found."}

    # Discover target source files
    source_files = []
    for ext in ["*.py", "*.js", "*.ts", "*.dart", "*.rs"]:
        source_files.extend(list(target_repo.rglob(ext)))

    symbol_summary = []
    for f in source_files[:10]: # Limit to top 10 files for fast outline
        res = index_file_symbols(str(f))
        if res.get("symbols"):
            symbol_summary.append({
                "file": f.name,
                "symbols_count": res["symbol_count"],
                "outline": res["symbols"][:5]
            })

    guide = {
        "ok": True,
        "repo_name": repo_name,
        "total_files_indexed": len(source_files),
        "key_components": symbol_summary,
        "learning_objectives": [
            f"1. Understand the core module structure of {repo_name}.",
            "2. Master AST symbol navigation (goto_definition, find_references).",
            "3. Run automated SAST security scans locally (Strix, Semgrep, Bandit).",
            "4. Hands-on coding: Extend features locally with zero AI dependency."
        ],
        "suggested_exercises": [
            f"Exercise A: Trace execution from main entrypoint across {len(source_files)} source files.",
            "Exercise B: Run local test suite (`pytest` or `cargo test`) and fix an edge case.",
            "Exercise C: Run `/cli strix scan local` to check for security vulnerabilities."
        ]
    }
    return guide
