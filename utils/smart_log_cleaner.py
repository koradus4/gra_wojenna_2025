"""
ULEPSZONY SYSTEM CZYSZCZENIA LOGÓW
==================================
Rozróżnia dane sesyjne (do czyszczenia) od archiwalnych (do zachowania)
"""

from pathlib import Path
import shutil
import json
from datetime import datetime, timedelta
from typing import List, Dict
import re

class SmartLogCleaner:
    """Inteligentne czyszczenie z rozróżnieniem na sesyjne vs archiwalne"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.logs_dir = self.project_root / "logs"
        self.today = datetime.now().strftime("%Y%m%d")
    
    def clean_session_only(self) -> Dict[str, int]:
        """Czyść TYLKO bieżącą sesję - zachowaj dane ML i archiwa"""
        stats = {
            'session_files': 0,
            'strategic_orders': 0, 
            'purchased_tokens': 0,
            'start_tokens': 0,
            'preserved_ml': 0
        }
        
        print("🧹 CZYSZCZENIE SESYJNE (zachowuję ML i archiwa)")
        print("-" * 50)
        
        # 1. Rozkazy strategiczne
        orders_file = self.project_root / "data" / "strategic_orders.json"
        if orders_file.exists():
            orders_file.unlink()
            stats['strategic_orders'] = 1
            print("✅ Usunięto rozkazy strategiczne")
        
        # 2. Zakupione żetony
        stats['purchased_tokens'] = self._clean_purchased_tokens()
        
        # 3. start_tokens.json → []
        start_tokens = self.project_root / "assets" / "start_tokens.json"
        if start_tokens.exists():
            start_tokens.write_text('[]', encoding='utf-8')
            stats['start_tokens'] = 1
            print("✅ Wyczyszczono start_tokens.json")
        
        # 4. Bieżące logi sesyjne (tylko z dzisiaj)
        if self.logs_dir.exists():
            session_pattern = f"*{self.today}*"
            preserved_paths = [
                self.logs_dir / "analysis" / "ml_ready",
                self.logs_dir / "analysis" / "raporty", 
                self.logs_dir / "analysis" / "statystyki"
            ]
            
            for log_file in self.logs_dir.rglob("dane_*.csv"):
                if self.today in log_file.name:
                    # Sprawdź czy to nie jest w folderze do zachowania
                    should_preserve = any(
                        preserved_path in log_file.parents 
                        for preserved_path in preserved_paths
                    )
                    
                    if should_preserve:
                        stats['preserved_ml'] += 1
                        print(f"💾 Zachowano: {log_file.relative_to(self.logs_dir)}")
                    else:
                        log_file.unlink()
                        stats['session_files'] += 1
                        print(f"✅ Usunięto: {log_file.relative_to(self.logs_dir)}")
            
            # Usuń też puste pliki python_*.log z dzisiaj
            for log_file in self.logs_dir.rglob("python_*.log"):
                if self.today in log_file.name and log_file.stat().st_size == 0:
                    log_file.unlink()
                    print(f"🗑️ Pusty log: {log_file.relative_to(self.logs_dir)}")
        
        print("-" * 50)
        print(f"✅ SESJA WYCZYSZCZONA:")
        print(f"   📄 Plików sesyjnych: {stats['session_files']}")  
        print(f"   💾 Zachowanych ML: {stats['preserved_ml']}")
        print(f"   🎯 Rozkazy: {stats['strategic_orders']}")
        print(f"   🪙 Żetony: {stats['purchased_tokens']}")
        
        return stats
    
    def clean_preserve_ml(self) -> Dict[str, int]:
        """Pełne czyszczenie z zachowaniem danych ML"""
        stats = self.clean_session_only()
        
        print("\n🧹 CZYSZCZENIE PEŁNE (zachowuję dane ML)")
        print("-" * 50)
        
        # Dodatkowo usuń WSZYSTKIE stare logi (nie tylko z dzisiaj)
        old_files = 0
        if self.logs_dir.exists():
            preserved_paths = [
                self.logs_dir / "analysis" / "ml_ready",
            ]
            
            # Usuń wszystkie dane_*.csv OPRÓCZ ml_ready
            for log_file in self.logs_dir.rglob("dane_*.csv"):
                should_preserve = any(
                    preserved_path in log_file.parents 
                    for preserved_path in preserved_paths
                )
                
                if not should_preserve and self.today not in log_file.name:
                    log_file.unlink()
                    old_files += 1
                    print(f"🗑️ Stary log: {log_file.relative_to(self.logs_dir)}")
            
            # Usuń wszystkie python_*.log
            for log_file in self.logs_dir.rglob("python_*.log"):
                log_file.unlink()
                old_files += 1
        
        stats['old_files'] = old_files
        print(f"✅ PEŁNE CZYSZCZENIE: +{old_files} starych plików")
        
        return stats
    
    def archive_session(self, archive_days: int = 30) -> Dict[str, int]:
        """Archiwizuj bieżącą sesję do archive/YYYY-MM-DD/"""
        archive_dir = self.project_root / "archive" / self.today
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        stats = {'archived_files': 0, 'ml_datasets': 0}
        
        print(f"📚 ARCHIWIZACJA SESJI → archive/{self.today}/")
        print("-" * 50)
        
        if self.logs_dir.exists():
            # Archiwizuj pliki z dzisiaj
            for log_file in self.logs_dir.rglob(f"*{self.today}*"):
                if log_file.is_file() and log_file.suffix in ['.csv', '.json', '.log']:
                    # Zachowaj strukturę folderów
                    rel_path = log_file.relative_to(self.logs_dir)
                    archive_path = archive_dir / rel_path
                    archive_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    shutil.copy2(log_file, archive_path)
                    stats['archived_files'] += 1
                    
                    if 'ml_ready' in str(log_file):
                        stats['ml_datasets'] += 1
                    
                    print(f"📦 {rel_path}")
        
        print(f"✅ ZARCHIWIZOWANO: {stats['archived_files']} plików")
        print(f"   📊 w tym ML datasets: {stats['ml_datasets']}")
        
        # Po archiwizacji - wyczyść sesję
        clean_stats = self.clean_session_only()
        stats.update(clean_stats)
        
        return stats
    
    def clean_old_archives(self, days_old: int = 30) -> Dict[str, int]:
        """Usuń archiwa starsze niż N dni"""
        archive_root = self.project_root / "archive"
        if not archive_root.exists():
            return {'removed_archives': 0}
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        removed_count = 0
        
        print(f"🗂️ CZYSZCZENIE STARYCH ARCHIWÓW (>{days_old} dni)")
        print("-" * 50)
        
        for archive_dir in archive_root.iterdir():
            if archive_dir.is_dir():
                # Sprawdź czy nazwa to data YYYYMMDD
                match = re.match(r'(\\d{8})', archive_dir.name)
                if match:
                    try:
                        archive_date = datetime.strptime(match.group(1), '%Y%m%d')
                        if archive_date < cutoff_date:
                            shutil.rmtree(archive_dir)
                            removed_count += 1
                            print(f"🗑️ Usunięto archiwum: {archive_dir.name}")
                    except ValueError:
                        continue
        
        print(f"✅ Usunięto {removed_count} starych archiwów")
        return {'removed_archives': removed_count}
    
    def get_ml_stats(self) -> Dict[str, any]:
        """Pokaż statystyki danych ML"""
        ml_dir = self.logs_dir / "analysis" / "ml_ready"
        if not ml_dir.exists():
            return {'status': 'brak_danych_ml'}
        
        stats = {
            'csv_files': 0,
            'meta_files': 0, 
            'total_size_kb': 0,
            'datasets': []
        }
        
        for file in ml_dir.glob("*.csv"):
            stats['csv_files'] += 1
            stats['total_size_kb'] += file.stat().st_size / 1024
            
            # Szukaj odpowiadającego pliku meta
            meta_file = file.with_name(f"{file.stem}_meta.json")
            if meta_file.exists():
                stats['meta_files'] += 1
                try:
                    meta_data = json.loads(meta_file.read_text(encoding='utf-8'))
                    stats['datasets'].append({
                        'name': file.stem,
                        'records': meta_data.get('rozmiar_datasetu', 0),
                        'features': meta_data.get('liczba_cech', 0),
                        'size_kb': file.stat().st_size / 1024
                    })
                except:
                    pass
        
        return stats
    
    def _clean_purchased_tokens(self) -> int:
        """Pomocnicza - czyść zakupione żetony"""
        tokens_dir = self.project_root / "assets" / "tokens"
        deleted = 0
        
        if tokens_dir.exists():
            # Usuń foldery nowe_dla_*
            for folder in tokens_dir.glob("nowe_dla_*"):
                if folder.is_dir():
                    shutil.rmtree(folder)
                    deleted += 1
                    print(f"✅ Folder żetonów: {folder.name}")
            
            # Usuń pliki nowy_* z aktualne/
            aktualne_dir = tokens_dir / "aktualne"
            if aktualne_dir.exists():
                for file in aktualne_dir.glob("nowy_*"):
                    file.unlink()
                    deleted += 1
                    print(f"✅ Żeton: {file.name}")
        
        # Czyść z index.json
        index_path = self.project_root / "assets" / "tokens" / "index.json"
        if index_path.exists():
            try:
                index_data = json.loads(index_path.read_text(encoding='utf-8'))
                cleaned = [t for t in index_data if not t.get("id", "").startswith("nowy_")]
                if len(cleaned) < len(index_data):
                    index_path.write_text(json.dumps(cleaned, indent=2, ensure_ascii=False), encoding='utf-8')
                    print(f"✅ Index: usunięto {len(index_data) - len(cleaned)} żetonów")
            except:
                pass
        
        return deleted


# Funkcje dla kompatybilności z istniejącym systemem
def smart_clean_session():
    """Czyszczenie sesyjne - zachowaj ML"""
    cleaner = SmartLogCleaner()
    return cleaner.clean_session_only()

def smart_clean_full():
    """Pełne czyszczenie - zachowaj ML"""  
    cleaner = SmartLogCleaner()
    return cleaner.clean_preserve_ml()

def smart_archive_and_clean():
    """Archiwizuj i wyczyść"""
    cleaner = SmartLogCleaner()
    return cleaner.archive_session()

def show_ml_status():
    """Pokaż status danych ML"""
    cleaner = SmartLogCleaner()
    stats = cleaner.get_ml_stats()
    
    print("📊 STATUS DANYCH ML")
    print("-" * 30)
    if stats.get('status') == 'brak_danych_ml':
        print("❌ Brak danych ML")
        return
    
    print(f"📄 Plików CSV: {stats['csv_files']}")
    print(f"📋 Plików meta: {stats['meta_files']}")
    print(f"💾 Rozmiar: {stats['total_size_kb']:.1f} KB")
    print("📊 Datasety:")
    
    for ds in stats['datasets']:
        print(f"  • {ds['name']}: {ds['records']} rekordów, {ds['features']} cech ({ds['size_kb']:.1f} KB)")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Inteligentne czyszczenie logów')
    parser.add_argument('--mode', choices=['session', 'full', 'archive', 'old_archives', 'ml_status'], 
                       default='session')
    parser.add_argument('--days', type=int, default=30, help='Dni dla old_archives')
    
    args = parser.parse_args()
    
    cleaner = SmartLogCleaner()
    
    if args.mode == 'session':
        cleaner.clean_session_only()
    elif args.mode == 'full':
        cleaner.clean_preserve_ml()
    elif args.mode == 'archive':
        cleaner.archive_session()
    elif args.mode == 'old_archives':
        cleaner.clean_old_archives(args.days)
    elif args.mode == 'ml_status':
        show_ml_status()