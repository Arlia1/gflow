#!/usr/bin/env python3
"""
Pipeline Orchestrator for Todo Frenos Instagram Content
Executes: Topic Brief -> Google Flow Generation -> Voiceover -> Assembly -> Instagram Publish
"""

import os
import sys
import subprocess

def run_pipeline(topic="pedal_duro"):
    print(f"=== Starting Todo Frenos Pipeline for topic: {topic} ===")
    
    # 1. Trigger Google Flow generation
    print("\n[Step 1] Triggering Google Flow visual generation...")
    res = subprocess.run(["node", "scripts/flow_generator.js"], capture_output=True, text=True)
    print(res.stdout)
    if res.returncode != 0:
        print("Error in Google Flow step:", res.stderr)
        return False
        
    # 2. Voiceover
    print("\n[Step 2] Synthesizing voiceover...")
    subprocess.run(["python3", "scripts/voice_generator.py"])
    
    print("\n[Step 3] Ready for review & publication.")
    return True

if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "pedal_duro"
    run_pipeline(topic)
