import sys
import os
sys.path.insert(0, os.path.abspath("."))
from dotenv import load_dotenv

load_dotenv(override=True)

from backend.translation_layer import get_active_translation_provider, translate

sys.stdout.reconfigure(encoding="utf-8")

print("=== TRANSLATION LAYER PROVIDER AUDIT ===")
info = get_active_translation_provider()
print(f"Active Provider : {info['active_provider']}")
print(f"Riva Model      : {info['riva_model']}")
print(f"Riva Configured : {info['riva_configured']}")
print("=" * 40)

test_cases = [
    ("The patient was admitted with acute chest pain and shortness of breath.", "en", "de", False),
    ("Der Patient wurde wegen akuter Brustschmerzen eingewiesen.", "de", "en", True),
    ("The laboratory results are within normal limits.", "en", "es", False),
    ("Le patient presente une amelioration clinique significative.", "fr", "en", True),
    ("The patient was admitted with acute chest pain and shortness of breath.", "en", "hi", False),
    ("मरीज़ को सीने में तेज़ दर्द और सांस लेने में तकलीफ के कारण भर्ती कराया गया था।", "hi", "en", True),
    ("The laboratory results are within normal limits.", "en", "hi", False),
    ("प्रयोगशाला के परिणाम सामान्य सीमा के भीतर हैं।", "hi", "en", True),
]

for text, src, tgt, to_en in test_cases:
    print(f"\n[INPUT  ({src} -> {tgt})]: {text}")
    output = translate(text, src_lang=src, to_english=to_en, target_lang=tgt)
    print(f"[OUTPUT ({tgt})]: {output}")
