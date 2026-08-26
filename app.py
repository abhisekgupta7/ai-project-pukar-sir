"""
app.py - AutoScan AI: Simple Automated Camera to Excel Scanner
Lab 7 AI Project: Real-Time Computer Vision + Live Excel Spreadsheet + Spoken Bilingual Voice
"""

import time
import threading
import cv2
import numpy as np
import pandas as pd
from PIL import Image
import streamlit as st

import excel_logger
import vision_scanner
import voice_announcer

# --- Page Setup ---
st.set_page_config(
    page_title="AutoScan AI",
    page_icon="📷",
    layout="wide"
)

st.markdown("""
<style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    .alert-box {
        background-color: #064E3B;
        color: #D1FAE5;
        border: 1px solid #059669;
        border-radius: 8px;
        padding: 10px 14px;
        margin-top: 8px;
        margin-bottom: 10px;
        font-weight: 600;
    }
    .stDownloadButton>button {
        background-color: #0284C7 !important;
        color: white !important;
        font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize
excel_logger.init_ledger()

if "scanner" not in st.session_state:
    st.session_state.scanner = vision_scanner.VisionScanner(debounce_seconds=2.5)
if "last_scanned" not in st.session_state:
    st.session_state.last_scanned = None
if "last_audio" not in st.session_state:
    st.session_state.last_audio = None
if "camera_on" not in st.session_state:
    st.session_state.camera_on = False

# Voice announcement in background
def trigger_voice_async(name: str, price: float, sku: str):
    def _worker():
        try:
            aud = voice_announcer.generate_scan_announcement(name, price, sku)
            st.session_state.last_audio = aud
        except Exception:
            pass
    threading.Thread(target=_worker, daemon=True).start()

# --- Title ---
st.title("📷 AutoScan AI")
st.markdown("Camera detects product barcodes & QR codes, **logs them into Excel in real time**, and plays **Nepali & English voice confirmations**.")
st.markdown("---")

col_left, col_right = st.columns([1, 1], gap="large")

# ==============================================================================
# RIGHT COLUMN (EXCEL SPREADSHEET & DOWNLOAD)
# ==============================================================================
with col_right:
    st.markdown("### 📋 Excel Spreadsheet (`inventory_ledger.xlsx`)")
    
    excel_bytes = excel_logger.get_excel_bytes()
    
    btn_dl, btn_clr = st.columns([3, 1])
    with btn_dl:
        st.download_button(
            label="📥 Download Excel (.xlsx)",
            data=excel_bytes,
            file_name="inventory_ledger.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    with btn_clr:
        if st.button("🧹 Clear Table", use_container_width=True):
            excel_logger.clear_ledger()
            st.session_state.last_scanned = None
            st.session_state.last_audio = None
            st.session_state.scanner.reset_cache()
            st.rerun()

    count_slot = st.empty()
    table_slot = st.empty()

    def update_excel_view():
        df = excel_logger.get_dataframe()
        count_slot.markdown(f"**Total Scanned:** `{len(df)} items`")
        if not df.empty:
            show_cols = ["Timestamp", "Product_ID", "Product_Name", "Category", "Price_USD", "Status"]
            existing = [c for c in show_cols if c in df.columns]
            table_slot.dataframe(
                df[existing],
                use_container_width=True,
                height=430,
                column_config={
                    "Price_USD": st.column_config.NumberColumn("Price ($)", format="$%.2f"),
                    "Product_ID": st.column_config.TextColumn("SKU / Barcode"),
                    "Product_Name": st.column_config.TextColumn("Product Name"),
                    "Timestamp": st.column_config.TextColumn("Time"),
                }
            )
        else:
            table_slot.info("The Excel file is empty. Scan a product on the left to see it added here!")

    update_excel_view()

# ==============================================================================
# LEFT COLUMN (ONLY 2 OPTIONS: LIVE CAMERA OR IMAGE UPLOAD)
# ==============================================================================
with col_left:
    st.markdown("### 🔍 Scan Product")
    
    scan_option = st.radio(
        "Select Scanning Mode:",
        ["📹 Live Camera", "📁 Upload Image"],
        horizontal=True
    )
    
    # -------------------------------------------------------------------------
    # OPTION 1: LIVE CAMERA
    # -------------------------------------------------------------------------
    if scan_option == "📹 Live Camera":
        c1, c2 = st.columns(2)
        if c1.button("▶️ Start Camera", type="primary", use_container_width=True):
            st.session_state.camera_on = True
        if c2.button("⏹️ Stop Camera", use_container_width=True):
            st.session_state.camera_on = False
            
        cam_view = st.empty()
        status_box = st.empty()
        
        if st.session_state.camera_on:
            status_box.success("🎥 **Camera Running!** Pass any product/barcode in front of the camera...")
            try:
                cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                if not cap.isOpened():
                    cap = cv2.VideoCapture(0)
            except Exception:
                cap = cv2.VideoCapture(0)
                
            if not cap or not cap.isOpened():
                status_box.error("❌ Could not connect to camera. Please make sure no other app is using it.")
                st.session_state.camera_on = False
            else:
                try:
                    # Safely attempt resolution set
                    try:
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    except Exception:
                        pass
                    
                    while st.session_state.camera_on:
                        ret, frame = cap.read()
                        if not ret or frame is None:
                            time.sleep(0.05)
                            continue
                            
                        # Scan frame
                        annotated, all_det, new_items = st.session_state.scanner.process_frame(frame, auto_debounce=True)
                        
                        # Render camera view
                        disp = cv2.resize(annotated, (480, 270))
                        cam_view.image(cv2.cvtColor(disp, cv2.COLOR_BGR2RGB), channels="RGB", use_container_width=True)
                        
                        # When product detected
                        if new_items:
                            for item in new_items:
                                rec = excel_logger.log_scan(item)
                                st.session_state.last_scanned = rec
                                update_excel_view()
                                trigger_voice_async(rec["Product_Name"], rec["Price_USD"], rec["Product_ID"])
                                
                            status_box.markdown(f"""
                            <div class="alert-box">
                                ✅ <b>SCANNED & LOGGED:</b> {st.session_state.last_scanned['Product_Name']} (${st.session_state.last_scanned['Price_USD']:.2f})<br>
                                <small>SKU: <code>{st.session_state.last_scanned['Product_ID']}</code></small>
                            </div>
                            """, unsafe_allow_html=True)
                            
                        time.sleep(0.01)
                finally:
                    cap.release()

    # -------------------------------------------------------------------------
    # OPTION 2: IMAGE UPLOAD
    # -------------------------------------------------------------------------
    else:
        uploaded_file = st.file_uploader("Upload product photo or barcode image:", type=["png", "jpg", "jpeg", "webp"])
        if uploaded_file is not None:
            pil_img = Image.open(uploaded_file).convert("RGB")
            frame_np = np.array(pil_img)
            frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)
            
            annotated_bgr, all_det, _ = st.session_state.scanner.process_frame(frame_bgr, auto_debounce=False)
            st.image(cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB), caption="Scanned Image", use_container_width=True)
            
            if all_det:
                for item in all_det:
                    rec = excel_logger.log_scan(item)
                    st.session_state.last_scanned = rec
                    st.session_state.last_audio = voice_announcer.generate_scan_announcement(
                        product_name=rec["Product_Name"],
                        price=rec["Price_USD"],
                        sku=rec["Product_ID"]
                    )
                update_excel_view()
                st.success(f"✅ Decoded {len(all_det)} item(s) and logged to Excel!")
            else:
                st.warning("⚠️ No barcode or QR code detected in this photo.")

    # Spoken Audio Confirmation (Lab 7)
    if st.session_state.last_scanned:
        sc = st.session_state.last_scanned
        st.markdown(f"""
        <div class="alert-box">
            ✅ <b>LOGGED TO EXCEL:</b> {sc['Product_Name']} (${sc['Price_USD']:.2f})<br>
            <small><b>SKU:</b> {sc['Product_ID']} | <b>Time:</b> {sc['Timestamp']}</small>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.last_audio:
            aud = st.session_state.last_audio
            st.markdown("##### 🔊 Spoken Audio Confirmation (Lab 7):")
            st.caption(f"🇳🇵 **Nepali Voice:** *{aud['text_ne']}*")
            st.audio(aud['audio_ne'], format="audio/mp3")
            st.caption(f"🇬🇧 **English Voice:** *{aud['text_en']}*")
            st.audio(aud['audio_en'], format="audio/mp3")

st.markdown("---")
st.caption("AutoScan AI • Lab 7 AI Capstone Project • Automated Vision & Barcode Scanning to Excel")
