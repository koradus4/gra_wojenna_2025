# Własne grafiki presetów

Ten folder zawiera niestandardowe grafiki PNG, które można importować jako presety w edytorze map.

## Jak używać

1. **Przygotuj obraz PNG** o wymiarach **64×64 pikseli** (lub mniejszy – zostanie wycentrowany)
2. **Użyj kanału alpha** do przezroczystości (piksele o alpha < 30 będą ignorowane)
3. **Zapisz plik** w tym folderze z opisową nazwą, np.:
   - `fort_kamienny.png`
   - `wioska_sredniowieczna.png`
   - `most_drewniany.png`
   
4. **Uruchom edytor tekstur** – kategoria **"Własne grafiki"** automatycznie załaduje wszystkie PNG z tego folderu

## Wskazówki

- **Skalowanie**: Po załadowaniu możesz skalować preset suwakiem 10–100%
- **Nazewnictwo**: Podkreślenia `_` w nazwie pliku zamienią się na spacje w UI
- **Paleta**: Używaj kolorów pasujących do estetyki gry (naturalne tony, wysoka saturacja dla ważnych punktów)
- **Rozmiar**: Mniejsze obrazy (np. 32×32) zostaną wycentrowane na 64×64
- **Format**: Tylko PNG z kanałem alpha; JPG/BMP nie są wspierane

## Przykładowe narzędzia do tworzenia grafiki

- **Aseprite** (pixel art)
- **GIMP** (darmowy edytor z wsparciem alpha)
- **Krita** (malowanie cyfrowe)
- **Photoshop** (profesjonalne)

## Debugowanie

Jeśli preset się nie ładuje, sprawdź terminal – błędy importu są logowane z prefiksem `⚠️`.
