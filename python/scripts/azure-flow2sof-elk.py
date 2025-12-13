#!/usr/bin/env python3
# SOF-ELK® Wrapper Script
# (C)2025 Lewes Technology Consulting, LLC

import sys
import os
import subprocess

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    package_path = os.path.join(project_root, "src")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = package_path + os.pathsep + env.get("PYTHONPATH", "")
    
    cmd = [sys.executable, "-m", "sof_elk.cli", "azure", "flow"] + sys.argv[1:]
    
    try:
        subprocess.check_call(cmd, env=env)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        sys.stderr.write(f"Error executing wrapper: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
