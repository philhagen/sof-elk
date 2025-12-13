import sys
import os
# Add current dir to path just in case
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import sof_elk.management.cli
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()
