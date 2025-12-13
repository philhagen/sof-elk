#!/usr/bin/env python3
import subprocess
import sys
import os
import shutil

def get_hatch_executable():
    # 1. Check PATH
    hatch = shutil.which("hatch")
    if hatch:
        return hatch
        
    # 2. Ask pip where it installed it
    try:
        out = subprocess.check_output([sys.executable, "-m", "pip", "show", "hatch"], text=True)
        location = None
        for line in out.splitlines():
            if line.startswith("Location:"):
                location = line.split(":", 1)[1].strip()
                break
        
        if location:
            # Expected: ...\PythonXX\site-packages
            # Scripts:  ...\PythonXX\Scripts
            # OR ...\Lib\site-packages -> ...\Scripts
            
            # Remove site-packages
            base_path = os.path.dirname(location) 
            
            # Check for Scripts folder at base_path or base_path/../Scripts
            candidates = [
                os.path.join(base_path, "Scripts", "hatch.exe"),
                os.path.join(os.path.dirname(base_path), "Scripts", "hatch.exe"),
                os.path.join(base_path, "bin", "hatch"), # non-windows fallback
            ]
            
            for path in candidates:
                if os.path.exists(path):
                    return path
                    
    except subprocess.CalledProcessError:
        pass
        
    return None

def install_hatch():
    print(f"Installing hatch using {sys.executable}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "hatch"])
        print("Hatch installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install hatch: {e}")
        sys.exit(1)

def run_step(description, cmd, hatch_path):
    print(f"Running step: {description}")
    try:
        # Use python -m hatch to ensure we use the installed module without PATH issues
        if cmd[0] == "hatch":
            cmd = [sys.executable, "-m", "hatch"] + cmd[1:]
        
        # We don't need to manipulate PATH for scripts dir if we use -m hatch
        env = os.environ.copy()
        scripts_dir = os.path.dirname(hatch_path)
        if scripts_dir not in env["PATH"]:
            env["PATH"] = scripts_dir + os.pathsep + env["PATH"]
            
        subprocess.check_call(cmd, env=env)
        print(f"Step '{description}' completed successfully.\n")
    except subprocess.CalledProcessError as e:
        print(f"Step '{description}' failed: {e}")
        sys.exit(1)

def main():
    hatch_path = get_hatch_executable()
    
    if not hatch_path:
        install_hatch()
        hatch_path = get_hatch_executable()
        
    if not hatch_path:
        print("Could not find hatch executable after installation.")
        sys.exit(1)
        
    print(f"Using hatch at: {hatch_path}")
    
    run_step("Create Environment", ["hatch", "env", "create"], hatch_path)
    run_step("Build Project", ["hatch", "build"], hatch_path)
    run_step("Generate ECS Fields", ["hatch", "run", "gen-ecs"], hatch_path)
    run_step("Run Tests", ["hatch", "run", "test", "tests/unit/test_refactored_scripts.py"], hatch_path)

if __name__ == "__main__":
    main()
