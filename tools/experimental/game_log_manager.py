"""
Menedżer Logów Gry (Game Log Manager) - Scentralizowane zarządzanie logowaniem
Sistema de registro centralizado para el juego de guerra

Organizuje logi w strukturze:
- ai/logs/ai/ - Sztuczna Inteligencja (Artificial Intelligence)
- ai/logs/human/ - Gracz Ludzki (Human Player)  
- ai/logs/game/ - Mechanika Gry (Game Mechanics)
- ai/logs/analysis/ - Analiza Danych (Data Analysis)

Każdy katalog ma swoje podkategorie dla szczegółowej organizacji logów.
"""

from __future__ import annotations
import json
import csv
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Literal
from enum import Enum
from dataclasses import dataclass, asdict

from utils.session_manager import LOGS_ROOT

# Definiowanie kategorii logów (Log Categories)
class KategoriaLog(Enum):
    """Kategorie logów (Log Categories)"""
    # AI Categories
    AI_DOWODCA = "ai/dowodca"          # AI Commander
    AI_GENERAL = "ai/general"          # AI General
    AI_WALKA = "ai/walka"             # AI Combat
    AI_RUCH = "ai/ruch"               # AI Movement
    AI_ZAOPATRZENIE = "ai/zaopatrzenie" # AI Supply
    AI_STRATEGIA = "ai/strategia"     # AI Strategy
    
    # Human Categories
    HUMAN_AKCJE = "human/akcje"       # Human Actions
    HUMAN_DECYZJE = "human/decyzje"   # Human Decisions
    HUMAN_INTERFEJS = "human/interfejs" # Human Interface
    
    # Game Categories
    GAME_MECHANIKA = "game/mechanika" # Game Mechanics
    GAME_STAN = "game/stan"           # Game State
    GAME_BLEDY = "game/bledy"         # Game Errors
    
    # Analysis Categories
    ANALYSIS_ML = "analysis/ml_ready" # ML Ready Data
    ANALYSIS_RAPORTY = "analysis/raporty" # Reports
    ANALYSIS_STATYSTYKI = "analysis/statystyki" # Statistics

# Tagi dla lepszej kategoryzacji (Tags for better categorization)
class TagLog(Enum):
    """Tagi logów dla szczegółowej kategoryzacji"""
    # Action Tags
    WALKA = "walka"           # combat
    RUCH = "ruch"             # movement  
    ZAOPATRZENIE = "zaopatrzenie" # supply
    STRATEGIA = "strategia"   # strategy
    DECYZJA = "decyzja"       # decision
    
    # Priority Tags
    KRYTYCZNY = "krytyczny"   # critical
    WAZNY = "wazny"           # important
    INFO = "info"             # information
    DEBUG = "debug"           # debug
    
    # Player Tags
    AI = "ai"                 # artificial intelligence
    HUMAN = "human"           # human player
    SYSTEM = "system"         # system

@dataclass
class WpisLog:
    """Struktura wpisu loga (Log Entry Structure)"""
    timestamp: str
    kategoria: KategoriaLog
    tagi: List[TagLog]
    gracz: Optional[str] = None      # player
    tura: Optional[int] = None       # turn
    faza: Optional[str] = None       # phase
    akcja: Optional[str] = None      # action
    szczegoly: Optional[Dict[str, Any]] = None  # details
    blad: Optional[str] = None       # error
    poziom: str = "INFO"             # level
    ml_dane: Optional[Dict[str, Any]] = None    # ML data

class GameLogManager:
    """
    Menedżer Logów Gry - Główna klasa do zarządzania systemem logowania
    (Game Log Manager - Main class for managing logging system)
    """
    
    def __init__(self, katalog_bazowy: Optional[Union[str, Path]] = None):
        """
        Inicializacja menedżera logów
        
        Args:
            katalog_bazowy: Katalog bazowy dla wszystkich logów (domyślnie `ai/logs`)
        """
        self.katalog_bazowy = Path(katalog_bazowy) if katalog_bazowy else Path(LOGS_ROOT)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.aktywna_gra = None
        self.aktualny_gracz = None
        self.aktualna_tura = 0
        
        # Tworzenie struktury katalogów
        self._utworz_strukture_katalogow()
        
        # Konfiguracja loggerów Pythona
        self._konfiguruj_loggery()
        
        # Statystyki sesji
        self.statystyki = {
            "wpisy_lacznie": 0,
            "wpisy_ai": 0,
            "wpisy_human": 0,
            "wpisy_game": 0,
            "bledy_lacznie": 0,
            "sesja_start": datetime.now()
        }
    
    def _utworz_strukture_katalogow(self):
        """Tworzy pełną strukturę katalogów logów"""
        for kategoria in KategoriaLog:
            katalog = self.katalog_bazowy / kategoria.value
            katalog.mkdir(parents=True, exist_ok=True)
    
    def _konfiguruj_loggery(self):
        """Konfiguruje loggery Pythona dla różnych kategorii"""
        self.loggery = {}
        
        for kategoria in KategoriaLog:
            logger_name = f"game.{kategoria.name.lower()}"
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.INFO)
            
            # Handler dla pliku
            plik_log = self.katalog_bazowy / kategoria.value / f"python_{self.session_id}.log"
            handler = logging.FileHandler(plik_log, encoding='utf-8')
            handler.setLevel(logging.INFO)
            
            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            
            logger.addHandler(handler)
            self.loggery[kategoria] = logger
    
    def ustaw_kontekst_gry(self, gracz: str, tura: int, gra_id: Optional[str] = None):
        """
        Ustawia kontekst aktualnej gry
        
        Args:
            gracz: Nazwa gracza (player name)
            tura: Numer tury (turn number)  
            gra_id: ID gry (optional)
        """
        self.aktualny_gracz = gracz
        self.aktualna_tura = tura
        if gra_id:
            self.aktywna_gra = gra_id
    
    def log(self, 
           kategoria: KategoriaLog,
           wiadomosc: str,
           tagi: Optional[List[TagLog]] = None,
           szczegoly: Optional[Dict[str, Any]] = None,
           poziom: str = "INFO",
           ml_dane: Optional[Dict[str, Any]] = None) -> bool:
        """
        Główna metoda logowania
        
        Args:
            kategoria: Kategoria loga
            wiadomosc: Wiadomość do zalogowania
            tagi: Lista tagów (optional)
            szczegoly: Dodatkowe szczegóły (optional)
            poziom: Poziom loga (INFO, WARNING, ERROR, DEBUG)
            ml_dane: Dane do uczenia maszynowego (optional)
            
        Returns:
            bool: True jeśli zapisano pomyślnie
        """
        try:
            # Tworzenie wpisu loga
            wpis = WpisLog(
                timestamp=datetime.now().isoformat(),
                kategoria=kategoria,
                tagi=tagi or [],
                gracz=self.aktualny_gracz,
                tura=self.aktualna_tura,
                akcja=wiadomosc,
                szczegoly=szczegoly,
                poziom=poziom,
                ml_dane=ml_dane
            )
            
            # Zapisywanie w różnych formatach
            self._zapisz_json(wpis)
            self._zapisz_csv(wpis)
            self._zapisz_python_log(wpis)
            
            # Aktualizacja statystyk
            self._aktualizuj_statystyki(kategoria, poziom)
            
            return True
            
        except Exception as e:
            print(f"❌ Błąd logowania (Logging Error): {e}")
            return False
    
    def _zapisz_json(self, wpis: WpisLog):
        """Zapisuje wpis w formacie JSON"""
        plik = self.katalog_bazowy / wpis.kategoria.value / f"dane_{self.session_id}.json"
        
        # Ładowanie istniejących danych
        dane = []
        if plik.exists():
            try:
                with open(plik, 'r', encoding='utf-8') as f:
                    dane = json.load(f)
            except json.JSONDecodeError:
                dane = []
        
        # Dodanie nowego wpisu
        wpis_dict = asdict(wpis)
        wpis_dict['kategoria'] = wpis.kategoria.value
        wpis_dict['tagi'] = [tag.value for tag in wpis.tagi]
        dane.append(wpis_dict)
        
        # Zapisanie
        with open(plik, 'w', encoding='utf-8') as f:
            json.dump(dane, f, ensure_ascii=False, indent=2)
    
    def _zapisz_csv(self, wpis: WpisLog):
        """Zapisuje wpis w formacie CSV"""
        plik = self.katalog_bazowy / wpis.kategoria.value / f"dane_{self.session_id}.csv"
        
        # Przygotowanie danych CSV
        dane_csv = {
            'timestamp': wpis.timestamp,
            'kategoria': wpis.kategoria.value,
            'tagi': ','.join([tag.value for tag in wpis.tagi]),
            'gracz': wpis.gracz or '',
            'tura': wpis.tura or 0,
            'faza': wpis.faza or '',
            'akcja': wpis.akcja or '',
            'poziom': wpis.poziom,
            'blad': wpis.blad or '',
            'szczegoly_json': json.dumps(wpis.szczegoly) if wpis.szczegoly else '',
            'ml_dane_json': json.dumps(wpis.ml_dane) if wpis.ml_dane else ''
        }
        
        # Sprawdzenie czy plik istnieje
        plik_istnieje = plik.exists()
        
        # Zapisanie
        with open(plik, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=dane_csv.keys())
            if not plik_istnieje:
                writer.writeheader()
            writer.writerow(dane_csv)
    
    def _zapisz_python_log(self, wpis: WpisLog):
        """Zapisuje wpis za pomocą loggera Pythona"""
        logger = self.loggery.get(wpis.kategoria)
        if logger:
            message = f"[{wpis.gracz}|T{wpis.tura}] {wpis.akcja}"
            if wpis.szczegoly:
                message += f" | {wpis.szczegoly}"
            
            poziom = wpis.poziom.upper()
            if poziom == "ERROR":
                logger.error(message)
            elif poziom == "WARNING":
                logger.warning(message)
            elif poziom == "DEBUG":
                logger.debug(message)
            else:
                logger.info(message)
    
    def _aktualizuj_statystyki(self, kategoria: KategoriaLog, poziom: str):
        """Aktualizuje statystyki logowania"""
        self.statystyki["wpisy_lacznie"] += 1
        
        if kategoria.value.startswith("ai/"):
            self.statystyki["wpisy_ai"] += 1
        elif kategoria.value.startswith("human/"):
            self.statystyki["wpisy_human"] += 1
        elif kategoria.value.startswith("game/"):
            self.statystyki["wpisy_game"] += 1
            
        if poziom.upper() == "ERROR":
            self.statystyki["bledy_lacznie"] += 1
    
    # Metody wygodne dla konkretnych kategorii (Convenience methods)
    
    def log_ai_dowodca(self, wiadomosc: str, **kwargs):
        """Loguje akcję AI Dowódcy (AI Commander)"""
        return self.log(KategoriaLog.AI_DOWODCA, wiadomosc, 
                       tagi=[TagLog.AI, TagLog.STRATEGIA], **kwargs)
    
    def log_ai_general(self, wiadomosc: str, **kwargs):
        """Loguje akcję AI Generała (AI General)"""
        return self.log(KategoriaLog.AI_GENERAL, wiadomosc,
                       tagi=[TagLog.AI, TagLog.DECYZJA], **kwargs)
    
    def log_ai_walka(self, wiadomosc: str, **kwargs):
        """Loguje akcję walki AI (AI Combat)"""
        return self.log(KategoriaLog.AI_WALKA, wiadomosc,
                       tagi=[TagLog.AI, TagLog.WALKA], **kwargs)
    
    def log_ai_ruch(self, wiadomosc: str, **kwargs):
        """Loguje ruch AI (AI Movement)"""
        return self.log(KategoriaLog.AI_RUCH, wiadomosc,
                       tagi=[TagLog.AI, TagLog.RUCH], **kwargs)
    
    def log_ai_zaopatrzenie(self, wiadomosc: str, **kwargs):
        """Loguje zaopatrzenie AI (AI Supply)"""
        return self.log(KategoriaLog.AI_ZAOPATRZENIE, wiadomosc,
                       tagi=[TagLog.AI, TagLog.ZAOPATRZENIE], **kwargs)
    
    def log_human_akcja(self, wiadomosc: str, **kwargs):
        """Loguje akcję gracza ludzkiego (Human Player Action)"""
        return self.log(KategoriaLog.HUMAN_AKCJE, wiadomosc,
                       tagi=[TagLog.HUMAN], **kwargs)
    
    def log_human_decyzja(self, wiadomosc: str, **kwargs):
        """Loguje decyzję gracza ludzkiego (Human Player Decision)"""
        return self.log(KategoriaLog.HUMAN_DECYZJE, wiadomosc,
                       tagi=[TagLog.HUMAN, TagLog.DECYZJA], **kwargs)
    
    def log_game_error(self, wiadomosc: str, **kwargs):
        """Loguje błąd gry (Game Error)"""
        kwargs.setdefault('poziom', 'ERROR')
        return self.log(KategoriaLog.GAME_BLEDY, wiadomosc,
                       tagi=[TagLog.SYSTEM], **kwargs)
    
    def log_game_mechanika(self, wiadomosc: str, **kwargs):
        """Loguje mechanikę gry (Game Mechanics)"""
        return self.log(KategoriaLog.GAME_MECHANIKA, wiadomosc,
                       tagi=[TagLog.SYSTEM], **kwargs)
    
    def generuj_raport_sesji(self) -> Dict[str, Any]:
        """
        Generuje raport z aktualnej sesji logowania
        
        Returns:
            Dict zawierający statystyki sesji
        """
        czas_sesji = datetime.now() - self.statystyki["sesja_start"]
        
        return {
            "session_id": self.session_id,
            "czas_trwania_sesji": str(czas_sesji),
            "statystyki": self.statystyki.copy(),
            "aktywna_gra": self.aktywna_gra,
            "ostatni_gracz": self.aktualny_gracz,
            "ostatnia_tura": self.aktualna_tura,
            "struktura_katalogow": [k.value for k in KategoriaLog],
            "dostepne_tagi": [t.value for t in TagLog]
        }
    
    def zapisz_raport_sesji(self):
        """Zapisuje raport sesji do pliku"""
        raport = self.generuj_raport_sesji()
        plik = self.katalog_bazowy / "analysis" / "raporty" / f"sesja_{self.session_id}.json"
        
        with open(plik, 'w', encoding='utf-8') as f:
            json.dump(raport, f, ensure_ascii=False, indent=2, default=str)

# Singleton instance dla łatwego dostępu
_game_log_manager = None

def get_game_log_manager() -> GameLogManager:
    """Zwraca singleton instancję GameLogManager"""
    global _game_log_manager
    if _game_log_manager is None:
        _game_log_manager = GameLogManager()
    return _game_log_manager

# Export głównych klas i funkcji
__all__ = [
    'GameLogManager',
    'KategoriaLog',
    'TagLog', 
    'WpisLog',
    'get_game_log_manager'
]