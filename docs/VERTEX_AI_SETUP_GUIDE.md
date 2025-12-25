# VERTEX AI IMAGEN 3 - INSTRUKCJA KONFIGURACJI

## 🔧 Krok 1: Instalacja wymaganych bibliotek

```powershell
pip install google-cloud-aiplatform
pip install google-generativeai
pip install vertexai
```

## 🔑 Krok 2: Konfiguracja Authentication

Vertex AI wymaga **Service Account Key** (plik JSON), nie tylko API Key.

### Opcja A: Service Account (ZALECANE)

1. **Przejdź do Google Cloud Console:**
   - https://console.cloud.google.com/
   - Zaloguj się tym samym kontem co API keys

2. **Wybierz projekt:**
   - Project ID: `gen-lang-client-0986780723`

3. **Utwórz Service Account:**
   - Menu → IAM & Admin → Service Accounts
   - Kliknij "+ CREATE SERVICE ACCOUNT"
   - Nazwa: `imagen-generator`
   - Opis: `Service account for Vertex AI Imagen 3 building generator`
   - Kliknij "CREATE AND CONTINUE"

4. **Nadaj uprawnienia:**
   - Wybierz role:
     - `Vertex AI User`
     - `Storage Object Viewer` (jeśli będziesz pobierać obrazy z Cloud Storage)
   - Kliknij "CONTINUE" → "DONE"

5. **Wygeneruj klucz JSON:**
   - Kliknij na utworzony Service Account
   - Zakładka "KEYS"
   - "ADD KEY" → "Create new key"
   - Wybierz **JSON**
   - Pobierz plik (np. `gen-lang-client-0986780723-1234567890ab.json`)

6. **Zapisz plik w projekcie:**
   ```powershell
   # Utwórz folder dla kluczy (NIE commituj do git!)
   mkdir credentials
   
   # Przenieś pobrany plik JSON do folderu
   move "C:\Users\klif\Downloads\gen-lang-client-*.json" "c:\Users\klif\OneDrive\Pulpit\gra wojenna 17082025\credentials\vertex-ai-key.json"
   ```

7. **Dodaj do .gitignore:**
   ```
   credentials/
   *.json
   ```

8. **Ustaw zmienną środowiskową:**
   ```powershell
   # PowerShell - dla bieżącej sesji
   $env:GOOGLE_APPLICATION_CREDENTIALS="c:\Users\klif\OneDrive\Pulpit\gra wojenna 17082025\credentials\vertex-ai-key.json"
   
   # Trwale (System Environment Variable):
   # Control Panel → System → Advanced → Environment Variables
   # User Variables → New:
   #   Name: GOOGLE_APPLICATION_CREDENTIALS
   #   Value: c:\Users\klif\OneDrive\Pulpit\gra wojenna 17082025\credentials\vertex-ai-key.json
   ```

### Opcja B: gcloud CLI (alternatywna)

```powershell
# Zainstaluj gcloud CLI
# https://cloud.google.com/sdk/docs/install

# Zaloguj się
gcloud auth application-default login

# Ustaw projekt
gcloud config set project gen-lang-client-0986780723
```

## 🧪 Krok 3: Test połączenia

Uruchom test:

```powershell
cd "c:\Users\klif\OneDrive\Pulpit\gra wojenna 17082025"
python -c "from google.cloud import aiplatform; aiplatform.init(project='gen-lang-client-0986780723', location='us-central1'); print('✅ Vertex AI połączony!')"
```

Jeśli działa - zobaczysz: `✅ Vertex AI połączony!`

## ⚠️ Najczęstsze problemy

### Problem 1: "DefaultCredentialsError"
**Rozwiązanie:** Ustaw `GOOGLE_APPLICATION_CREDENTIALS` jak w Kroku 2.8

### Problem 2: "Permission denied"
**Rozwiązanie:** Service Account musi mieć rolę `Vertex AI User` w projekcie

### Problem 3: "API not enabled"
**Rozwiązanie:** 
```
1. https://console.cloud.google.com/apis/library/aiplatform.googleapis.com
2. Kliknij "ENABLE"
```

### Problem 4: "Quota exceeded"
**Rozwiązanie:** Vertex AI Imagen 3 ma limit requestów. Sprawdź:
- https://console.cloud.google.com/iam-admin/quotas
- Filtruj: "Vertex AI API"

## 💰 Koszty

Imagen 3 (imagegeneration@006):
- **$0.04 per image** (1024x1024)
- **$0.02 per image** (256x256)
- Free tier: **$300 credits** dla nowych użytkowników

## 📝 Następne kroki

Po skonfigurowaniu:
1. Uruchom `edytory/generate_settlement_buildings.py`
2. Wybierz metodę "🤖 Vertex AI Imagen 3"
3. Generuj budynki!

## 🔗 Linki

- Vertex AI Console: https://console.cloud.google.com/vertex-ai
- Imagen dokumentacja: https://cloud.google.com/vertex-ai/docs/generative-ai/image/generate-images
- Pricing: https://cloud.google.com/vertex-ai/pricing#generative_ai_models
