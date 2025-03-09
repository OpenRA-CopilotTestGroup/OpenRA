# openra_ir_compiler/__init__.py
from .parser import IRParser
from .dependency import DependencyResolver
from .generator import CodeGenerator

def compile_ir(ir_json):
    """Main entry point for IR compilation."""
    parser = IRParser(ir_json)
    parsed_actions = parser.parse()
    resolver = DependencyResolver(parsed_actions)
    ordered_actions = resolver.resolve()  # Get dependency-ordered actions
    generator = CodeGenerator(ordered_actions)  # Pass ordered actions
    return generator.generate()
