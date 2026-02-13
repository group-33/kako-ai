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
        
        is_exact = (filename.lower() == best_filename.lower()) or (filename.lower() in best_filename.lower() and score == 100) # Strict exactness usually implies score 100
        
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


def get_pdf_orientation(local_path: str) -> str:
    """
    Detects if a PDF is landscape or portrait based on the first page.
    Returns "landscape" or "portrait".
    """
    if not local_path.lower().endswith(".pdf"):
        return "portrait" # Default

    try:
        from pypdf import PdfReader
        
        reader = PdfReader(local_path)
        if not reader.pages:
            return "portrait"
            
        page = reader.pages[0]
        
        # 1. Get Physical Dimensions (MediaBox)
        mbox = page.mediabox
        width = float(mbox.width)
        height = float(mbox.height)
        
        # 2. Check for Rotation
        rotation = page.get("/Rotate", 0)
        rotation = int(rotation) % 360
        
        if rotation in (90, 270):
             width, height = height, width
             
        # 3. Decision
        if width > height:
            return "landscape"
            
    except Exception as e:
        print(f"Warning: Orientation detection failed (pypdf): {e}")
    
    return "portrait"
