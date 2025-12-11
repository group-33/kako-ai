import cv2
import numpy as np
import pytesseract
import base64
from pytesseract import Output

# Konstanten
BAD_WORDS = [
    "gmbh", "hirt", "heidelberg",
    "vertraulich", "confidential", "version", "drawn", "date"
]

def numpy_to_base64(img_array):
    """Converts an OpenCV image (numpy) to a Base64 string."""
    _, buffer = cv2.imencode('.png', img_array)
    return base64.b64encode(buffer).decode('utf-8')

def filter_unsafe_tables(table_images: list, unsafe_keywords: list = None) -> list:
    if not table_images:
        return []

    if unsafe_keywords is None:
        unsafe_keywords = BAD_WORDS
    
    unsafe_keywords = [k.lower() for k in unsafe_keywords]
    filtered_results = []
    
    print(f"--- 🔍 Filtering {len(table_images)} tables for unsafe data ---")

    for i, img in enumerate(table_images):
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
            
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        try:
            text = pytesseract.image_to_string(binary, config='--psm 6')
            text_lower = text.lower()
            
            found_unsafe = False
            for keyword in unsafe_keywords:
                if keyword in text_lower:
                    print(f"   ❌ Table {i} dropped! Found unsafe keyword: '{keyword}'")
                    found_unsafe = True
                    break
            
            if not found_unsafe:
                filtered_results.append(img)
                
        except Exception as e:
            print(f"   ⚠️ OCR Failed for Table {i}: {e}. Keeping it by default.")
            filtered_results.append(img)

    return filtered_results

def split_merged_crop(crop_img):
    if crop_img.size == 0: return []
    
    h, w = crop_img.shape[:2]
    gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY) if len(crop_img.shape) == 3 else crop_img
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

    line_scale = 15 
    hor_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (w // line_scale, 1))
    horizontal_structure = cv2.dilate(cv2.erode(binary, hor_kernel, iterations=1), hor_kernel, iterations=2)

    roi_top_cut = int(h * 0.15)    
    roi_bottom_cut = int(h * 0.65)
    
    if roi_bottom_cut <= roi_top_cut:
        roi_top_cut = 0
        roi_bottom_cut = h

    roi_structure = horizontal_structure[roi_top_cut:roi_bottom_cut, :]
    structure_projection = np.sum(roi_structure, axis=0)

    sensitivity = 0.02 
    break_threshold = (roi_bottom_cut - roi_top_cut) * sensitivity * 255 
    gap_indices = np.where(structure_projection <= break_threshold)[0]

    if len(gap_indices) == 0:
        return [crop_img]

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
        gap_center = gap[0] + len(gap) // 2
        if len(gap) >= min_gap_width and margin_safety < gap_center < (w - margin_safety):
            valid_splits.append(gap_center)

    if valid_splits:
        valid_splits.sort(key=lambda x: abs(x - w//2))
        return [crop_img[:, :valid_splits[0]], crop_img[:, valid_splits[0]:]]
    
    return [crop_img]

def extract_bom_tight_crop(image_path, output_dir="/tmp"):
    import os
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    filename_base = os.path.splitext(os.path.basename(image_path))[0]

    original_img = cv2.imread(image_path)
    if original_img is None: return []
    
    img_h, img_w = original_img.shape[:2]
    gray = cv2.cvtColor(original_img, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    
    scale = 50 
    kernel_len = img_w // scale
    ver_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_len))
    hor_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_len, 1))
    
    vert_lines = cv2.dilate(cv2.erode(binary, ver_kernel, iterations=3), ver_kernel, iterations=3)
    hor_lines = cv2.dilate(cv2.erode(binary, hor_kernel, iterations=3), hor_kernel, iterations=3)
    
    joints = cv2.bitwise_and(cv2.dilate(vert_lines, np.ones((3,3)), iterations=1), 
                             cv2.dilate(hor_lines, np.ones((3,3)), iterations=1))
    
    gap_w, gap_h = img_w // 5, img_h // 20
    mask_woven = cv2.dilate(cv2.dilate(joints, np.ones((1, gap_w)), iterations=1), np.ones((gap_h, 1)), iterations=1)

    contours, _ = cv2.findContours(mask_woven, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    table_crops = []
    min_area = (img_w * img_h) * 0.05 

    for i, c in enumerate(contours):
        bx, by, bw, bh = cv2.boundingRect(c)
        if (bw * bh) < min_area or (bw > 0.9 * img_w and bh > 0.9 * img_h): continue

        joints_roi = joints[by:by+bh, bx:bx+bw]
        points = cv2.findNonZero(joints_roi)

        if points is not None:
            min_x, max_x = np.min(points[:, 0, 0]), np.max(points[:, 0, 0])
            min_y, max_y = np.min(points[:, 0, 1]), np.max(points[:, 0, 1])

            x1, y1 = max(0, bx + min_x - 5), max(0, by + min_y - 5)
            x2, y2 = min(img_w, bx + max_x + 5), min(img_h, by + max_y + 5)

            sub_crops = split_merged_crop(original_img[y1:y2, x1:x2])
            for part_idx, final_crop in enumerate(sub_crops):
                out_path = f"{output_dir}/{filename_base}_crop_{i}_p{part_idx}.png"
                cv2.imwrite(out_path, final_crop)
                table_crops.append(final_crop)

    return table_crops

def merge_images_vertically(image_list, padding=20):
    if not image_list: return None
    max_width = max(img.shape[1] for img in image_list)
    processed = []
    
    for img in image_list:
        h, w = img.shape[:2]
        if w < max_width:
            pad = ((0,0), (0, max_width - w)) if len(img.shape) == 2 else ((0,0), (0, max_width - w), (0,0))
            img = np.pad(img, pad, mode='constant', constant_values=255)
        processed.append(img)
        processed.append(np.full((padding, max_width, 3) if len(img.shape)==3 else (padding, max_width), 255, dtype=np.uint8))
        
    return np.vstack(processed[:-1]) if processed else None