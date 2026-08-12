"""
AST Codebase Symbol Indexer for Odysseus.
Parses Python, JS/TS, Dart, and Rust files into lightweight symbol trees
(functions, classes, methods, imports) to enable token-efficient code navigation.
"""

import ast
import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class SymbolItem:
    def __init__(self, name: str, symbol_type: str, line_no: int, end_line_no: int, details: str = ""):
        self.name = name
        self.symbol_type = symbol_type
        self.line_no = line_no
        self.end_line_no = end_line_no
        self.details = details

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.symbol_type,
            "line_no": self.line_no,
            "end_line_no": self.end_line_no,
            "details": self.details
        }

def parse_python_ast(file_path: Path) -> List[SymbolItem]:
    """Parse Python file using ast module."""
    symbols = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(content)
        lines = content.splitlines()

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                end_line = getattr(node, 'end_lineno', node.lineno)
                symbols.append(SymbolItem(node.name, "class", node.lineno, end_line, f"class {node.name}"))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end_line = getattr(node, 'end_lineno', node.lineno)
                args = [a.arg for a in node.args.args]
                is_async = isinstance(node, ast.AsyncFunctionDef)
                prefix = "async def" if is_async else "def"
                symbols.append(SymbolItem(node.name, "function", node.lineno, end_line, f"{prefix} {node.name}({', '.join(args)})"))
    except Exception as e:
        logger.debug(f"Python AST parse error for {file_path}: {e}")
    return symbols

def parse_generic_regex(file_path: Path) -> List[SymbolItem]:
    """Parse JS/TS/Dart/Rust files using regex pattern matching."""
    symbols = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()
        
        # Regex patterns for common language constructs
        fn_pattern = re.compile(r'^\s*(?:async\s+)?(?:export\s+)?(?:default\s+)?function\s+([a-zA-Z0-9_$]+)\s*\(|^^\s*(?:export\s+)?const\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\(', re.MULTILINE)
        class_pattern = re.compile(r'^\s*(?:export\s+)?(?:default\s+)?class\s+([a-zA-Z0-9_$]+)', re.MULTILINE)
        
        for idx, line in enumerate(lines, 1):
            cl_match = class_pattern.search(line)
            if cl_match:
                name = cl_match.group(1)
                symbols.append(SymbolItem(name, "class", idx, idx, f"class {name}"))
                continue
            
            fn_match = fn_pattern.search(line)
            if fn_match:
                name = fn_match.group(1) or fn_match.group(2)
                if name:
                    symbols.append(SymbolItem(name, "function", idx, idx, f"function {name}"))
    except Exception as e:
        logger.debug(f"Generic regex symbol parse error for {file_path}: {e}")
    return symbols

def index_file_symbols(file_path_str: str) -> Dict[str, Any]:
    """Index symbols for a single target file."""
    path = Path(file_path_str)
    if not path.exists() or not path.is_file():
        return {"error": "File not found", "symbols": []}

    suffix = path.suffix.lower()
    if suffix == ".py":
        symbols = parse_python_ast(path)
    elif suffix in [".js", ".ts", ".jsx", ".tsx", ".dart", ".rs"]:
        symbols = parse_generic_regex(path)
    else:
        symbols = []

    return {
        "file": str(path.resolve()),
        "extension": suffix,
        "symbol_count": len(symbols),
        "symbols": [s.to_dict() for s in symbols]
    }

def get_ast_outline(file_path_str: str) -> str:
    """Generate a token-efficient AST outline of a file."""
    res = index_file_symbols(file_path_str)
    if "error" in res:
        return f"Error: {res['error']}"

    symbols = res["symbols"]
    if not symbols:
        return f"No symbols indexed for {Path(file_path_str).name}"

    lines = [f"AST Symbol Tree for {Path(file_path_str).name} ({len(symbols)} symbols):"]
    for s in symbols:
        lines.append(f"  - [{s['type'].upper()}] {s['name']} (Lines {s['line_no']}-{s['end_line_no']}): {s['details']}")
    return "\n".join(lines)
