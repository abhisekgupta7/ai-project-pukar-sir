"""
vision_scanner.py - Industrial-Grade Anti-Glare & Super-Sharp Barcode/QR Vision Scanner
Optimized for laptop webcams: Anti-glare filter, plastic reflection suppression, sharpening, and multi-scale detection.
"""

import time
import json
import re
import cv2
import numpy as np

try:
    from pyzbar.pyzbar import decode as pyzbar_decode
    PYZBAR_AVAILABLE = True
except Exception:
    PYZBAR_AVAILABLE = False

class VisionScanner:
    def __init__(self, debounce_seconds: float = 2.5):
        self.opencv_detector = cv2.QRCodeDetector()
        self.debounce_seconds = debounce_seconds
        self.seen_cache = {}

    def parse_payload(self, raw_text: str, code_type: str = "BARCODE") -> dict:
        """Extracts clean metadata from raw barcode/QR payload."""
        if not raw_text or not raw_text.strip():
            return {}
        
        raw_text = raw_text.strip()
        
        # 1. JSON payload
        try:
            parsed = json.loads(raw_text)
            if isinstance(parsed, dict):
                return {
                    "product_id": str(parsed.get("product_id", parsed.get("sku", parsed.get("id", "SKU-PROD-01")))),
                    "name": str(parsed.get("name", parsed.get("title", "Scanned Product"))),
                    "category": str(parsed.get("category", "General")),
                    "price": float(parsed.get("price", parsed.get("cost", 19.99))),
                    "batch": str(parsed.get("batch", "B-2026-X1")),
                    "status": "QC Passed"
                }
        except Exception:
            pass
        
        # 2. Key-Value text (SKU: 123, Name: Milk, Price: 3.5)
        if ":" in raw_text:
            items = {}
            for line in raw_text.split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    items[k.strip().lower()] = v.strip()
            if items:
                sku = items.get("sku", items.get("product_id", items.get("id", "SKU-TXT-01")))
                name = items.get("name", items.get("title", f"Product ({sku})"))
                cat = items.get("category", "Retail")
                raw_price = items.get("price", "25.0").replace("$", "").replace("Rs", "").strip()
                try:
                    price = float(raw_price)
                except Exception:
                    price = 25.0
                return {
                    "product_id": sku,
                    "name": name,
                    "category": cat,
                    "price": price,
                    "batch": items.get("batch", "B-2026-X1"),
                    "status": "QC Passed"
                }

        # 3. Standard Retail Barcode (EAN-13, UPC, Code 128)
        clean_id = re.sub(r'[^A-Za-z0-9-_.]', '', raw_text)[:20]
        if not clean_id:
            clean_id = f"BAR-{hash(raw_text)%1000000:06d}"
            
        item_title = f"Retail Item #{clean_id[-6:]}" if len(clean_id) >= 6 else f"Product {clean_id}"
        
        return {
            "product_id": clean_id,
            "name": item_title,
            "category": "Retail Merchandise",
            "price": 28.50,
            "batch": "LOT-2026-B",
            "status": "QC Passed"
        }

    def _generate_enhanced_variants(self, gray: np.ndarray) -> list[np.ndarray]:
        """
        Creates specialized optical filters to overcome plastic glare, low webcam resolution, and motion blur.
        """
        variants = [gray]
        
        # Filter 1: CLAHE Contrast Stretch (penetrates dark/indoor lighting)
        clahe = cv2.createCLAHE(clipLimit=3.5, tileGridSize=(8, 8)).apply(gray)
        variants.append(clahe)
        
        # Filter 2: Anti-Glare Morphological Black-Hat Filter (removes shiny plastic reflections)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
        blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)
        blackhat_sharp = cv2.normalize(blackhat, None, 0, 255, cv2.NORM_MINMAX)
        variants.append(blackhat_sharp)
        
        # Filter 3: Unsharp Masking (USM) - sharpens barcode lines so user doesn't need to bring box too close
        gaussian = cv2.GaussianBlur(clahe, (0, 0), 2.0)
        unsharp = cv2.addWeighted(clahe, 1.8, gaussian, -0.8, 0)
        variants.append(unsharp)
        
        # Filter 4: Adaptive Otsu Binarization
        _, otsu = cv2.threshold(clahe, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        variants.append(otsu)
        
        return variants

    def process_frame(self, frame: np.ndarray, auto_debounce: bool = True) -> tuple[np.ndarray, list[dict], list[dict]]:
        """
        Processes frame with industrial anti-glare filters & multi-orientation barcode recovery.
        """
        annotated = frame.copy()
        all_detected = []
        new_items = []
        current_time = time.time()
        detected_payloads = set()

        if PYZBAR_AVAILABLE:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
            enhanced_passes = self._generate_enhanced_variants(gray)
            
            for p_img in enhanced_passes:
                barcodes = pyzbar_decode(p_img)
                
                # If not found horizontally, test vertical rotation (for tilted/held boxes)
                if not barcodes:
                    rot = cv2.rotate(p_img, cv2.ROTATE_90_CLOCKWISE)
                    rot_barcodes = pyzbar_decode(rot)
                    if rot_barcodes:
                        barcodes = rot_barcodes
                
                if barcodes:
                    for barcode in barcodes:
                        try:
                            raw_data = barcode.data.decode("utf-8")
                        except Exception:
                            raw_data = str(barcode.data)
                            
                        if not raw_data or raw_data in detected_payloads:
                            continue
                        
                        detected_payloads.add(raw_data)
                        code_type = str(barcode.type)
                        parsed = self.parse_payload(raw_data, code_type)
                        all_detected.append(parsed)
                        
                        # Debounce
                        sku = parsed["product_id"]
                        last_t = self.seen_cache.get(sku, 0.0)
                        if not auto_debounce or (current_time - last_t > self.debounce_seconds):
                            self.seen_cache[sku] = current_time
                            new_items.append(parsed)
                            
                        # Draw bounding box & label
                        (x, y, bw, bh) = barcode.rect
                        cv2.rectangle(annotated, (x, y), (x + bw, y + bh), (0, 255, 0), 3)
                        
                        label = f"{parsed['name']} | ${parsed['price']:.2f}"
                        cv2.rectangle(annotated, (x, max(0, y - 28)), (x + len(label) * 11, y), (15, 23, 42), -1)
                        cv2.rectangle(annotated, (x, max(0, y - 28)), (x + len(label) * 11, y), (0, 255, 0), 1)
                        cv2.putText(annotated, label, (x + 5, max(18, y - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)
                    
                    if all_detected:
                        break

        # Fallback to OpenCV QR detector
        if not all_detected:
            retval, decoded_info, points, _ = self.opencv_detector.detectAndDecodeMulti(frame)
            if retval and points is not None:
                for text, pts in zip(decoded_info, points):
                    if not text or text in detected_payloads:
                        continue
                    detected_payloads.add(text)
                    parsed = self.parse_payload(text, "QR_CODE")
                    all_detected.append(parsed)
                    
                    sku = parsed["product_id"]
                    last_t = self.seen_cache.get(sku, 0.0)
                    if not auto_debounce or (current_time - last_t > self.debounce_seconds):
                        self.seen_cache[sku] = current_time
                        new_items.append(parsed)
                        
                    pts_int = pts.astype(int)
                    cv2.polylines(annotated, [pts_int], isClosed=True, color=(0, 255, 0), thickness=3)
                    x, y = pts_int[0][0], pts_int[0][1]
                    label = f"{parsed['name']} | ${parsed['price']:.2f}"
                    cv2.rectangle(annotated, (x, max(0, y - 28)), (x + len(label) * 11, y), (15, 23, 42), -1)
                    cv2.putText(annotated, label, (x + 5, max(18, y - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

        return annotated, all_detected, new_items

    def reset_cache(self):
        self.seen_cache.clear()
