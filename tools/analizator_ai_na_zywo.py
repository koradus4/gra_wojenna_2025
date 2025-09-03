#!/usr/bin/env python3
"""
ANALIZATOR AI W CZASIE RZECZYWISTYM
Monitoruje logi AI i wyświetla statystyki na żywo
Uruchomienie: python tools/analizator_ai_na_zywo.py
"""
import csv
import json
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict, deque
import threading
import io

class AnalizatorAINaZywo:
    def __init__(self, katalog_logow="logs/ai_flow"):
        self.katalog_logow = Path(katalog_logow)
        self.dziala = False
        self.statystyki = defaultdict(lambda: defaultdict(int))
        self.ostatnie_zdarzenia = deque(maxlen=50)
        self.ostatnie_rozmiary_plikow = {}
        self.watek_monitorowania = None

    def rozpocznij_monitorowanie(self):
        """Rozpoczyna monitorowanie logów AI"""
        if self.dziala:
            return
        self.dziala = True
        self.watek_monitorowania = threading.Thread(target=self._petla_monitorowania, daemon=True)
        self.watek_monitorowania.start()
        print("🔍 Rozpoczęto monitorowanie logów AI...")

    def zatrzymaj_monitorowanie(self):
        """Zatrzymuje monitorowanie logów AI"""
        self.dziala = False
        if self.watek_monitorowania:
            self.watek_monitorowania.join(timeout=2)
        print("🛑 Zatrzymano monitorowanie")

    def _petla_monitorowania(self):
        """Główna pętla monitorowania"""
        while self.dziala:
            try:
                self._sprawdz_nowe_zdarzenia()
                time.sleep(1)
            except Exception:
                time.sleep(5)

    def _sprawdz_nowe_zdarzenia(self):
        """Sprawdza czy pojawiły się nowe zdarzenia w logach"""
        if not self.katalog_logow.exists():
            return
            
        for plik_csv in self.katalog_logow.glob('*.csv'):
            try:
                aktualny_rozmiar = plik_csv.stat().st_size
                ostatni_rozmiar = self.ostatnie_rozmiary_plikow.get(str(plik_csv), 0)
                
                if aktualny_rozmiar > ostatni_rozmiar:
                    self._czytaj_nowe_linie(plik_csv, ostatni_rozmiar)
                    self.ostatnie_rozmiary_plikow[str(plik_csv)] = aktualny_rozmiar
            except Exception:
                pass

    def _czytaj_nowe_linie(self, plik_csv, pozycja_start):
        """Czyta nowe linie z pliku CSV"""
        try:
            with open(plik_csv, 'r', encoding='utf-8') as f:
                f.seek(pozycja_start)
                zawartosc = f.read()
                
            if not zawartosc.strip():
                return
                
            typ_pliku = self._okresl_typ_pliku(plik_csv.name)
            
            for linia in zawartosc.strip().split('\n'):
                if linia.strip():
                    self._przetwarz_linie_logu(linia, typ_pliku, plik_csv.name)
        except Exception:
            pass

    def _okresl_typ_pliku(self, nazwa_pliku):
        """Określa typ pliku logu na podstawie nazwy"""
        if nazwa_pliku.startswith('ai_flow_'):
            return 'glowny'
        if nazwa_pliku.startswith('purchases_'):
            return 'zakupy'
        if nazwa_pliku.startswith('deployment_'):
            return 'rozmieszczenie'
        if nazwa_pliku.startswith('debug_'):
            return 'debug'
        return 'nieznany'

    def _przetwarz_linie_logu(self, linia, typ_pliku, nazwa_pliku):
        """Przetwarza pojedynczą linię logu"""
        try:
            czytnik = csv.reader(io.StringIO(linia))
            wiersz = next(czytnik)
            
            if typ_pliku == 'glowny':
                self._przetwarz_zdarzenie_glowne(wiersz, nazwa_pliku)
            elif typ_pliku == 'zakupy':
                self._przetwarz_zdarzenie_zakupu(wiersz, nazwa_pliku)
            elif typ_pliku == 'rozmieszczenie':
                self._przetwarz_zdarzenie_rozmieszczenia(wiersz, nazwa_pliku)
            elif typ_pliku == 'debug':
                self._przetwarz_zdarzenie_debug(wiersz, nazwa_pliku)
        except Exception:
            pass

    def _przetwarz_zdarzenie_glowne(self, wiersz, nazwa_pliku):
        """Przetwarza zdarzenie główne"""
        if len(wiersz) < 6:
            return
            
        czas, tura, faza, komponent, akcja, status = wiersz[:6]
        szczegoly = wiersz[6] if len(wiersz) > 6 else ''
        
        zdarzenie = {
            'czas': czas, 'tura': tura, 'faza': faza, 'komponent': komponent,
            'akcja': akcja, 'status': status, 'szczegoly': szczegoly, 
            'plik': nazwa_pliku, 'typ': 'glowny'
        }
        
        self.ostatnie_zdarzenia.append(zdarzenie)
        self.statystyki['glowne'][f"{komponent}_{akcja}"] += 1
        self.statystyki['statusy'][status] += 1

    def _przetwarz_zdarzenie_zakupu(self, wiersz, nazwa_pliku):
        """Przetwarza zdarzenie zakupu jednostki"""
        if len(wiersz) < 10:
            return
            
        czas, tura, id_dowodcy, typ_jednostki, rozmiar_jednostki, koszt = wiersz[:6]
        pe_przed, pe_po, folder_utworzony, json_utworzony = wiersz[6:10]
        sukces = wiersz[12] if len(wiersz) > 12 else 'True'
        
        wydane_pe = 0
        if pe_przed.isdigit() and pe_po.isdigit():
            wydane_pe = int(pe_przed) - int(pe_po)
        
        zdarzenie = {
            'czas': czas, 'tura': tura, 'id_dowodcy': id_dowodcy,
            'typ_jednostki': typ_jednostki, 'rozmiar_jednostki': rozmiar_jednostki, 
            'koszt': koszt, 'wydane_pe': wydane_pe,
            'sukces': sukces.lower() == 'true', 'typ': 'zakup'
        }
        
        self.ostatnie_zdarzenia.append(zdarzenie)
        self.statystyki['zakupy']['total'] += 1
        self.statystyki['zakupy'][f"{typ_jednostki}_{rozmiar_jednostki}"] += 1
        
        if zdarzenie['sukces']:
            self.statystyki['zakupy']['udane'] += 1
        else:
            self.statystyki['zakupy']['nieudane'] += 1

    def _przetwarz_zdarzenie_rozmieszczenia(self, wiersz, nazwa_pliku):
        """Przetwarza zdarzenie rozmieszczenia jednostki"""
        if len(wiersz) < 8:
            return
            
        czas, tura, id_dowodcy, id_zetona, typ_jednostki = wiersz[:5]
        deploy_q, deploy_r = wiersz[5:7]
        sukces = wiersz[11] if len(wiersz) > 11 else 'True'
        
        zdarzenie = {
            'czas': czas, 'tura': tura, 'id_dowodcy': id_dowodcy,
            'id_zetona': id_zetona, 'typ_jednostki': typ_jednostki, 
            'pozycja': (deploy_q, deploy_r),
            'sukces': sukces.lower() == 'true', 'typ': 'rozmieszczenie'
        }
        
        self.ostatnie_zdarzenia.append(zdarzenie)
        self.statystyki['rozmieszczenia']['total'] += 1
        
        if zdarzenie['sukces']:
            self.statystyki['rozmieszczenia']['udane'] += 1
        else:
            self.statystyki['rozmieszczenia']['nieudane'] += 1

    def _przetwarz_zdarzenie_debug(self, wiersz, nazwa_pliku):
        """Przetwarza zdarzenie debug"""
        if len(wiersz) < 5:
            return
            
        czas, tura, komponent, funkcja, typ_zdarzenia = wiersz[:5]
        self.statystyki['debug'][f"{komponent}_{funkcja}"] += 1
        self.statystyki['debug']['total'] += 1

    def pokaz_statystyki(self):
        """Wyświetla aktualne statystyki"""
        print("\n" + "=" * 40)
        print("📊 STATYSTYKI AI")
        print("=" * 40)
        
        print("🎯 STATUSY:")
        for status, liczba in self.statystyki['statusy'].items():
            print(f"  {status}: {liczba}")
        
        print("\n💰 ZAKUPY:")
        if self.statystyki['zakupy']:
            total = self.statystyki['zakupy']['total']
            udane = self.statystyki['zakupy']['udane']
            nieudane = self.statystyki['zakupy']['nieudane']
            print(f"  Łącznie: {total} | Udane: {udane} | Nieudane: {nieudane}")
        
        print("\n🎯 ROZMIESZCZENIA:")
        if self.statystyki['rozmieszczenia']:
            total = self.statystyki['rozmieszczenia']['total']
            udane = self.statystyki['rozmieszczenia']['udane']
            nieudane = self.statystyki['rozmieszczenia']['nieudane']
            print(f"  Łącznie: {total} | Udane: {udane} | Nieudane: {nieudane}")
        
        print("\n📋 OSTATNIE ZDARZENIA:")
        for zdarzenie in list(self.ostatnie_zdarzenia)[-5:]:
            typ = zdarzenie['typ']
            akcja = zdarzenie.get('akcja') or zdarzenie.get('typ_jednostki', '')
            status = zdarzenie.get('status', 'OK' if zdarzenie.get('sukces', True) else 'BŁĄD')
            print(f"  {typ}: {akcja} → {status}")

    def zapisz_raport(self, nazwa_pliku=None):
        """Zapisuje raport do pliku JSON"""
        if not nazwa_pliku:
            czas_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            nazwa_pliku = f"raport_analizy_ai_{czas_str}.json"
        
        raport = {
            'czas_raportu': datetime.now().isoformat(),
            'statystyki': dict(self.statystyki),
            'ostatnie_zdarzenia': list(self.ostatnie_zdarzenia)
        }
        
        self.katalog_logow.mkdir(exist_ok=True)
        sciezka = self.katalog_logow / nazwa_pliku
        
        with open(sciezka, 'w', encoding='utf-8') as f:
            json.dump(raport, f, indent=2, ensure_ascii=False)
        
        return sciezka


def main():
    """Główna funkcja programu"""
    print("🚀 ANALIZATOR AI W CZASIE RZECZYWISTYM")
    print("=" * 50)
    
    analizator = AnalizatorAINaZywo()
    analizator.rozpocznij_monitorowanie()
    
    print("📝 Dostępne komendy:")
    print("  s = pokaż statystyki")
    print("  r = zapisz raport")
    print("  q = zakończ")
    print("-" * 30)
    
    try:
        while True:
            komenda = input("Komenda: ").strip().lower()
            
            if komenda == 'q':
                break
            elif komenda == 's':
                analizator.pokaz_statystyki()
            elif komenda == 'r':
                sciezka = analizator.zapisz_raport()
                print(f"✅ Raport zapisany: {sciezka}")
            else:
                print("❓ Nieznana komenda. Użyj: s/r/q")
                
    except KeyboardInterrupt:
        print("\n🛑 Przerwano przez użytkownika")
    finally:
        analizator.zatrzymaj_monitorowanie()


if __name__ == '__main__':
    main()
