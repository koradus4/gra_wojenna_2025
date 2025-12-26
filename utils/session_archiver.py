import shutil
from pathlib import Path
from typing import Dict


class SessionArchiver:
    """System archiwizacji sesji z rotacją maksymalnie 5 sesji"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.logs_dir = self.project_root / "ai" / "logs" / "sessions"
        self.sesja_aktualna_dir = self.logs_dir / "sesja_aktualna"
        self.archiwum_sesji_dir = self.logs_dir / "archiwum_sesji"
        self.max_archived_sessions = 5
    
    def archive_current_sessions(self) -> Dict[str, int]:
        """Archiwizuje wszystkie sesje z sesja_aktualna/ do archiwum_sesji/"""
        stats = {
            'archived': 0,
            'cleaned': 0,
            'total_in_archive': 0,
            'errors': 0
        }
        
        print("[ARCHIVER] Rozpoczynam archiwizację sesji...")
        
        if not self.sesja_aktualna_dir.exists():
            print("[ARCHIVER] Brak katalogu sesja_aktualna/ - pomijam archiwizację")
            return stats
        
        has_sessions = any(session_dir.is_dir() for session_dir in self.sesja_aktualna_dir.iterdir())
        if has_sessions:
            self.archiwum_sesji_dir.mkdir(parents=True, exist_ok=True)

        # Przenieś wszystkie foldery sesji do archiwum
        for session_dir in self.sesja_aktualna_dir.iterdir():
            if session_dir.is_dir():
                session_name = session_dir.name
                target_path = self.archiwum_sesji_dir / session_name
                
                try:
                    if target_path.exists():
                        # Jeśli sesja już istnieje w archiwum, nadpisz
                        shutil.rmtree(target_path)
                        print(f"[ARCHIVER] Nadpisano istniejącą sesję: {session_name}")
                    
                    shutil.move(str(session_dir), str(target_path))
                    stats['archived'] += 1
                    print(f"[ARCHIVER] Zarchiwizowano: {session_name}")
                    
                except Exception as e:
                    stats['errors'] += 1
                    print(f"[ARCHIVER] Błąd archiwizacji {session_name}: {e}")
        
        # Wywołaj rotację po archiwizacji
        rotation_stats = self._rotate_archived_sessions()
        stats['cleaned'] = rotation_stats['cleaned']
        stats['total_in_archive'] = rotation_stats['total_remaining']
        
        removed_dirs = self._cleanup_empty_dirs()

        print(f"[ARCHIVER] Archiwizacja zakończona:")
        print(f"   Zarchiwizowano: {stats['archived']} sesji")
        print(f"   Wyczyszczono starych: {stats['cleaned']} sesji") 
        print(f"   W archiwum: {stats['total_in_archive']} sesji")
        if removed_dirs:
            print(f"   Usunięto pustych katalogów: {removed_dirs}")
        if stats['errors'] > 0:
            print(f"   Błędów: {stats['errors']}")
        
        return stats
    
    def _rotate_archived_sessions(self) -> Dict[str, int]:
        """Usuwa najstarsze sesje, zachowując maksymalnie max_archived_sessions"""
        if not self.archiwum_sesji_dir.exists():
            return {'cleaned': 0, 'total_remaining': 0}
        
        # Pobierz wszystkie foldery sesji z archiwum
        session_dirs = [d for d in self.archiwum_sesji_dir.iterdir() if d.is_dir()]
        
        if len(session_dirs) <= self.max_archived_sessions:
            return {'cleaned': 0, 'total_remaining': len(session_dirs)}
        
        # Sortuj sesje według czasu utworzenia (najstarsze pierwsze)
        session_dirs.sort(key=lambda x: x.stat().st_ctime)
        
        # Usuń najstarsze sesje ponad limit
        sessions_to_remove = session_dirs[:-self.max_archived_sessions]
        cleaned = 0
        
        print(f"[ARCHIVER] Rotacja: {len(session_dirs)} sesji -> max {self.max_archived_sessions}")
        
        for old_session in sessions_to_remove:
            try:
                shutil.rmtree(old_session)
                cleaned += 1
                print(f"[ARCHIVER] Usunięto starą sesję: {old_session.name}")
            except Exception as e:
                print(f"[ARCHIVER] Błąd usuwania {old_session.name}: {e}")
        
        remaining_sessions = len(session_dirs) - cleaned
        return {'cleaned': cleaned, 'total_remaining': remaining_sessions}

    def _cleanup_empty_dirs(self) -> int:
        """Usuwa puste katalogi sesji oraz katalog logs, jeśli nie zawiera danych."""
        removed = 0

        for directory in (self.sesja_aktualna_dir, self.archiwum_sesji_dir):
            if directory.exists():
                try:
                    next(directory.iterdir())
                except StopIteration:
                    directory.rmdir()
                    removed += 1
                except OSError:
                    continue

        if self.logs_dir.exists():
            try:
                next(self.logs_dir.iterdir())
            except StopIteration:
                self.logs_dir.rmdir()
                removed += 1
            except OSError:
                pass

        return removed


# Funkcje pomocnicze dla łatwego użycia
def archive_sessions() -> Dict[str, int]:
    """Archiwizuje wszystkie bieżące sesje"""
    archiver = SessionArchiver()
    return archiver.archive_current_sessions()


if __name__ == "__main__":
    # Test systemu archiwizacji
    print("TEST SYSTEM ARCHIWIZACJI")
    print("-" * 50)
    
    # Test archiwizacji
    print("Test archiwizacji...")
    archive_stats = archive_sessions()
    print(f"Wyniki: {archive_stats}")
    
    print("Test archiwizacji zakończony")
