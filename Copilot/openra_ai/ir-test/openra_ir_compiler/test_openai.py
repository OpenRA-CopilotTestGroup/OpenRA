# openra_ir_compiler/test_openai.py
import os
import json
import time
from dotenv import load_dotenv
from openai import OpenAI
import importlib
from . import compile_ir  # Import the function directly

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in .env")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Force reload of generator module to ensure latest version
import openra_ir_compiler.generator
importlib.reload(openra_ir_compiler.generator)

def load_file(file_path):
    """Load content from a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def generate_ir(command):
    """Generate IR JSON from a natural language command using OpenAI."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    prompt = load_file(os.path.join(base_dir, 'prompt.txt'))
    ir_spec = load_file(os.path.join(base_dir, 'ir_spec.txt'))
    api_summary = load_file(os.path.join(base_dir, 'game_api_summary.txt'))

    full_prompt = f"{prompt}\n\nIR Specification:\n{ir_spec}\n\nGameAPI Summary:\n{api_summary}\n\n当前命令：\"{command}\"\n生成对应的IR JSON："

    # Start timing LLM response
    llm_start_time = time.time()
    
    # Call OpenAI API (compatible with 1.65.0)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # Use "gpt-4o" or similar if available
        messages=[
            {"role": "system", "content": full_prompt},
            {"role": "user", "content": command}
        ],
        temperature=0.2,
    )
    
    # Calculate LLM response time
    llm_response_time = time.time() - llm_start_time
    
    # Extract the response content
    ir_json_str = response.choices[0].message.content.strip()
    
    # Start timing post-processing
    post_processing_start_time = time.time()
    
    # Try to extract JSON from the response
    try:
        # Find JSON content between triple backticks if present
        if "```json" in ir_json_str and "```" in ir_json_str.split("```json", 1)[1]:
            ir_json_str = ir_json_str.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in ir_json_str and "```" in ir_json_str.split("```", 1)[1]:
            ir_json_str = ir_json_str.split("```", 1)[1].split("```", 1)[0].strip()
            
        # Parse the JSON
        ir_json = json.loads(ir_json_str)
        
        # Calculate post-processing time
        post_processing_time = time.time() - post_processing_start_time
        
        # Log timing information
        print(f"Command: '{command}'")
        print(f"LLM Response Time: {llm_response_time:.2f} seconds")
        print(f"Post-processing Time: {post_processing_time:.2f} seconds")
        print(f"Total Time: {llm_response_time + post_processing_time:.2f} seconds")
        print("-" * 50)
        
        return ir_json
    except json.JSONDecodeError as e:
        post_processing_time = time.time() - post_processing_start_time
        print(f"Command: '{command}'")
        print(f"LLM Response Time: {llm_response_time:.2f} seconds")
        print(f"Post-processing Time: {post_processing_time:.2f} seconds (Failed)")
        print(f"Error: JSON parsing failed - {str(e)}")
        print(f"Raw response: {ir_json_str}")
        print("-" * 50)
        raise ValueError(f"Failed to parse JSON from response: {e}")

def test_command(command):
    """Test the full pipeline: command → IR → Python code with timing."""
    try:
        # Start timing the entire process
        total_start_time = time.time()
        
        # Print command info
        print(f"\nTesting command: '{command}'")
        print("-" * 50)
        
        # Generate IR
        print("Generating IR...")
        ir_start_time = time.time()
        ir_json = generate_ir(command)
        ir_time = time.time() - ir_start_time
        
        # Print the generated IR
        print("Generated IR:")
        print(json.dumps(ir_json, indent=2, ensure_ascii=False))
        print("-" * 50)
        
        # Compile IR to code
        print("Compiling IR to Python code...")
        compile_start_time = time.time()
        print("Actions being compiled:", json.dumps(ir_json["actions"], indent=2, ensure_ascii=False))
        try:
            python_code = compile_ir(ir_json)  # Call the function directly
        except Exception as e:
            print(f"Compile error: {str(e)}")
            raise  # Preserve stack trace for debugging
        compile_time = time.time() - compile_start_time
        
        # Print the generated code
        print("<code>")
        print(python_code)
        print("</code>")
        print("-" * 50)
        
        # Calculate total time
        total_time = time.time() - total_start_time
        
        # Log detailed timing information
        print(f"Detailed timing for command: '{command}'")
        print(f"IR Generation Time: {ir_time:.2f} seconds")
        print(f"Code Compilation Time: {compile_time:.2f} seconds")
        print(f"Total Processing Time: {total_time:.2f} seconds")
        print("=" * 50)
        
        return {
            "ir": ir_json,
            "code": python_code,
            "timing": {
                "ir_generation": ir_time,
                "code_compilation": compile_time,
                "total": total_time
            }
        }
    except Exception as e:
        print(f"Error processing command '{command}': {str(e)}")
        raise  # Re-raise to capture full stack trace
        return {"error": str(e)}

if __name__ == "__main__":
    # Example usage
    test_commands = [
        "所有单位攻击敌方基地",
        "派這三個步兵去探路",
        "生产5个步枪兵5个火箭兵"
    ]
    
    results = {}
    for cmd in test_commands:
        results[cmd] = test_command(cmd)
    
    # Print summary
    print("\n===== PERFORMANCE SUMMARY =====")
    for cmd, result in results.items():
        if "timing" in result:
            timing = result["timing"]
            print(f"Command: '{cmd}'")
            print(f"  IR Generation: {timing['ir_generation']:.2f}s")
            print(f"  Code Compilation: {timing['code_compilation']:.2f}s")
            print(f"  Total Time: {timing['total']:.2f}s")
        else:
            print(f"Command: '{cmd}' - Failed: {result.get('error', 'Unknown error')}")