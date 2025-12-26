# 🏗️ Generator Budynków Miejskich - INSTRUKCJA KONFIGURACJI

## 📋 SZYBKI START - KONFIGURACJA VERTEX AI IMAGEN 3

### ✅ KROK 1: Instalacja bibliotek

```powershell
# Otwórz PowerShell i uruchom:
pip install google-cloud-aiplatform
pip install google-generativeai
```

### ✅ KROK 2: Utwórz Service Account w Google Cloud

1. **Otwórz Google Cloud Console:**
   - https://console.cloud.google.com/
   - Zaloguj się

2. **Wybierz projekt:**
   - Project ID: `gen-lang-client-0986780723`

3. **Utwórz Service Account:**
   - Menu → **IAM & Admin** → **Service Accounts**
   - Kliknij **"+ CREATE SERVICE ACCOUNT"**
   
   **Konfiguracja:**
   - Service account name: `imagen-building-generator`
   - Description: `Service account for Vertex AI Imagen 3 building generator`
   - Kliknij **"CREATE AND CONTINUE"**

4. **Nadaj uprawnienia:**
   - Wybierz role:
     - ✅ `Vertex AI User`
     - ✅ `AI Platform Developer` (opcjonalnie)
   - Kliknij **"CONTINUE"** → **"DONE"**

5. **Wygeneruj klucz JSON:**
   - Kliknij na utworzony Service Account
   - Zakładka **"KEYS"**
   - **"ADD KEY"** → **"Create new key"**
   - Wybierz **JSON**
   - Pobierz plik (zostanie zapisany w Downloads)

### ✅ KROK 3: Zapisz klucz w projekcie

```powershell
# Utwórz folder credentials
mkdir "c:\Users\klif\OneDrive\Pulpit\gra wojenna 17082025\credentials"

# Przenieś pobrany plik JSON
# ZAMIEŃ "gen-lang-client-*.json" na faktyczną nazwę pobranego pliku!
move "C:\Users\klif\Downloads\gen-lang-client-*.json" "c:\Users\klif\OneDrive\Pulpit\gra wojenna 17082025\credentials\vertex-ai-key.json"
```

### ✅ KROK 4: Ustaw zmienną środowiskową

**Opcja A: Dla bieżącej sesji PowerShell**
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="c:\Users\klif\OneDrive\Pulpit\gra wojenna 17082025\credentials\vertex-ai-key.json"
```

**Opcja B: Trwale (ZALECANE)**
1. Naciśnij `Windows + R`
2. Wpisz: `sysdm.cpl`
3. Zakładka **"Advanced"** → **"Environment Variables"**
4. W sekcji **"User variables"** kliknij **"New"**
5. Wpisz:
   - **Variable name:** `GOOGLE_APPLICATION_CREDENTIALS`
   - **Variable value:** `c:\Users\klif\OneDrive\Pulpit\gra wojenna 17082025\credentials\vertex-ai-key.json`
6. Kliknij **OK** → **OK**
7. **Zrestartuj VS Code** (aby odświeżyć zmienne)

### ✅ KROK 5: Włącz Vertex AI API

1. Otwórz: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project=gen-lang-client-0986780723
2. Kliknij **"ENABLE"**
3. Poczekaj ~30 sekund na aktywację

### ✅ KROK 6: Test połączenia

```powershell
cd "c:\Users\klif\OneDrive\Pulpit\gra wojenna 17082025"
python edytory/test_vertex_ai.py
```

**Oczekiwany wynik:**
```
✅ SUKCES! Vertex AI Imagen 3 gotowy do użycia!
```

---

## 🎯 JAK UŻYWAĆ GENERATORA

### 1. Uruchom narzędzie
```powershell
cd "c:\Users\klif\OneDrive\Pulpit\gra wojenna 17082025"
python edytory/generate_settlement_buildings.py
```

### 2. Wybierz tryb: **🏗️ GENERUJ NOWE BUDYNKI (Imagen 3)**

### 3. Wybierz typ budynku z listy:
- Kamienica
- Dom mieszkalny
- Ratusz
- Sklep/warsztat
- Kościół
- Dworzec kolejowy
- Szkoła
- Szpital
- Restauracja/kawiarnia
- Bank
- Teatr/kino
- Fabryka/zakład
- Magazyn
- Hotel
- Poczta
- Straż pożarna
- Koszary wojskowe
- Muzeum

### 4. Skonfiguruj:
- **Liczba wariantów:** ile budynków wygenerować (1-12)
- **Style:** cegła, tynk, kamień, drewno (zaznacz które chcesz)

### 5. Kliknij **🎨 GENERUJ WARIANTY**

### 6. Poczekaj (~30-60 sekund na budynek)

### 7. Zapisz: **💾 Zapisz wszystkie**

**Pliki zostaną zapisane w:**
```
assets/terrain/presets/user_assets/settlement/ai_generated/
```

---

## ⚠️ ROZWIĄZYWANIE PROBLEMÓW

### Problem 1: "No module named 'vertexai'"
**Rozwiązanie:**
```powershell
pip install google-cloud-aiplatform
```

### Problem 2: "DefaultCredentialsError"
**Rozwiązanie:** Sprawdź czy zmienna `GOOGLE_APPLICATION_CREDENTIALS` jest ustawiona:
```powershell
echo $env:GOOGLE_APPLICATION_CREDENTIALS
```
Jeśli puste - przejdź do Kroku 4.

### Problem 3: "Permission denied" lub "403 Forbidden"
**Rozwiązanie:** 
1. Service Account musi mieć rolę **Vertex AI User**
2. Sprawdź w: https://console.cloud.google.com/iam-admin/iam

### Problem 4: "API not enabled"
**Rozwiązanie:**
1. Włącz Vertex AI API (Krok 5)
2. Poczekaj 1-2 minuty i spróbuj ponownie

### Problem 5: "Quota exceeded"
**Rozwiązanie:**
- Imagen 3 ma limity requestów
- Sprawdź: https://console.cloud.google.com/iam-admin/quotas
- Filtruj: "Vertex AI API"
- Możesz generować po 1 budynku zamiast batch

---

## 💰 KOSZTY VERTEX AI IMAGEN 3

- **$0.04 USD** za obraz 1024x1024
- **$0.02 USD** za obraz 256x256
- Generujemy **64x64** (zaliczane jako 256x256)

**Przykładowe koszty:**
- 10 budynków = ~$0.20
- 50 budynków = ~$1.00
- 100 budynków = ~$2.00

**Free tier:** Nowi użytkownicy dostają **$300 kredytów** na 90 dni!

---

## 📁 STRUKTURA PLIKÓW

```
edytory/
├── generate_settlement_buildings.py  # 🎨 Główne narzędzie GUI
├── test_vertex_ai.py                 # 🧪 Test konfiguracji
credentials/
└── vertex-ai-key.json                # 🔑 Klucz Service Account (NIE commituj!)
assets/terrain/presets/user_assets/settlement/
├── kamienica_miejska1.png            # 🖼️ Obrazy referencyjne
├── dom_1.png
└── ai_generated/                     # 📂 Wygenerowane budynki
    ├── kamienica_cegła_v1_20251223_143022.png
    └── ...
```

---

## 🔗 LINKI

- **Vertex AI Console:** https://console.cloud.google.com/vertex-ai
- **Imagen Dokumentacja:** https://cloud.google.com/vertex-ai/docs/generative-ai/image/generate-images
- **Pricing:** https://cloud.google.com/vertex-ai/pricing#generative_ai_models
- **IAM & Service Accounts:** https://console.cloud.google.com/iam-admin/serviceaccounts

---

## 📞 POMOC

Jeśli coś nie działa:
1. Uruchom test: `python edytory/test_vertex_ai.py`
2. Sprawdź dokumentację: `docs/VERTEX_AI_SETUP_GUIDE.md`
3. Sprawdź logi w konsoli PowerShell

**Szczegółowa dokumentacja:** `docs/VERTEX_AI_SETUP_GUIDE.md`
