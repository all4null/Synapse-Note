import sys
import os
import inspect

# Add path to synapse-core
current_dir = os.getcwd()
# Assuming we are running from 'c:\Users\JM\Desktop\새 폴더 (2)' or similar
synapse_core_path = os.path.join(current_dir, "synapse-core")
if synapse_core_path not in sys.path:
    sys.path.append(synapse_core_path)

try:
    from stt.Clova import ClovaSpeechClient
    print("Successfully imported ClovaSpeechClient")
    
    # Get source code of transcribe_from_file
    source = inspect.getsource(ClovaSpeechClient.transcribe_from_file)
    print("\n--- Source of transcribe_from_file ---")
    print(source)
    print("--------------------------------------")
    
    if "self.speaker_info" in source:
        print("\n[FAIL] 'self.speaker_info' found in source code!")
    else:
        print("\n[PASS] 'self.speaker_info' NOT found in source code.")
        
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
