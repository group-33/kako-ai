import os
import cv2
import dspy
from backend.src.models import BillOfMaterials # Pfad ggf. anpassen
from .image_processing import extract_bom_tight_crop, filter_unsafe_tables, merge_images_vertically
from .file_utils import fetch_file_via_ssh, convert_pdf_to_png

class BOMExtractionSignature(dspy.Signature):
    """
    Extracts all components, part numbers, and quantities from a technical drawing.
    Outputs the result as a structured Bill of Materials (BOM).
    """
    drawing = dspy.InputField(desc="The customer's technical drawing ('Zeichnung').")
    bom: BillOfMaterials = dspy.OutputField()

class BOMExtractorModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.extractor = dspy.Predict(BOMExtractionSignature)

    def forward(self, filename: str):
        # 1. Fetch & Convert
        local_path = fetch_file_via_ssh(filename)
        local_path = convert_pdf_to_png(local_path)

        # 2. Rotation Check
        img_check = cv2.imread(local_path)
        if img_check is not None:
            h, w = img_check.shape[:2]
            if h > w:
                print(f"🔄 Detected Vertical Image ({w}x{h}). Rotating 90° Right...")
                cv2.imwrite(local_path, cv2.rotate(img_check, cv2.ROTATE_90_CLOCKWISE))

        # 3. Harvest Tables
        raw_tables = extract_bom_tight_crop(local_path)
        safe_tables = filter_unsafe_tables(raw_tables) # Filter unsafe keywords

        if not safe_tables:
            print("❌ No valid BOM tables found.")
            return BillOfMaterials(items=[])

        # 4. Merge
        merged_image = merge_images_vertically(safe_tables)
        if merged_image is None: return BillOfMaterials(items=[])

        base_name = os.path.splitext(os.path.basename(local_path))[0]
        merged_file_path = f"/tmp/{base_name}_MERGED_BOM.png"
        cv2.imwrite(merged_file_path, merged_image)

        # 5. Gemini Extraction
        print(f"--- 🤖 Sending file path to Gemini: {merged_file_path} ---")
        try:
            dspy_image = dspy.Image(url=merged_file_path)
            prediction = self.extractor(drawing=dspy_image)
            return prediction.bom
        except Exception as e:
            print(f"   ⚠️ Gemini Failed: {e}")
            return BillOfMaterials(items=[])