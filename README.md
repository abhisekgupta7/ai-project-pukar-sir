# 🏭 AutoScan AI: Automated Vision to Excel 
> **Artificial Intelligence Lab 7 Capstone Project**  
> *Purwanchal Campus, Institute of Engineering (IOE)*

AutoScan AI is a lightweight, end-to-end multimodal AI application engineered to automate manual barcode & QR scanning across **Manufacturing Production Lines (Conveyor Belts)** and **Shopping Mall Retail Checkouts**.

It uses real-time computer vision to detect, decode, and log products directly into an **Excel workbook (`inventory_ledger.xlsx`)**, while simultaneously providing **Bilingual Text-to-Speech audio confirmations (English & Nepali)**.

---

## 🎯 Lab 7 Multimodal AI Compliance

| Requirement | Implementation in AutoScan AI |
|:---|:---|
| **Capability 1 (Computer Vision)** | Real-time QR/Barcode localization, multi-detection per frame, debounce/deduplication filter, bounding box tracking via OpenCV. |
| **Capability 2 (NLP & Machine Translation)** | Automated natural language scan event reports & executive shift summaries translated to Nepali via `deep-translator`. |
| **Capability 3 (Audio / Speech Synthesis)** | Real-time in-memory Text-to-Speech (TTS) via `gTTS` in both English and Nepali. |
| **Data Persistence** | Continuous streaming & batch logging into `inventory_ledger.xlsx` via `pandas` & `openpyxl`. |
| **Interactive UI** | Lightweight, responsive Streamlit dashboard. |

---

## 📂 Project Architecture

```
AbhiAiProject/
├── app.py                  # Main Streamlit web application
├── vision_scanner.py       # OpenCV vision processor & debounce tracker
├── excel_logger.py         # Real-time Excel (.xlsx) read/write/export engine
├── voice_announcer.py      # Lab 7 multimodal pipeline (NLP + Translation + gTTS)
├── sample_generator.py     # Preset & custom QR generator test kit
├── test_pipeline.py        # End-to-end automated verification script
├── sample_qrs/             # Directory containing generated sample product tags
├── inventory_ledger.xlsx   # Auto-created & updated Excel spreadsheet
└── requirements.txt        # Lightweight dependencies list
```

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Pipeline Test
```bash
python test_pipeline.py
```

### 3. Launch the Web Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🖥️ Application Features

1. **🎥 Live Conveyor & Camera Scanner:**
   - **Simulated Conveyor Belt:** Push virtual items onto the conveyor belt to test continuous automatic logging.
   - **Live Webcam / Camera:** Hold physical QR codes or phone screens in front of your camera.
   - **Upload Static Frame:** Analyze high-resolution conveyor camera snapshots.
   - **Real-Time Voice Playback:** Hear instant spoken confirmations in English and Nepali.

2. **📁 Multi-Item & Batch Image Processor:**
   - Upload 10+ package images simultaneously.
   - Auto-scans all items and logs them to Excel in a single batch with consolidated voice report.

3. **📊 Real-Time Excel Ledger & Analytics:**
   - Live editable table showing current `inventory_ledger.xlsx` contents.
   - Real-time KPIs: Scanned count, Total inventory valuation ($), Unique SKUs, QC pass rate.
   - Category & Station breakdown charts.
   - One-click **Download Excel (.xlsx)** button.

4. **🎙️ Voice Dispatch & Audio Shift Reports:**
   - One-click **Executive Spoken Summary** of current warehouse/mall inventory in English & Nepali.
   - Custom multilingual announcer to broadcast floor instructions.

5. **🏷️ QR Code Studio:**
   - Create custom tags with custom SKU, name, price, and category.
   - Download PNG or push directly to the live conveyor scanner.

---

## 💡 Technologies Used
- **Language:** Python 3.13
- **Computer Vision:** OpenCV (`cv2`)
- **Web UI:** Streamlit
- **Spreadsheet Engine:** Pandas & OpenPyXL
- **NLP / Translation:** Deep-Translator (Google Translator API)
- **Speech Synthesis:** gTTS (Google Text-to-Speech)
