"""
test_pipeline.py - Verification script to test all components end-to-end
"""

import os
import cv2
import numpy as np
from PIL import Image

import excel_logger
import sample_generator
import vision_scanner
import voice_announcer

def run_tests():
    print("=== 1. Testing Sample Generation ===")
    sample_paths = sample_generator.generate_all_samples()
    print(f"Generated {len(sample_paths)} sample QRs: {sample_paths[:2]}")
    assert len(sample_paths) > 0, "No sample QRs generated!"

    print("\n=== 2. Testing Vision Scanner ===")
    scanner = vision_scanner.VisionScanner(debounce_seconds=1.0)
    test_img = cv2.imread(sample_paths[0])
    annotated, all_det, new_items = scanner.process_frame(test_img)
    print(f"Detected {len(all_det)} items. Extracted data: {all_det[0] if all_det else 'None'}")
    assert len(all_det) > 0, "Failed to detect QR in test image!"

    print("\n=== 3. Testing Real-Time Excel Logging ===")
    excel_logger.clear_ledger()
    log_rec = excel_logger.log_scan(all_det[0])
    print(f"Logged record: {log_rec}")
    df = excel_logger.get_dataframe()
    print(f"Excel Ledger currently has {len(df)} rows:\n{df[['Scan_ID', 'Product_Name', 'Price_USD']]}")
    assert len(df) == 1, "Excel logging failed!"

    print("\n=== 4. Testing Conveyor Frame Simulation ===")
    conveyor_img = sample_generator.generate_conveyor_mock_frame()
    conveyor_np = np.array(conveyor_img)
    conveyor_bgr = cv2.cvtColor(conveyor_np, cv2.COLOR_RGB2BGR)
    _, all_conv, new_conv = scanner.process_frame(conveyor_bgr, auto_debounce=False)
    print(f"Conveyor multi-item scan: detected {len(all_conv)} items on the belt.")
    excel_logger.log_batch(all_conv)
    stats = excel_logger.get_summary_stats()
    print(f"Summary Stats: {stats}")

    print("\n=== 5. Testing Multimodal NLP & Speech Engine (Lab 7) ===")
    announcement = voice_announcer.generate_scan_announcement(
        product_name="Sony Wireless Headphones",
        price=299.99,
        sku="SKU-ELE-901"
    )
    print(f"English Text: {announcement['text_en']}")
    print(f"Nepali Length: {len(announcement['text_ne'])} chars")
    print(f"Audio EN: {len(announcement['audio_en'])} bytes | Audio NE: {len(announcement['audio_ne'])} bytes")
    assert len(announcement['audio_en']) > 0, "English audio generation failed!"

    print("\n[SUCCESS] ALL PIPELINE TESTS PASSED!")

if __name__ == "__main__":
    run_tests()
