# openra_ir_compiler/exceptions.py
class IRValidationError(Exception):
    """Raised when the IR is malformed or invalid."""
    pass

class DependencyError(Exception):
    """Raised when dependency resolution fails (e.g., cycles)."""
    pass

class CodeGenerationError(Exception):
    """Raised when code generation fails."""
    pass
