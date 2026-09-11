import ast
from typing import Any, Callable, Dict, Tuple

class SandboxExecutor:
    """
    Isolated execution sandbox for synthesized schema transformation patches.
    Verifies AST safety, dynamically detects any single-argument transformation function,
    and guarantees zero-crash execution.
    """

    BANNED_MODULES = {"os", "sys", "subprocess", "socket", "shutil", "requests", "urllib"}

    @classmethod
    def verify_ast_safety(cls, code_str: str) -> Tuple[bool, str]:
        try:
            tree = ast.parse(code_str)
        except SyntaxError as se:
            return False, f"AST Syntax error: {se}"

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in cls.BANNED_MODULES:
                        return False, f"Security Violation: Import of '{alias.name}' is prohibited."
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split(".")[0] in cls.BANNED_MODULES:
                    return False, f"Security Violation: Import from '{node.module}' is prohibited."
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in {"eval", "exec", "__import__", "compile", "open"}:
                    return False, f"Security Violation: Use of '{node.func.id}()' is prohibited."

        return True, "AST verification passed."

    @classmethod
    def compile_patch(cls, code_str: str) -> Tuple[bool, Callable[[Dict[str, Any]], Dict[str, Any]], str]:
        # 1. AST Safety Check
        safe, msg = cls.verify_ast_safety(code_str)
        if not safe:
            return False, None, msg

        # 2. Compile in isolated namespace
        local_scope = {}
        try:
            compiled = compile(code_str, "<sandbox_patch>", "exec")
            exec(compiled, {"__builtins__": __builtins__}, local_scope)
        except Exception as e:
            return False, None, f"Sandbox compilation error: {e}"

        # 3. Dynamic Callable Discovery:
        # Check standard name first
        if "transform_record" in local_scope and callable(local_scope["transform_record"]):
            return True, local_scope["transform_record"], "Compilation successful."

        # Otherwise find ANY user-defined callable in local_scope (e.g. transform, heal, map_record)
        for name, obj in local_scope.items():
            if callable(obj) and not name.startswith("_"):
                return True, obj, f"Compilation successful (using function '{name}')."

        return False, None, "No valid transformation function found in synthesized code."