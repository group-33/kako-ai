import os
import paramiko
import tempfile
from scp import SCPClient
from thefuzz import process
from pdf2image import convert_from_path
from dotenv import load_dotenv
import time

load_dotenv()

SSH_HOST = os.getenv("SSH_HOST")
SSH_PORT = int(os.getenv("SSH_PORT"))
SSH_USER = os.getenv("SSH_USER")
SSH_PASS = os.getenv("SSH_PASS")
REMOTE_DIR = os.getenv("REMOTE_DIR")

def fetch_file_via_ssh(filename: str) -> str:
    """Fetch a file from a remote SSH host into a local temp file.

    If SSH access is not configured via environment variables, a clear error
    is raised instead of attempting to connect to localhost.
    """
    if not SSH_HOST or not SSH_USER or not REMOTE_DIR:
        raise RuntimeError(
            "SSH-based file lookup is not configured "
            "(SSH_HOST, SSH_USER or REMOTE_DIR are missing)."
        )

    print(f"--- 🔍 Fuzzy Search: Looking for '{filename}' in {REMOTE_DIR}... ---")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            print(f"🔌 Connecting to SSH (Attempt {attempt + 1}/{max_retries})...")
            ssh.connect(
                SSH_HOST, 
                port=SSH_PORT, 
                username=SSH_USER, 
                password=SSH_PASS,
                # 🛑 CRITICAL: Give the proxy time to handshake!
                banner_timeout=30,  
                timeout=30
            )
            # If we get here, connection is successful
            break 
        except Exception as e:
            print(f"⚠️ Connection failed: {e}")
            if attempt < max_retries - 1:
                print(f"⏳ Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                print("❌ Max retries reached.")
                raise e # Re-raise the last error if all fail
    try:
        ssh.connect(SSH_HOST, port=SSH_PORT, username=SSH_USER, password=SSH_PASS)
        stdin, stdout, stderr = ssh.exec_command(f"ls -1 '{REMOTE_DIR}'")
        remote_files = [line.strip() for line in stdout.readlines()]
        
        if not remote_files:
            raise FileNotFoundError(f"Remote directory '{REMOTE_DIR}' empty/unreadable.")

        match_result = process.extractOne(filename, remote_files, score_cutoff=60)
        if match_result:
            best_filename, score = match_result
            print(f"--> Match Found: '{best_filename}' (Confidence: {score}%)")
        else:
            raise FileNotFoundError(f"No file found similar to '{filename}'")

        remote_path = f"{REMOTE_DIR}/{best_filename}"
        ext = os.path.splitext(best_filename)[1]
        temp_fd, local_path = tempfile.mkstemp(suffix=ext)
        os.close(temp_fd)
        
        with SCPClient(ssh.get_transport()) as scp:
            print(f"Downloading: {remote_path}")
            scp.get(remote_path, local_path)
            
        return local_path
        
    finally:
        ssh.close()

def convert_pdf_to_png(local_path: str) -> str:
    """Converts a PDF to PNG if necessary. Returns the path to the image."""
    if local_path.lower().endswith(".pdf"):
        print("--- 📄 Converting PDF (150 DPI)... ---")
        try:
            images = convert_from_path(local_path, dpi=150)
            if images:
                png_path = local_path.replace(".pdf", ".png")
                images[0].save(png_path, "PNG")
                return png_path
        except Exception as e:
            print(f"Warning: PDF conversion failed: {e}")
    return local_path
