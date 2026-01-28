import os
import paramiko
import tempfile
from scp import SCPClient
from thefuzz import process
from pdf2image import convert_from_path
from dotenv import load_dotenv

load_dotenv()

SSH_HOST = os.getenv("SSH_HOST")
SSH_PORT = int(os.getenv("SSH_PORT"))
SSH_USER = os.getenv("SSH_USER")
SSH_PASS = os.getenv("SSH_PASS")
REMOTE_DIR = os.getenv("REMOTE_DIR")

def fetch_file_via_ssh(filename: str) -> tuple[str, str, bool]:
    """Fetch a file from a remote SSH host into a local temp file.

    Returns:
        (local_path, remote_filename, is_exact_match)
    """
    if not SSH_HOST or not SSH_USER or not REMOTE_DIR:
        raise RuntimeError(
            "SSH-based file lookup is not configured "
            "(SSH_HOST, SSH_USER or REMOTE_DIR are missing)."
        )

    print(f"--- 🔍 Fuzzy Search: Looking for '{filename}' in {REMOTE_DIR}... ---")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
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
        
        # Determine if it was an exact match (ignoring case maybe, but file systems are picky)
        # We'll treat case-insensitive equality as "exact enough" for valid files
        is_exact = (filename.lower() == best_filename.lower()) or (filename.lower() in best_filename.lower() and score == 100) # Strict exactness usually implies score 100
        
        # Actually, let's just trust string equality for "Exact".
        # If user asked for "Drawing-123" and we found "Drawing-123.pdf", that's usually considered exact in this tool context? 
        # But `filename` input might not have extension.
        # Let's say: if input is contained in output with high score, or equals.
        # Simplest: if filename.lower().strip() == best_filename.lower().strip() (ignoring extension if user omitted it?)
        # Let's stick to strict equality check for "Exact" vs "Did you mean".
        is_exact = filename == best_filename
        
        return local_path, best_filename, is_exact
        
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
