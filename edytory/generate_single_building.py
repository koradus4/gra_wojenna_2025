"""
Szybkie generowanie pojedynczego budynku przez Imagen 3
"""
from pathlib import Path
from PIL import Image
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
from datetime import datetime

# Konfiguracja
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "assets" / "terrain" / "presets" / "user_assets" / "settlement" / "ai_generated"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Init Vertex AI
print("🔧 Inicjalizacja Vertex AI...")
vertexai.init(project='gen-lang-client-0986780723', location='us-central1')

# Załaduj model
print('🤖 Ładuję Imagen 3...')
model = ImageGenerationModel.from_pretrained('imagegeneration@006')

# Prompt dla dworca kolejowego
prompt = """
Create a pixel art building for a 1939 WW2 strategy game map.

BUILDING TYPE:
Railway station building from 1939 Poland. Long rectangular structure with platform area, waiting room visible, industrial-civic architecture. Clock on facade, railway signage, functional utilitarian design. Brick construction typical of Central European railway stations.

CONSTRUCTION STYLE:
Red brick construction, earthy brown-red tones, similar to existing Polish town buildings

TECHNICAL REQUIREMENTS:
- Image size: 64x64 pixels EXACTLY
- View: Isometric top-down perspective (3/4 view like strategy games)
- Art style: Clean pixel art with clear outlines, similar to Age of Empires II
- Color palette: Muted historical colors (browns, greys, earth tones, no neon)
- Era accuracy: 1939 Central European railway architecture
- Tile format: Centered on transparent background, hex-tile compatible
- Detail level: Recognizable at small size, readable on game map
- Shadows: Subtle, consistent light from top-left
- Style: Match the aesthetic of traditional Polish brick buildings

AVOID:
- Modern architecture (glass facades, contemporary design)
- Bright saturated colors (stay muted and historical)
- Photo-realistic rendering (keep it pixel art style)
- Excessive detail that becomes noise at small size
- Anachronistic elements (modern trains, antennas, contemporary vehicles)
""".strip()

print("\n" + "="*60)
print("🚂 GENERUJĘ: Dworzec kolejowy (1939)")
print("="*60)
print(f"\n📝 Prompt (pierwsze 200 znaków):")
print(f"   {prompt[:200]}...")
print(f"\n🎨 Generuję przez Imagen 3...")
print(f"⏳ To potrwa 30-60 sekund...\n")

try:
    # Generuj
    response = model.generate_images(
        prompt=prompt,
        number_of_images=1,
        aspect_ratio='1:1',
        safety_filter_level='block_few',
        person_generation='dont_allow'
    )

    if response.images:
        print('✅ Wygenerowano obraz!')
        
        # Pobierz obraz
        generated_image = response.images[0]
        
        # Zapisz tymczasowo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'dworzec_kolejowy_cegla_{timestamp}.png'
        output_path = OUTPUT_DIR / filename
        
        # Konwersja do PIL
        try:
            pil_img = generated_image._pil_image
        except AttributeError:
            temp_file = OUTPUT_DIR / '_temp_imagen.png'
            generated_image.save(str(temp_file))
            pil_img = Image.open(temp_file)
            temp_file.unlink()
        
        # Post-processing
        print(f"📐 Oryginalny rozmiar: {pil_img.size}")
        
        # Konwersja do RGBA
        if pil_img.mode != 'RGBA':
            pil_img = pil_img.convert('RGBA')
        
        # Resize do 64x64 (pixel-art style)
        if pil_img.size != (64, 64):
            pil_img = pil_img.resize((64, 64), Image.NEAREST)
            print(f"📏 Zmieniono rozmiar na: 64x64px")
        
        # Zapisz finalny obraz
        pil_img.save(output_path)
        
        print(f"\n💾 ZAPISANO:")
        print(f"   {output_path}")
        print(f"\n📊 Szczegóły:")
        print(f"   Rozmiar: {pil_img.size}")
        print(f"   Tryb: {pil_img.mode}")
        print(f"   Format: PNG")
        
        print("\n" + "="*60)
        print("✅ SUKCES! Dworzec kolejowy wygenerowany!")
        print("="*60)
        
        # Pokaż ścieżkę względną
        try:
            rel_path = output_path.relative_to(PROJECT_ROOT)
            print(f"\n📂 Lokalizacja: {rel_path}")
        except:
            pass
            
    else:
        print('❌ Imagen 3 nie zwrócił obrazu')
        print('💡 Sprawdź czy Vertex AI API jest włączony i masz dostęp do modelu')

except Exception as e:
    print(f'\n❌ BŁĄD: {e}')
    import traceback
    traceback.print_exc()
    print("\n💡 Sprawdź:")
    print("   1. Czy jesteś zalogowany: gcloud auth application-default login")
    print("   2. Czy Vertex AI API jest włączony")
    print("   3. Czy masz uprawnienia do projektu gen-lang-client-0986780723")
