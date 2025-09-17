"""
Session Manager - System zarządzania sesjami logowania
====================================================

Zapobiega tworzeniu duplikatów katalogów timestampowych poprzez
utrzymanie jednej aktywnej sesji przez cały czas działania gry.

NOWY SYSTEM: logs/sesja_aktualna/YYYY-MM-DD_HH-MM/ (polskie nazwy)
STARY SYSTEM: logs/current_session/YYYY-MM-DD_HH-MM/ (zastąpiony)
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import threading

class SessionManager:
    """Singleton zarządzający bieżącą sesją logowania"""
    
    _instance: Optional['SessionManager'] = None
    _lock = threading.Lock()
    _current_session_path: Optional[Path] = None
    _session_start_time: Optional[datetime] = None
    _session_lock_file: Optional[Path] = None
    
    def __new__(cls):
        """Singleton pattern - tylko jedna instancja"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SessionManager, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def get_current_session_dir(cls) -> Path:
        """
        Zwraca katalog bieżącej sesji - ZAWSZE TEN SAM przez całą grę
        
        NOWA ŚCIEŻKA: logs/sesja_aktualna/YYYY-MM-DD_HH-MM/
        
        Returns:
            Path: Ścieżka do katalogu bieżącej sesji
        """
        if cls._current_session_path is None:
            cls._initialize_session()
        
        return cls._current_session_path
    
    @classmethod
    def _initialize_session(cls):
        """Inicjalizuje nową sesję z timestampem i archiwizuje starą"""
        # KROK 1: Archiwizuj poprzednią sesję jeśli istnieje
        cls._archive_previous_session()
        
        # KROK 2: Utwórz nową sesję
        cls._session_start_time = datetime.now()
        timestamp = cls._session_start_time.strftime('%Y-%m-%d_%H-%M')
        
        # NOWA ŚCIEŻKA: logs/sesja_aktualna/ (polskie nazwy)
        cls._current_session_path = Path('logs') / 'sesja_aktualna' / timestamp
        cls._current_session_path.mkdir(parents=True, exist_ok=True)
        
        # Tworzenie pliku blokady sesji
        cls._create_session_lock()
        
        print(f"🎯 [SESSION] Nowa sesja: {timestamp}")
        print(f"📁 [SESSION] Katalog: {cls._current_session_path}")
    
    @classmethod
    def _archive_previous_session(cls):
        """Archiwizuj poprzednią sesję z sesja_aktualna/ do archiwum_sesji/"""
        sesja_aktualna_dir = Path('logs') / 'sesja_aktualna'
        archiwum_dir = Path('logs') / 'archiwum_sesji'
        archiwum_dir.mkdir(parents=True, exist_ok=True)
        
        # Znajdź wszystkie sesje w sesja_aktualna/
        if sesja_aktualna_dir.exists():
            existing_sessions = list(sesja_aktualna_dir.glob('*'))
            
            for session_dir in existing_sessions:
                if session_dir.is_dir():
                    # Przenieś do archiwum
                    target_path = archiwum_dir / session_dir.name
                    if not target_path.exists():
                        session_dir.rename(target_path)
                        print(f"📦 [ARCHIWUM] Przeniesiono sesję: {session_dir.name}")
        
        # Zachowaj tylko 5 najnowszych sesji w archiwum
        cls._cleanup_old_archives(archiwum_dir)
    
    @classmethod
    def _cleanup_old_archives(cls, archiwum_dir: Path):
        """Zachowaj tylko 5 najnowszych sesji w archiwum"""
        if not archiwum_dir.exists():
            return
            
        # Sortuj sesje według daty modyfikacji (najnowsze pierwsze)
        archived_sessions = sorted(
            [d for d in archiwum_dir.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        # Usuń sesje starsze niż 5 najnowszych
        sessions_to_delete = archived_sessions[5:]  # Zachowaj tylko 5 najnowszych
        
        for old_session in sessions_to_delete:
            import shutil
            shutil.rmtree(old_session)
            print(f"🗑️ [ARCHIWUM] Usunięto starą sesję: {old_session.name}")
    
    @classmethod
    def _create_session_lock(cls):
        """Tworzy plik .session_lock z informacjami o sesji"""
        if cls._current_session_path is None:
            return
            
        cls._session_lock_file = cls._current_session_path / '.session_lock'
        
        session_info = {
            'start_time': cls._session_start_time.isoformat() if cls._session_start_time else None,
            'pid': os.getpid(),
            'version': '4.1',
            'system': 'Nowy System Sesji - Polskie Nazwy',
            'path': str(cls._current_session_path),
            'created_by': 'SessionManager'
        }
        
        try:
            with open(cls._session_lock_file, 'w', encoding='utf-8') as f:
                json.dump(session_info, f, indent=2, ensure_ascii=False)
            print(f"🔒 [SESSION] Utworzono blokadę: .session_lock")
        except Exception as e:
            print(f"⚠️ [SESSION] Błąd tworzenia blokady: {e}")
    
    @classmethod
    def get_session_info(cls) -> dict:
        """Zwraca informacje o bieżącej sesji"""
        if cls._current_session_path is None:
            return {'status': 'no_active_session'}
        
        return {
            'status': 'active',
            'session_path': str(cls._current_session_path),
            'start_time': cls._session_start_time.isoformat() if cls._session_start_time else None,
            'duration_minutes': (datetime.now() - cls._session_start_time).total_seconds() / 60 if cls._session_start_time else 0,
            'lock_file_exists': cls._session_lock_file.exists() if cls._session_lock_file else False,
            'pid': os.getpid()
        }
    
    @classmethod
    def end_session(cls):
        """Kończy bieżącą sesję (przygotowanie do archiwizacji)"""
        if cls._current_session_path is None:
            print("ℹ️ [SESSION] Brak aktywnej sesji do zakończenia")
            return
        
        print(f"🏁 [SESSION] Kończenie sesji: {cls._current_session_path.name}")
        
        # Aktualizacja pliku blokady z czasem zakończenia
        if cls._session_lock_file and cls._session_lock_file.exists():
            try:
                with open(cls._session_lock_file, 'r', encoding='utf-8') as f:
                    session_info = json.load(f)
                
                session_info['end_time'] = datetime.now().isoformat()
                session_info['duration_minutes'] = (datetime.now() - cls._session_start_time).total_seconds() / 60 if cls._session_start_time else 0
                session_info['status'] = 'ended'
                
                with open(cls._session_lock_file, 'w', encoding='utf-8') as f:
                    json.dump(session_info, f, indent=2, ensure_ascii=False)
                    
                print(f"✅ [SESSION] Zaktualizowano informacje o sesji")
            except Exception as e:
                print(f"⚠️ [SESSION] Błąd aktualizacji blokady: {e}")
        
        # Reset zmiennych klasy
        cls._current_session_path = None
        cls._session_start_time = None
        cls._session_lock_file = None
    
    @classmethod
    def cleanup_empty_sessions(cls):
        """Usuwa puste katalogi sesji (bez plików logów)"""
        sesja_aktualna = Path('logs') / 'sesja_aktualna'
        if not sesja_aktualna.exists():
            return
        
        cleaned = 0
        for session_dir in sesja_aktualna.iterdir():
            if session_dir.is_dir():
                # Sprawdź czy sesja ma jakiekolwiek pliki logów (nie tylko .session_lock)
                log_files = [f for f in session_dir.rglob('*') if f.is_file() and f.name != '.session_lock']
                
                if not log_files:
                    try:
                        # Usuń pustą sesję
                        import shutil
                        shutil.rmtree(session_dir)
                        cleaned += 1
                        print(f"🧹 [SESSION] Usunięto pustą sesję: {session_dir.name}")
                    except Exception as e:
                        print(f"⚠️ [SESSION] Błąd usuwania pustej sesji {session_dir.name}: {e}")
        
        if cleaned > 0:
            print(f"✅ [SESSION] Wyczyszczono {cleaned} pustych sesji")
    
    @classmethod
    def get_specialized_ai_logs_dir(cls) -> dict:
        """Zwraca ścieżki do specjalistycznych logów AI"""
        from typing import Dict
        
        base = cls.get_current_session_dir() / "ai_commander_zaawansowany"
        base.mkdir(parents=True, exist_ok=True)
        
        dirs = {
            'strategiczne': base / 'decyzje_strategiczne',
            'taktyczne': base / 'akcje_taktyczne', 
            'ekonomiczne': base / 'decyzje_ekonomiczne',
            'wywiad': base / 'analiza_wywiadu',
            'wydajnosc': base / 'wydajnosc_ai',
            'zwyciestwo': base / 'analiza_zwyciestwa'
        }
        
        # Tworzenie wszystkich katalogów
        for nazwa, sciezka in dirs.items():
            sciezka.mkdir(parents=True, exist_ok=True)
        
        return dirs


# Funkcje pomocnicze dla kompatybilności z istniejącym kodem
def get_session_log_dir() -> Path:
    """
    NOWA FUNKCJA - zastąpienie starej get_session_log_dir()
    Używa SessionManager zamiast tworzenia nowego timestampu za każdym razem
    """
    return SessionManager.get_current_session_dir()

def get_current_session_dir() -> Path:
    """
    FUNKCJA GLOBALNA - dla kompatybilności z AI modułami
    Zwraca ścieżkę do katalogu bieżącej sesji
    """
    return SessionManager.get_current_session_dir()

def get_log_files():
    """
    Zwraca ścieżki do plików logów AI Commander dla bieżącej sesji
    ZGODNE z ai/logowanie_ai.py
    """
    log_dir = get_session_log_dir() / 'ai_commander'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    today = datetime.now().strftime('%Y%m%d')
    log_file = log_dir / f"actions_{today}.csv"
    turn_log_file = log_dir / f"turns_{today}.csv"
    
    return log_dir, log_file, turn_log_file


if __name__ == "__main__":
    # Test systemu
    print("🧪 TEST SYSTEM SESJI")
    print("-" * 40)
    
    # Test 1: Pierwszego utworzenia sesji
    session1 = SessionManager.get_current_session_dir()
    print(f"Test 1 - Sesja: {session1}")
    
    # Test 2: Powtórnego pobrania (powinno być identyczne)
    session2 = SessionManager.get_current_session_dir()
    print(f"Test 2 - Sesja: {session2}")
    print(f"Identyczne: {session1 == session2}")
    
    # Test 3: Informacje o sesji
    info = SessionManager.get_session_info()
    print(f"Test 3 - Info: {info}")
    
    # Test 4: Funkcje pomocnicze
    log_dir, log_file, turn_file = get_log_files()
    print(f"Test 4 - Log dir: {log_dir}")
    
    print("\n✅ Wszystkie testy zakończone")