#!/usr/bin/env python3
"""
Script to verify the PCB AiD backend installation and dependencies.
"""
import importlib
import os
import sys
from pathlib import Path

# Required modules
REQUIRED_MODULES = [
    # Core modules
    "fastapi",
    "uvicorn",
    "pydantic",
    "dotenv",
    
    # PCB analysis modules
    "networkx",
    "shapely",
    
    # LangChain and OpenRouter modules
    "langchain",
    "langchain_openai",
    "langgraph",
    "requests",
    "httpx"
]

# Required files
REQUIRED_FILES = [
    "app.py",
    "main.py", 
    "trace_extractor.py",
    "api_key_manager.py",
    "api_routes.py",
    "test_openrouter.py",
    "ai/config.py",
    "ai/utils.py",
    "ai/workflow.py",
    "ai/agents/pcb_agents.py",
    "ai/tools/pcb_tools.py",
]

def check_modules():
    """Check if all required modules are installed."""
    print("Checking Python modules...")
    
    all_modules_found = True
    for module_name in REQUIRED_MODULES:
        try:
            # Handle hyphenated package names
            import_name = module_name.replace("-", "_")
            importlib.import_module(import_name)
            print(f"✅ {module_name}")
        except ImportError:
            print(f"❌ {module_name} - NOT FOUND")
            all_modules_found = False
    
    return all_modules_found

def check_files():
    """Check if all required files exist."""
    print("\nChecking required files...")
    
    all_files_found = True
    base_dir = Path(__file__).parent
    
    for file_path in REQUIRED_FILES:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - NOT FOUND")
            all_files_found = False
    
    return all_files_found

def check_openrouter_api_key():
    """Check if OpenRouter API key is configured."""
    print("\nChecking OpenRouter API key configuration...")
    
    # Check .env file
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        print("❌ .env file not found")
        return False
    
    # Check if OPENROUTER_API_KEY is set in environment
    from dotenv import load_dotenv
    load_dotenv(env_path)
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in .env file")
        return False
    
    print(f"✅ OpenRouter API key found (starting with {api_key[:8]}...)")
    return True

def main():
    """Main function."""
    print("PCB AiD Backend Installation Verification\n")
    print("=" * 40)
    
    # Check Python version
    py_version = sys.version.split()[0]
    print(f"Python version: {py_version}")
    
    # Check modules
    modules_ok = check_modules()
    
    # Check files
    files_ok = check_files()
    
    # Check OpenRouter API key
    api_key_ok = check_openrouter_api_key()
    
    # Summary
    print("\n" + "=" * 40)
    print("Installation verification summary:")
    print(f"Required modules: {'✅ OK' if modules_ok else '❌ Missing modules'}")
    print(f"Required files: {'✅ OK' if files_ok else '❌ Missing files'}")
    print(f"OpenRouter API key: {'✅ Configured' if api_key_ok else '❌ Not configured'}")
    
    if modules_ok and files_ok and api_key_ok:
        print("\n✅ Installation complete! You can run the server with: ./run_server.sh")
        return 0
    else:
        print("\n❌ Installation incomplete. Please fix the issues above.")
        
        if not modules_ok:
            print("\nTo install missing modules, run: pip install -r requirements.txt")
        
        if not api_key_ok:
            print("\nTo configure OpenRouter API key, run: python setup_env.py")
        
        return 1

if __name__ == "__main__":
    sys.exit(main()) 