"""
excel_logger.py - Real-Time Excel Database Manager for AutoScan AI
Maintains real-time logs of scanned items into an Excel ledger (.xlsx)
"""

import os
from datetime import datetime
from io import BytesIO
import pandas as pd
import openpyxl

LEDGER_FILE = "inventory_ledger.xlsx"
COLUMNS = [
    "Scan_ID",
    "Timestamp",
    "Product_ID",
    "Product_Name",
    "Category",
    "Price_USD",
    "Batch_Number",
    "Station_Line",
    "Status"
]

def init_ledger(file_path: str = LEDGER_FILE) -> str:
    """Initializes the Excel ledger file with default columns if it doesn't exist."""
    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=COLUMNS)
        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Inventory_Log")
    return file_path

def log_scan(product_info: dict, file_path: str = LEDGER_FILE) -> dict:
    """
    Logs a single scanned product into the Excel ledger.
    Returns the formatted record dict with assigned Scan_ID and Timestamp.
    """
    init_ledger(file_path)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    scan_id = f"SCN-{datetime.now().strftime('%y%m%d%H%M%S%f')[:15]}"
    
    new_record = {
        "Scan_ID": scan_id,
        "Timestamp": timestamp,
        "Product_ID": str(product_info.get("product_id", product_info.get("sku", "UNKNOWN"))),
        "Product_Name": str(product_info.get("name", "Unknown Item")),
        "Category": str(product_info.get("category", "General")),
        "Price_USD": float(product_info.get("price", 0.0)),
        "Batch_Number": str(product_info.get("batch", "B-001")),
        "Station_Line": str(product_info.get("station", "Conveyor-1")),
        "Status": str(product_info.get("status", "QC Passed"))
    }
    
    # Load existing ledger and append row
    try:
        df = pd.read_excel(file_path, engine="openpyxl")
        df_new = pd.DataFrame([new_record])
        if df.empty or df.dropna(how="all").empty:
            df_updated = df_new
        else:
            df_updated = pd.concat([df, df_new], ignore_index=True)
        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            df_updated.to_excel(writer, index=False, sheet_name="Inventory_Log")
    except Exception as e:
        df_new = pd.DataFrame([new_record])
        df_new.to_excel(file_path, index=False, engine="openpyxl")
        
    return new_record

def log_batch(products_list: list[dict], file_path: str = LEDGER_FILE) -> list[dict]:
    """Logs a batch of multiple scanned products into the Excel ledger."""
    init_ledger(file_path)
    if not products_list:
        return []
    
    records = []
    base_time = datetime.now()
    for idx, p in enumerate(products_list):
        timestamp = base_time.strftime("%Y-%m-%d %H:%M:%S")
        scan_id = f"SCN-{base_time.strftime('%y%m%d%H%M%S')}-{idx+1:03d}"
        rec = {
            "Scan_ID": scan_id,
            "Timestamp": timestamp,
            "Product_ID": str(p.get("product_id", p.get("sku", "UNKNOWN"))),
            "Product_Name": str(p.get("name", "Unknown Item")),
            "Category": str(p.get("category", "General")),
            "Price_USD": float(p.get("price", 0.0)),
            "Batch_Number": str(p.get("batch", "B-001")),
            "Station_Line": str(p.get("station", "Conveyor-1")),
            "Status": str(p.get("status", "QC Passed"))
        }
        records.append(rec)
        
    df = get_dataframe(file_path)
    df_new = pd.DataFrame(records)
    if df.empty or df.dropna(how="all").empty:
        df_updated = df_new
    else:
        df_updated = pd.concat([df, df_new], ignore_index=True)
    
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        df_updated.to_excel(writer, index=False, sheet_name="Inventory_Log")
        
    return records

def get_dataframe(file_path: str = LEDGER_FILE) -> pd.DataFrame:
    """Reads the current Excel ledger into a pandas DataFrame with strictly typed columns."""
    init_ledger(file_path)
    try:
        df = pd.read_excel(file_path, engine="openpyxl")
        if df.empty:
            return pd.DataFrame(columns=COLUMNS)
        
        # Ensure consistent string types to prevent PyArrow serialization errors
        str_cols = ["Scan_ID", "Timestamp", "Product_ID", "Product_Name", "Category", "Batch_Number", "Station_Line", "Status"]
        for col in str_cols:
            if col in df.columns:
                df[col] = df[col].astype(str)
                
        if "Price_USD" in df.columns:
            df["Price_USD"] = pd.to_numeric(df["Price_USD"], errors="coerce").fillna(0.0)
            
        return df
    except Exception:
        return pd.DataFrame(columns=COLUMNS)

def get_summary_stats(file_path: str = LEDGER_FILE) -> dict:
    """Computes summary statistics from the Excel ledger."""
    df = get_dataframe(file_path)
    if df.empty:
        return {
            "total_scanned": 0,
            "total_value": 0.0,
            "unique_skus": 0,
            "qc_passed": 0,
            "categories": {}
        }
    
    total_scanned = len(df)
    total_value = float(df["Price_USD"].sum()) if "Price_USD" in df.columns else 0.0
    unique_skus = int(df["Product_ID"].nunique()) if "Product_ID" in df.columns else 0
    qc_passed = int((df["Status"] == "QC Passed").sum()) if "Status" in df.columns else total_scanned
    cat_counts = df["Category"].value_counts().to_dict() if "Category" in df.columns else {}
    
    return {
        "total_scanned": total_scanned,
        "total_value": round(total_value, 2),
        "unique_skus": unique_skus,
        "qc_passed": qc_passed,
        "categories": cat_counts
    }

def get_excel_bytes(file_path: str = LEDGER_FILE) -> bytes:
    """Returns Excel file as raw bytes for direct browser download."""
    df = get_dataframe(file_path)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Inventory_Log")
    return output.getvalue()

def clear_ledger(file_path: str = LEDGER_FILE) -> None:
    """Resets the Excel ledger file."""
    df = pd.DataFrame(columns=COLUMNS)
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Inventory_Log")
