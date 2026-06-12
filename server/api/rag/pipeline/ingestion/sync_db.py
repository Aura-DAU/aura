import os
import sys
import subprocess
from pathlib import Path

def run_step(script_name, cwd):
    print("\n" + "="*50)
    print(f"RUNNING STEP: {script_name} in {cwd}")
    print("="*50)
    
    # Use the current virtual environment's python
    venv_python = sys.executable
    
    process = subprocess.Popen(
        [venv_python, script_name],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Stream the output
    for line in process.stdout:
        print(line, end="")
        
    process.wait()
    if process.returncode != 0:
        print(f"\n[ERROR] Step {script_name} failed with exit code {process.returncode}")
        sys.exit(process.returncode)
    else:
        print(f"\n[SUCCESS] Step {script_name} completed.")

def main():
    base_dir = Path(__file__).resolve().parents[3]
    print(f"Base Directory: {base_dir}")
    
    chunking_dir = base_dir / "server" / "api" / "rag" / "pipeline" / "ingestion" / "chunking"
    embeddings_dir = base_dir / "server" / "api" / "rag" / "pipeline" / "ingestion" / "embeddings"
    
    # Step 1: Chunking
    run_step("process_all.py", chunking_dir)
    
    # Step 2: Generate Embeddings
    run_step("generate_embeddings.py", embeddings_dir)
    
    # Step 3: Upload to Pinecone
    run_step("upload_to_pinecone.py", embeddings_dir)
    
    print("\n" + "="*50)
    print("ALL STEPS COMPLETED. PINECONE INDEX IS FULLY SYNCED!")
    print("="*50)

if __name__ == "__main__":
    main()
