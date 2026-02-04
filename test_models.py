import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

print(f"🔑 API Key présente: {bool(api_key)}")
print(f"🔑 Premiers caractères: {api_key[:20]}...")

genai.configure(api_key=api_key)

print("\n📋 Modèles disponibles avec generateContent:\n")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ {m.name}")
except Exception as e:
    print(f"❌ Erreur lors du listing: {e}")