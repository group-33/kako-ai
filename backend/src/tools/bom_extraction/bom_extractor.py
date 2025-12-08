# bom_extractor.py
import os
import numpy as np
import sys
import cv2
import dspy
import gc
import paramiko
import tempfile
import pytesseract
from pytesseract import Output
from scp import SCPClient
from thefuzz import process
from pdf2image import convert_from_path
from pydantic import BaseModel, Field
from models import BillOfMaterials
from dotenv import load_dotenv
import base64

load_dotenv()
SSH_HOST = os.getenv("SSH_HOST")
SSH_PORT = int(os.getenv("SSH_PORT")) # Default to 22 if missing
SSH_USER = os.getenv("SSH_USER")
SSH_PASS = os.getenv("SSH_PASS")
REMOTE_DIR = os.getenv("REMOTE_DIR")
YOUR_API_KEY = os.getenv("GEMINI_API_KEY")
bad_words = [
    "gmbh", "hirt", "heidelberg",
    "vertraulich", "confidential", "version","GmbH", "HIRT", "Date","drawn"
]
def filter_unsafe_tables(table_images: list, unsafe_keywords: list = None) -> list:
    """
    Takes a list of images (numpy arrays), OCRs them, and removes 
    any that contain specific 'unsafe' keywords.
    """
    if not table_images:
        return []

    # Default unsafe keywords (normalized to lowercase)
    if unsafe_keywords is None:
        unsafe_keywords = ["gmbh", "hirt", "heidelberg", "confidential"]
    
    # Ensure all keywords are lowercase for case-insensitive matching
    unsafe_keywords = [k.lower() for k in unsafe_keywords]
    
    filtered_results = []
    
    print(f"--- 🔍 Filtering {len(table_images)} tables for unsafe data ---")

    for i, img in enumerate(table_images):
        # 1. Preprocessing for Tesseract
        # Tesseract works best on high-contrast grayscale
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
            
        # Optional: Thresholding to make text crisp black-on-white
        # This helps if the "GmbH" is faint or has a gray background
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        # 2. Run OCR
        # --psm 6 assumes a single uniform block of text (good for headers/tables)
        # --psm 3 is fully automatic (good if the crop includes random graphics)
        try:
            text = pytesseract.image_to_string(binary, config='--psm 6')
            text_lower = text.lower()
            
            # 3. Check for Keywords
            # We look for ANY match. If we find one, we mark it unsafe.
            found_unsafe = False
            for keyword in unsafe_keywords:
                if keyword in text_lower:
                    print(f"   ❌ Table {i} dropped! Found unsafe keyword: '{keyword}'")
                    found_unsafe = True
                    break # Stop checking other keywords for this image
            
            # 4. Keep or Discard
            if not found_unsafe:
                print(f"   ✅ Table {i} is safe.")
                filtered_results.append(img)
                
        except Exception as e:
            print(f"   ⚠️ OCR Failed for Table {i}: {e}. Keeping it by default.")
            filtered_results.append(img)

    return filtered_results

def split_merged_crop(crop_img):
    if crop_img.size == 0: return []
    
    h, w = crop_img.shape[:2]
    
    if len(crop_img.shape) == 3:
        gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
    else:
        gray = crop_img
        
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

    # ==========================================
    # TUNING PARAMETER 1: THE STRUCTURAL KERNEL
    # ==========================================
    # CHANGE: Lowered from 30 to 15.
    # Why? A smaller number makes the kernel WIDER.
    # A wider kernel forces the code to bridge empty columns inside a table.
    line_scale = 15 
    hor_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (w // line_scale, 1))
    
    horizontal_structure = cv2.erode(binary, hor_kernel, iterations=1)
    horizontal_structure = cv2.dilate(horizontal_structure, hor_kernel, iterations=2)

    # ==========================================
    # TUNING PARAMETER 2: IGNORE HEADERS/FOOTERS
    # ==========================================
    # FIX: These cannot be 0.0.
    # To handle your Shared Footer, we look at the range from 15% to 65%.
    # This ignores the top header (0-15%) and the bottom footer area (65-100%).
    
    roi_top_cut = int(h * 0.15)    
    roi_bottom_cut = int(h * 0.65) # <--- FIXED (Was 0.0)
    
    # Safety Check: If image is tiny, reset to full height to prevent crash
    if roi_bottom_cut <= roi_top_cut:
        roi_top_cut = 0
        roi_bottom_cut = h

    roi_structure = horizontal_structure[roi_top_cut:roi_bottom_cut, :]
    
    structure_projection = np.sum(roi_structure, axis=0)

    # ==========================================
    # TUNING PARAMETER 3: THE "GAP" THRESHOLD
    # ==========================================
    # 0.02 is usually safer than 0.05 if it's splitting too aggressively.
    sensitivity = 0.02 
    
    roi_h = roi_bottom_cut - roi_top_cut
    break_threshold = roi_h * sensitivity * 255 
    
    gap_indices = np.where(structure_projection <= break_threshold)[0]

    if len(gap_indices) == 0:
        return [crop_img]

    # --- Standard Split Logic ---
    split_candidates = []
    current_gap = []
    for idx in gap_indices:
        if not current_gap or idx == current_gap[-1] + 1:
            current_gap.append(idx)
        else:
            if len(current_gap) > 0: split_candidates.append(current_gap)
            current_gap = [idx]
    if current_gap: split_candidates.append(current_gap)

    valid_splits = []
    min_gap_width = 5 
    margin_safety = w * 0.15 
    
    for gap in split_candidates:
        gap_width = len(gap)
        gap_center = gap[0] + gap_width // 2
        
        if gap_width >= min_gap_width:
            if margin_safety < gap_center < (w - margin_safety):
                valid_splits.append(gap_center)

    if valid_splits:
        valid_splits.sort(key=lambda x: abs(x - w//2))
        split_x = valid_splits[0]
        print(f"   -> Split success at x={split_x}")
        return [crop_img[:, :split_x], crop_img[:, split_x:]]
    
    return [crop_img]

def extract_bom_tight_crop(image_path, output_dir="/tmp"):
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    filename_base = os.path.splitext(os.path.basename(image_path))[0]

    # 1. Load & Preprocess
    original_img = cv2.imread(image_path)
    if original_img is None:
        print(f"Error: Could not load image at {image_path}")
        return []
    
    img_h, img_w = original_img.shape[:2]
    gray = cv2.cvtColor(original_img, cv2.COLOR_BGR2GRAY)
    
    # Adaptive Threshold
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 11, 2
    )
    
    # 2. Extract Lines
    scale = 50 
    kernel_len = img_w // scale
    
    ver_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_len))
    hor_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_len, 1))
    fat_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

    img_temp1 = cv2.erode(binary, ver_kernel, iterations=3)
    vert_lines = cv2.dilate(img_temp1, ver_kernel, iterations=3)
    
    img_temp2 = cv2.erode(binary, hor_kernel, iterations=3)
    hor_lines = cv2.dilate(img_temp2, hor_kernel, iterations=3)
    
    vert_lines = cv2.dilate(vert_lines, fat_kernel, iterations=1)
    hor_lines = cv2.dilate(hor_lines, fat_kernel, iterations=1)

    # 3. Find Joints
    joints = cv2.bitwise_and(vert_lines, hor_lines)
    
    # 4. Weaving
    gap_w = img_w // 5   
    gap_h = img_h // 20 
    
    kernel_h_stitch = cv2.getStructuringElement(cv2.MORPH_RECT, (gap_w, 1)) 
    mask_horizontal = cv2.dilate(joints, kernel_h_stitch, iterations=1)
    
    kernel_v_stitch = cv2.getStructuringElement(cv2.MORPH_RECT, (1, gap_h))
    mask_woven = cv2.dilate(mask_horizontal, kernel_v_stitch, iterations=1)

    # 5. Find Contours
    contours, _ = cv2.findContours(mask_woven, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    table_crops = []
    
    total_image_area = img_w * img_h
    min_area_threshold = total_image_area * 0.05 

    print(f"Processing {len(contours)} candidates...")

    for i, c in enumerate(contours):
        bx, by, bw, bh = cv2.boundingRect(c)
        current_area = bw * bh
        
        if current_area < min_area_threshold: continue
        if bw > 0.9 * img_w and bh > 0.9 * img_h: continue

        # --- TIGHT CROP LOGIC ---
        joints_roi = joints[by:by+bh, bx:bx+bw]
        points = cv2.findNonZero(joints_roi)

        if points is not None:
            points_x = points[:, 0, 0]
            points_y = points[:, 0, 1]

            min_x_roi = np.min(points_x)
            max_x_roi = np.max(points_x)
            min_y_roi = np.min(points_y)
            max_y_roi = np.max(points_y)

            tight_x1 = bx + min_x_roi
            tight_y1 = by + min_y_roi
            tight_x2 = bx + max_x_roi
            tight_y2 = by + max_y_roi

            tiny_pad = 5 
            final_x1 = max(0, tight_x1 - tiny_pad)
            final_y1 = max(0, tight_y1 - tiny_pad)
            final_x2 = min(img_w, tight_x2 + tiny_pad)
            final_y2 = min(img_h, tight_y2 + tiny_pad)

            # Initial Crop
            crop = original_img[final_y1:final_y2, final_x1:final_x2]
            
            # ### NEW CODE STARTS HERE ###
            # Instead of saving immediately, we check if it needs splitting
            
            sub_crops = split_merged_crop(crop)
            
            for part_idx, final_crop in enumerate(sub_crops):
                out_path = f"{output_dir}/{filename_base}_crop_{i}_part_{part_idx}.png"
                cv2.imwrite(out_path, final_crop)
                table_crops.append(final_crop)
                print(f"Table extracted: {out_path} (Size: {final_crop.shape[1]}x{final_crop.shape[0]})")
            
            # ### NEW CODE ENDS HERE ###

        else:
             print(f"Warning: Contour {i} had area but no precise joints found inside.")

    if not table_crops:
        print("No tables found.")

    return table_crops

# Usage
# extract_bom_tables_stitched("drawing.png")
def fetch_file_via_ssh(filename: str) -> str:
    print(f"--- 🔍 Fuzzy Search: Looking for '{filename}' in {REMOTE_DIR}... ---")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(SSH_HOST, port=SSH_PORT, username=SSH_USER, password=SSH_PASS)
        
        # --- 1. GET FILE LIST ---
        # We run 'ls' on the remote PC to see what files actually exist.
        # We use quotes around REMOTE_DIR to handle spaces in folder names.
        stdin, stdout, stderr = ssh.exec_command(f"ls -1 '{REMOTE_DIR}'")
        
        # Read the output into a Python list
        remote_files = [line.strip() for line in stdout.readlines()]
        
        if not remote_files:
            raise FileNotFoundError(f"Remote directory '{REMOTE_DIR}' appears empty or unreadable.")

        # --- 2. FUZZY MATCH ---
        # finding the single best match from the list
        # score_cutoff=60 ensures we don't pick random garbage if nothing matches
        match_result = process.extractOne(filename, remote_files, score_cutoff=60)
        
        if match_result:
            best_filename, score = match_result
            print(f"--> Match Found: '{best_filename}' (Confidence: {score}%)")
        else:
            raise FileNotFoundError(f"No file found similar to '{filename}'")

        # --- 3. DOWNLOAD THE MATCH ---
        remote_path = f"{REMOTE_DIR}/{best_filename}"
        
        # Create temp file with the CORRECT extension from the found file
        ext = os.path.splitext(best_filename)[1]
        temp_fd, local_path = tempfile.mkstemp(suffix=ext)
        os.close(temp_fd)
        
        # Use SCP to download the REAL file we found
        with SCPClient(ssh.get_transport()) as scp:
            print(f"Downloading: {remote_path}")
            scp.get(remote_path, local_path)
            
        print(f"--- ✅ File saved locally to: {local_path} ---")
        return local_path
        
    except Exception as e:
        print(f"--- ❌ Error: {e} ---")
        raise e
    finally:
        ssh.close()

def numpy_to_base64(img_array):
    """Converts an OpenCV image (numpy) to a Base64 string for the LLM."""
    _, buffer = cv2.imencode('.png', img_array)
    return base64.b64encode(buffer).decode('utf-8')

def merge_images_vertically(image_list, padding=20):
    """
    Stacks a list of OpenCV images vertically. 
    Adds white padding between them to separate tables visually.
    """
    if not image_list:
        return None
        
    # 1. Find max width to normalize image sizes
    max_width = max(img.shape[1] for img in image_list)
    
    processed_images = []
    
    for img in image_list:
        h, w = img.shape[:2]
        
        # If image is narrower than max_width, pad it with white on the right
        if w < max_width:
            pad_width = max_width - w
            if len(img.shape) == 3: # Color
                img = np.pad(img, ((0,0), (0, pad_width), (0,0)), mode='constant', constant_values=255)
            else: # Grayscale
                img = np.pad(img, ((0,0), (0, pad_width)), mode='constant', constant_values=255)
        
        processed_images.append(img)
        
        # Add a white separator bar
        separator_shape = (padding, max_width, 3) if len(img.shape)==3 else (padding, max_width)
        separator = np.full(separator_shape, 255, dtype=np.uint8)
        processed_images.append(separator)
        
    # Remove the last separator
    if len(processed_images) > 1:
        processed_images.pop()
        
    # Stack vertically
    return np.vstack(processed_images)

class BOMExtractionSignature(dspy.Signature):
    """
    Extracts all components, part numbers, and quantities from a technical drawing.
    Outputs the result as a structured Bill of Materials (BOM).
    """
    
    # Input: We'll pass the drawing (as an image) to this field.
    drawing = dspy.InputField(desc="The customer's technical drawing ('Zeichnung').")
    
    # Output: We tell DSPy the output *must* follow the BillOfMaterials Pydantic model.
    bom: BillOfMaterials = dspy.OutputField()
# bom_extractor.py (continued...)

# 3. Define the DSPy Module (the agent)
class BOMExtractor(dspy.Module):
    def __init__(self):
        super().__init__()
        # We use ChainOfThought to force the LM to "think" before answering,
        # which improves accuracy for complex tasks like this.
        self.extractor = dspy.Predict(BOMExtractionSignature)

    def forward(self, filename: str):
        # 1. Fetch
        local_path = fetch_file_via_ssh(filename)
        
        # 2. Convert PDF
        if local_path.lower().endswith(".pdf"):
            print("--- 📄 Converting PDF (150 DPI)... ---")
            try:
                images = convert_from_path(local_path, dpi=150)
                if images:
                    png_path = local_path.replace(".pdf", ".png")
                    images[0].save(png_path, "PNG")
                    local_path = png_path 
            except Exception: pass

        # 2.5 Rotation Check
        try:
            img_check = cv2.imread(local_path)
            if img_check is not None:
                h, w = img_check.shape[:2]
                if h > w:
                    print(f"🔄 Detected Vertical Image ({w}x{h}). Rotating 90° Right...")
                    img_rotated = cv2.rotate(img_check, cv2.ROTATE_90_CLOCKWISE)
                    cv2.imwrite(local_path, img_rotated)
        except Exception: pass

        # 3. HARVEST (Get Numpy Arrays)
        raw_tables = extract_bom_tight_crop(local_path)
        if not raw_tables:
            print("❌ No BOM tables found.")
            return BillOfMaterials(items=[])

        # 4. FILTER (Remove unsafe keywords)
        safe_tables = filter_unsafe_tables(raw_tables, bad_words)
        if not safe_tables:
            print("❌ All tables were filtered out.")
            return BillOfMaterials(items=[])

        # =========================================================
        # 5. MERGE & SAVE TO DISK
        # =========================================================
        print(f"\n--- 🧩 Merging {len(safe_tables)} tables into one image ---")
        
        merged_image = merge_images_vertically(safe_tables)
        
        if merged_image is None:
            print("❌ Error: Merged image was empty.")
            return BillOfMaterials(items=[])

        # Generate a temporary path for the merged file
        # We use the original filename base so we know where it came from
        base_name = os.path.splitext(os.path.basename(local_path))[0]
        merged_file_path = f"/tmp/{base_name}_MERGED_BOM.png"
        
        print(f"--- 💾 Saving merged table to: {merged_file_path} ---")
        cv2.imwrite(merged_file_path, merged_image)

        # =========================================================
        # 6. GEMINI EXTRACTION (Using File Path)
        # =========================================================
        print(f"--- 🤖 Sending file path to Gemini ---")
        
        try:
            # Create DSPy Image Object using the LOCAL PATH
            # This is cleaner and avoids large Base64 strings in memory
            dspy_image = dspy.Image(url=merged_file_path)

            # Predict
            prediction = self.extractor(drawing=dspy_image)
            
            # Get Results
            extracted_items = prediction.bom.items
            print(f"       -> Gemini returned {len(extracted_items)} items.")
            
            return prediction.bom

        except Exception as e:
            print(f"   ⚠️ Gemini Failed: {e}")
            return BillOfMaterials(items=[])

_extractor_instance = BOMExtractor()

class RetrieveBOM(dspy.Module):
    """
    A tool to extract the Bill of Materials (BOM) from a technical drawing.
    Input must be the filename of the drawing (e.g., "123-456.pdf").
    Returns a string representation of the parts list.
    """
    name = "retrieve_bom"
    input_variable = "filename"
    desc = "Takes a filename of a technical drawing and returns the Bill of Materials (BOM) containing part numbers and quantities."

    def __call__(self, filename: str):
        print(f"\n[Tool] Agent requested BOM for: {filename}")
        try:
            # Call your existing forward method
            bom_result = _extractor_instance.forward(filename)
            
            # The Agent needs TEXT/STRING back, not a Pydantic object
            # We convert the BOM object to a clean string format
            return bom_result.model_dump_json()
            
        except Exception as e:
            return f"Error: Failed to extract BOM. Reason: {str(e)}"

# --- 4. Test Runner ---
def test_bom_extractor():
    
    # Configure Gemini
    lm = dspy.LM(model='gemini/gemini-2.5-flash', api_key=YOUR_API_KEY)
    dspy.settings.configure(lm=lm)
    print("--- 🛠️ STARTING DRY RUN ---")
    
    #TEST_FILENAME = "2000-103008-00.pdf" 
    TEST_FILENAME = "4000019-1210.00."
    
    agent = BOMExtractor()
    try:
        # Note: Ensure you have configured dspy with Gemini before running this!
        # dspy.configure(lm=dspy.Google("models/gemini-1.5-flash", api_key="..."))
        
        result = agent(filename=TEST_FILENAME)
        print("\n--- 5. EXTRACTION COMPLETE ---")
        print("Raw Output (Pydantic Model):")
        print(result)
        
        print("\nPretty JSON Output:")
        print(result.model_dump_json(indent=2))
        
    except Exception as e:
        print("\n--- EXTRACTION FAILED ---")
        print(f"An error occurred: {e}")
        print("\n--- DEBUG: Last LM Request/Response ---")
        lm.inspect_history(n=1)

if __name__ == "__main__":
    test_bom_extractor()