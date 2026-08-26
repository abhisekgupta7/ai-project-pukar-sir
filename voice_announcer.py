"""
voice_announcer.py - Multimodal NLP & Speech Engine for AutoScan AI (Lab 7 Capstone)
Chains together:
1. Dynamic Speech/NLP Synthesis
2. English -> Nepali Machine Translation (deep_translator)
3. Text-to-Speech Generation (gTTS)
"""

from io import BytesIO
from deep_translator import GoogleTranslator
from gtts import gTTS

def translate_to_nepali(text_en: str) -> str:
    """Translates English text into Nepali using GoogleTranslator."""
    try:
        translated = GoogleTranslator(source='en', target='ne').translate(text_en)
        return translated if translated else text_en
    except Exception as e:
        # Fallback to English if translation service is unavailable
        return f"[Translation Error: {text_en}]"

def text_to_speech(text: str, lang: str = 'en') -> bytes:
    """
    Converts input text into spoken MP3 audio bytes using gTTS.
    lang='en' for English, lang='ne' for Nepali.
    """
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        audio_buffer = BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return audio_buffer.read()
    except Exception as e:
        return b""

def generate_scan_announcement(product_name: str, price: float, sku: str) -> dict:
    """
    Generates bilingual announcement (English & Nepali) + Audio for a single scanned product.
    """
    text_en = f"Product scanned: {product_name}. SKU {sku}. Price {price:.2f} dollars. Saved to Excel."
    text_ne = translate_to_nepali(text_en)
    
    audio_en = text_to_speech(text_en, lang='en')
    audio_ne = text_to_speech(text_ne, lang='ne')
    
    return {
        "text_en": text_en,
        "text_ne": text_ne,
        "audio_en": audio_en,
        "audio_ne": audio_ne
    }

def generate_batch_announcement(item_count: int, total_val: float) -> dict:
    """Generates bilingual announcement for batch scan completion."""
    text_en = f"Batch scan complete. Successfully logged {item_count} items into Excel ledger. Total value is {total_val:.2f} dollars."
    text_ne = translate_to_nepali(text_en)
    
    audio_en = text_to_speech(text_en, lang='en')
    audio_ne = text_to_speech(text_ne, lang='ne')
    
    return {
        "text_en": text_en,
        "text_ne": text_ne,
        "audio_en": audio_en,
        "audio_ne": audio_ne
    }

def generate_shift_summary_audio(stats: dict) -> dict:
    """Generates an executive voice report of current Excel ledger inventory."""
    total = stats.get("total_scanned", 0)
    val = stats.get("total_value", 0.0)
    skus = stats.get("unique_skus", 0)
    qc = stats.get("qc_passed", 0)
    
    text_en = (
        f"Inventory operations update: Total {total} products logged across {skus} unique SKUs. "
        f"Cumulative valuation is {val:.2f} dollars. Quality control passed for {qc} items."
    )
    
    text_ne = translate_to_nepali(text_en)
    
    audio_en = text_to_speech(text_en, lang='en')
    audio_ne = text_to_speech(text_ne, lang='ne')
    
    return {
        "text_en": text_en,
        "text_ne": text_ne,
        "audio_en": audio_en,
        "audio_ne": audio_ne
    }
