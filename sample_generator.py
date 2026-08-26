"""
sample_generator.py - Generates realistic Sample Product QR Codes and Conveyor Test Sheets
"""

import os
import json
import qrcode
from PIL import Image, ImageDraw, ImageFont

SAMPLE_DIR = "sample_qrs"

SAMPLE_PRODUCTS = [
    {
        "product_id": "SKU-ELE-901",
        "name": "Sony Wireless Headphones WH-1000",
        "category": "Electronics",
        "price": 299.99,
        "batch": "BATCH-2026-A1",
        "status": "QC Passed"
    },
    {
        "product_id": "SKU-ELE-902",
        "name": "Apple 20W USB-C Power Adapter",
        "category": "Electronics",
        "price": 19.00,
        "batch": "BATCH-2026-A1",
        "status": "QC Passed"
    },
    {
        "product_id": "SKU-GRO-304",
        "name": "Himalayan Organic Arabica Coffee 500g",
        "category": "Groceries",
        "price": 14.50,
        "batch": "BATCH-2026-B3",
        "status": "QC Passed"
    },
    {
        "product_id": "SKU-GRO-305",
        "name": "Extra Virgin Olive Oil 1L",
        "category": "Groceries",
        "price": 22.00,
        "batch": "BATCH-2026-B3",
        "status": "QC Passed"
    },
    {
        "product_id": "SKU-APP-501",
        "name": "Nike Dri-FIT Sports T-Shirt (M)",
        "category": "Apparel",
        "price": 38.00,
        "batch": "BATCH-2026-C2",
        "status": "QC Passed"
    },
    {
        "product_id": "SKU-IND-701",
        "name": "Heavy Duty Industrial Ball Valve 2-Inch",
        "category": "Industrial",
        "price": 85.50,
        "batch": "BATCH-2026-D4",
        "status": "QC Passed"
    },
    {
        "product_id": "SKU-MED-101",
        "name": "First Aid Surgical Bandages (Pack of 50)",
        "category": "Healthcare",
        "price": 12.75,
        "batch": "BATCH-2026-H1",
        "status": "QC Passed"
    }
]

def generate_qr_image(product_data: dict, save_path: str = None) -> Image.Image:
    """Creates a stylized QR code image containing JSON product data with a clean label."""
    json_payload = json.dumps(product_data)
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(json_payload)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#1E293B", back_color="white").convert("RGB")
    
    # Create an attached label card underneath
    width, height = qr_img.size
    card_height = height + 70
    card = Image.new("RGB", (width, card_height), "#F8FAFC")
    card.paste(qr_img, (0, 0))
    
    draw = ImageDraw.Draw(card)
    # Add text label
    text_sku = f"{product_data['product_id']}"
    text_name = f"{product_data['name'][:22]}"
    text_price = f"${product_data['price']:.2f} | {product_data['category']}"
    
    draw.text((10, height + 6), text_sku, fill="#0F172A")
    draw.text((10, height + 24), text_name, fill="#334155")
    draw.text((10, height + 44), text_price, fill="#0284C7")
    
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        card.save(save_path)
        
    return card

def generate_all_samples(output_dir: str = SAMPLE_DIR) -> list[str]:
    """Generates all preset sample QR codes and saves them to the sample directory."""
    os.makedirs(output_dir, exist_ok=True)
    paths = []
    for product in SAMPLE_PRODUCTS:
        filename = f"{product['product_id']}.png"
        filepath = os.path.join(output_dir, filename)
        generate_qr_image(product, filepath)
        paths.append(filepath)
    return paths

def generate_conveyor_mock_frame(products: list[dict] = None) -> Image.Image:
    """Creates a simulated multi-product conveyor belt image with multiple QR codes."""
    if products is None:
        products = SAMPLE_PRODUCTS[:3]
        
    belt_width = 800
    belt_height = 360
    
    # Dark conveyor belt background with steel rollers
    frame = Image.new("RGB", (belt_width, belt_height), "#334155")
    draw = ImageDraw.Draw(frame)
    
    # Conveyor belt track markings
    for y in range(0, belt_height, 40):
        draw.line([(0, y), (belt_width, y)], fill="#1E293B", width=2)
        
    # Yellow hazard safety lines on edges
    draw.rectangle([0, 0, belt_width, 18], fill="#EAB308")
    draw.rectangle([0, belt_height - 18, belt_width, belt_height], fill="#EAB308")
    draw.text((20, 3), "▲ CONVEYOR LINE 01 - AUTOMATED SCANNING ZONE ▲", fill="#000000")
    
    # Place products on the belt
    offset_x = 40
    for prod in products:
        qr_img = generate_qr_image(prod)
        qr_img = qr_img.resize((180, 230))
        # Draw cardboard box border
        box_x = offset_x
        box_y = 60
        draw.rectangle([box_x - 6, box_y - 6, box_x + 186, box_y + 236], fill="#D97706", outline="#78350F", width=2)
        frame.paste(qr_img, (box_x, box_y))
        offset_x += 250
        
    return frame

if __name__ == "__main__":
    generated = generate_all_samples()
    print(f"Generated {len(generated)} sample QR codes in '{SAMPLE_DIR}/'")
