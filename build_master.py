import os
import re

# Directories to exclude
EXCLUDE_DIRS = {
    '.git', '.github', '.vscode', 'frontend', 'venv', 'node_modules', 
    'JOB_FILES', '__pycache__', 'kplc_pdfs'
}

def find_all_py_files():
    py_files = []
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    for root, dirs, files in os.walk(base_dir):
        # Exclude specified directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            if file.endswith('.py'):
                # Avoid master_py.py, build_master.py, run_all_scripts.py, etc.
                if file in ['master_py.py', 'build_master.py', 'run_all_scripts.py', 'inspect_amazon.py', 'inspect_au.py', 'uploading.py']:
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, base_dir)
                py_files.append(rel_path.replace('\\', '/'))
                
    return sorted(py_files, key=lambda x: x.lower())

def generate_master_py():
    py_files = find_all_py_files()
    print(f"Found {len(py_files)} python files in company subdirectories.")
    
    master_content = []
    # Header of master_py.py
    master_content.append('''# -*- coding: utf-8 -*-
"""
==============================================================================
MASTER PYTHON SCRIPTS RUNNER & DEBUGGER
==============================================================================
This file compiles and wraps all python scripts from the company folders.
It allows running and debugging each company script individually or in sequence.
"""

import os
import sys
import traceback
import importlib
import asyncio

# Prevent UnicodeEncodeError on Windows console when printing emoji/unicode
if sys.platform == 'win32':
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except Exception:
        pass

# Original working directory and sys.path
ORIGINAL_CWD = os.getcwd()
ORIGINAL_SYS_PATH = list(sys.path)

class EnvironmentGuard:
    """Context manager to isolate current working directory and sys.path for each script."""
    def __init__(self, script_path):
        self.script_path = script_path
        self.script_dir = os.path.dirname(os.path.abspath(script_path))
        self.old_cwd = os.getcwd()
        self.old_path = list(sys.path)

    def __enter__(self):
        print(f"\\n[ENV] Switching CWD to: {self.script_dir}")
        os.chdir(self.script_dir)
        if self.script_dir not in sys.path:
            sys.path.insert(0, self.script_dir)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.old_cwd)
        sys.path = self.old_path
        if exc_type:
            print(f"\\n❌ Error execution in {self.script_path}:")
            traceback.print_exception(exc_type, exc_val, exc_tb)
            return True # Prevent exception from crashing the master script
        return False
''')

    # Now wrap each script
    script_registry = []
    
    for script_rel_path in py_files:
        # Create a safe python function name from the relative path
        # e.g. "Accor/accor.py" -> "run_Accor_accor"
        safe_name = "run_" + re.sub(r'[^a-zA-Z0-9_]', '_', script_rel_path.replace('.py', ''))
        script_registry.append((script_rel_path, safe_name))
        
        master_content.append(f"\n# {'='*80}")
        master_content.append(f"# SCRIPT: {script_rel_path}")
        master_content.append(f"# {'='*80}")
        master_content.append(f"def {safe_name}():")
        master_content.append(f"    \"\"\"Wrapper execution for {script_rel_path}\"\"\"")
        master_content.append(f"    with EnvironmentGuard({repr(script_rel_path)}):")
        
        # Read the file and indent its lines
        has_lines = False
        try:
            with open(script_rel_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Write lines indented by 8 spaces (4 spaces inside def, 4 spaces inside with statement)
            for line in lines:
                stripped = line.rstrip()
                if stripped:
                    master_content.append("        " + stripped)
                    has_lines = True
                else:
                    master_content.append("")
        except Exception as e:
            master_content.append(f"        print(f'Failed to read script content: {e}')")
            has_lines = True
            
        if not has_lines:
            master_content.append("        pass")
            
        master_content.append("") # Empty line after function

    # Add interactive CLI/UI at the bottom of master_py.py
    master_content.append('''
# ==============================================================================
# INTERACTIVE RUNNER MENU
# ==============================================================================

SCRIPTS = [
''')
    for script_rel_path, safe_name in script_registry:
        master_content.append(f"    ({repr(script_rel_path)}, {safe_name}),")
        
    master_content.append(''']

def display_menu():
    print("\\n" + "=" * 80)
    print("                    MASTER SCRIPTS RUNNER & DEBUGGER")
    print("=" * 80)
    print(f"Total scripts compiled: {len(SCRIPTS)}")
    print("-" * 80)
    
    # Print in columns to look clean and neat
    col_width = 38
    for idx, (path, _) in enumerate(SCRIPTS, 1):
        # Format script path nicely
        display_name = f"{idx:2d}. {path}"
        if len(display_name) > col_width - 2:
            display_name = display_name[:col_width-5] + "..."
        
        # We can print two per line
        if idx % 2 == 1:
            print(f"{display_name:<{col_width}}", end="")
        else:
            print(f"{display_name}")
            
    if len(SCRIPTS) % 2 != 0:
        print()
        
    print("-" * 80)
    print("Options:")
    print("  [number]  - Run and debug a specific script (e.g. 1)")
    print("  all       - Run all scripts sequentially with error isolation")
    print("  find [str]- Find scripts by company or name")
    print("  exit/q    - Exit the debugger")
    print("=" * 80)

def main():
    while True:
        display_menu()
        try:
            choice = input("\\nEnter your choice: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\\nExiting.")
            break
            
        if not choice:
            continue
            
        if choice.lower() in ['exit', 'q', 'quit']:
            print("Exiting.")
            break
            
        elif choice.lower() == 'all':
            print(f"Starting execution of all {len(SCRIPTS)} scripts...")
            for i, (path, func) in enumerate(SCRIPTS, 1):
                print(f"\\n[{i}/{len(SCRIPTS)}] Running {path}...")
                try:
                    func()
                except Exception as e:
                    print(f"Fatal error running {path}: {e}")
            print("\\nAll scripts executed.")
            
        elif choice.lower().startswith('find '):
            query = choice[5:].strip().lower()
            results = []
            for idx, (path, _) in enumerate(SCRIPTS, 1):
                if query in path.lower():
                    results.append((idx, path))
            if results:
                print(f"\\nMatches for '{query}':")
                for idx, path in results:
                    print(f"  [{idx}] {path}")
            else:
                print(f"\\nNo scripts match '{query}'")
                
        elif choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(SCRIPTS):
                path, func = SCRIPTS[idx - 1]
                print(f"\\nExecuting script {idx}: {path}")
                print("-" * 80)
                try:
                    func()
                except Exception as e:
                    print(f"Fatal error running {path}: {e}")
                print("-" * 80)
                print(f"Finished executing {path}")
            else:
                print(f"Invalid script number. Please choose between 1 and {len(SCRIPTS)}")
        else:
            print("Invalid input. Please enter a valid option.")

if __name__ == '__main__':
    main()
''')

    # Write the compiled master file
    with open('master_py.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(master_content))
    print("Successfully generated master_py.py!")

if __name__ == '__main__':
    generate_master_py()
