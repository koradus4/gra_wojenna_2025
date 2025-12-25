"""
TEST VERTEX AI IMAGEN 3 - Szybki test połączenia
"""

import os
from pathlib import Path

print("=" * 60)
print("🧪 TEST VERTEX AI IMAGEN 3")
print("=" * 60)

# 1. Sprawdź zmienną środowiskową
print("\n1️⃣ Sprawdzam GOOGLE_APPLICATION_CREDENTIALS...")
creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
if creds_path:
    print(f"   ✅ Znaleziono: {creds_path}")
    if Path(creds_path).exists():
        print(f"   ✅ Plik istnieje")
    else:
        print(f"   ❌ Plik NIE istnieje!")
else:
    print(f"   ⚠️  Brak zmiennej GOOGLE_APPLICATION_CREDENTIALS")
    print(f"   📝 Ustaw ją:")
    print(f'      $env:GOOGLE_APPLICATION_CREDENTIALS="c:\\Users\\klif\\OneDrive\\Pulpit\\gra wojenna 17082025\\credentials\\vertex-ai-key.json"')

# 2. Sprawdź biblioteki
print("\n2️⃣ Sprawdzam biblioteki Python...")
try:
    import google.cloud.aiplatform
    print("   ✅ google-cloud-aiplatform zainstalowany")
except ImportError:
    print("   ❌ Brak google-cloud-aiplatform")
    print("   📝 Zainstaluj: pip install google-cloud-aiplatform")

try:
    import vertexai
    print("   ✅ vertexai zainstalowany")
except ImportError:
    print("   ❌ Brak vertexai")
    print("   📝 Zainstaluj: pip install google-cloud-aiplatform")

try:
    import google.generativeai
    print("   ✅ google-generativeai zainstalowany")
except ImportError:
    print("   ❌ Brak google-generativeai")
    print("   📝 Zainstaluj: pip install google-generativeai")

# 3. Test połączenia
print("\n3️⃣ Test połączenia z Vertex AI...")
try:
    import vertexai
    from google.cloud import aiplatform
    
    PROJECT_ID = "gen-lang-client-0986780723"
    LOCATION = "us-central1"
    
    vertexai.init(
        project=PROJECT_ID,
        location=LOCATION
    )
    
    print(f"   ✅ Połączono z projektem: {PROJECT_ID}")
    print(f"   ✅ Region: {LOCATION}")
    
    # Test dostępu do modelu
    print("\n4️⃣ Test dostępu do Imagen 3...")
    from vertexai.preview.vision_models import ImageGenerationModel
    
    model = ImageGenerationModel.from_pretrained("imagegeneration@006")
    print(f"   ✅ Model Imagen 3 załadowany!")
    
    print("\n" + "=" * 60)
    print("✅ SUKCES! Vertex AI Imagen 3 gotowy do użycia!")
    print("=" * 60)
    print("\n📝 Uruchom generator budynków:")
    print("   python edytory/generate_settlement_buildings.py")
    print("\n💡 Wybierz tryb '🏗️ GENERUJ NOWE BUDYNKI (Imagen 3)'")
    
except Exception as e:
    print(f"\n   ❌ BŁĄD: {e}")
    print("\n📖 Sprawdź dokumentację:")
    print("   docs/VERTEX_AI_SETUP_GUIDE.md")
    import traceback
    traceback.print_exc()
