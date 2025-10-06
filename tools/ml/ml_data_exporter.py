"""
ML Data Exporter - Eksporter Danych do Uczenia Maszynowego
(ML Data Exporter for Machine Learning preprocessing)

Konwertuje logi gry na format odpowiedni do uczenia maszynowego,
z uwzględnieniem parametrów AI i analityki gry.
"""

from __future__ import annotations
import json
import csv
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import logging

from tools.experimental.game_log_manager import KategoriaLog, TagLog, get_game_log_manager
from utils.session_manager import LOGS_ROOT

@dataclass
class MLDataset:
    """Struktura datasetu ML (ML Dataset Structure)"""
    nazwa: str                    # dataset name
    opis: str                    # description
    cechy: List[str]             # features
    etykiety: List[str]          # labels
    dane_trenujace: pd.DataFrame # training data
    metadane: Dict[str, Any]     # metadata
    timestamp: str               # creation timestamp

class MLDataExporter:
    """
    Eksporter Danych ML - Przygotowuje dane z logów do uczenia maszynowego
    (ML Data Exporter - Prepares log data for machine learning)
    """
    
    def __init__(self, katalog_logow: Union[str, Path] = LOGS_ROOT,
                 katalog_wyjsciowy: Union[str, Path] = LOGS_ROOT / "analysis" / "ml_ready"):
        """
        Inicializacja eksportera ML
        
        Args:
            katalog_logow: Katalog z logami źródłowymi
            katalog_wyjsciowy: Katalog dla danych ML-ready
        """
        self.katalog_logow = Path(katalog_logow)
        self.katalog_wyjsciowy = Path(katalog_wyjsciowy)
        self.katalog_wyjsciowy.mkdir(parents=True, exist_ok=True)
        
        # Konfiguracja eksportera
        self.mapowanie_cech = self._utworz_mapowanie_cech()
        self.transformacje = self._utworz_transformacje()
        self.logger = logging.getLogger(__name__)
        
    def _utworz_mapowanie_cech(self) -> Dict[str, Dict[str, Any]]:
        """
        Mapowanie pól logów na cechy ML
        (Mapping log fields to ML features)
        """
        return {
            # Cechy czasowe (Temporal features)
            "tura": {
                "typ": "numeric",
                "opis": "Numer tury gry (game turn number)",
                "normalizacja": "minmax",
                "zakres": [1, 100]
            },
            "timestamp": {
                "typ": "datetime",
                "opis": "Znacznik czasowy akcji (action timestamp)",
                "transformacja": ["hour", "minute", "day_of_week"]
            },
            
            # Cechy ekonomiczne (Economic features)
            "pe_start": {
                "typ": "numeric",
                "opis": "Punkty ekonomiczne na początku tury (PE at turn start)",
                "normalizacja": "standard"
            },
            "pe_allocated": {
                "typ": "numeric", 
                "opis": "Alokowane PE (allocated PE)",
                "normalizacja": "standard"
            },
            "pe_spent_purchases": {
                "typ": "numeric",
                "opis": "PE wydane na zakupy (PE spent on purchases)",
                "normalizacja": "standard"
            },
            
            # Cechy jednostek (Unit features)
            "unit_type": {
                "typ": "categorical",
                "opis": "Typ jednostki (unit type)",
                "encoding": "onehot",
                "kategorie": ["infantry", "armor", "artillery", "air", "naval"]
            },
            "mp_before": {
                "typ": "numeric",
                "opis": "Punkty ruchu przed akcją (movement points before action)",
                "normalizacja": "minmax",
                "zakres": [0, 10]
            },
            "fuel_before": {
                "typ": "numeric",
                "opis": "Paliwo przed akcją (fuel before action)",
                "normalizacja": "minmax",
                "zakres": [0, 100]
            },
            
            # Cechy taktyczne (Tactical features)
            "action_type": {
                "typ": "categorical",
                "opis": "Typ akcji (action type)",
                "encoding": "onehot",
                "kategorie": ["move", "attack", "defend", "supply", "deploy"]
            },
            "threat_level": {
                "typ": "numeric",
                "opis": "Poziom zagrożenia (threat level)",
                "normalizacja": "minmax",
                "zakres": [0, 10]
            },
            "aggression_level": {
                "typ": "numeric",
                "opis": "Poziom agresji AI (AI aggression level)",
                "normalizacja": "minmax",
                "zakres": [0, 1]
            },
            
            # Cechy pozycyjne (Positional features)
            "from_pos_q": {
                "typ": "numeric",
                "opis": "Pozycja Q źródłowa (source Q position)",
                "normalizacja": "minmax"
            },
            "from_pos_r": {
                "typ": "numeric", 
                "opis": "Pozycja R źródłowa (source R position)",
                "normalizacja": "minmax"
            },
            "distance": {
                "typ": "computed",
                "opis": "Dystans ruchu (movement distance)", 
                "formula": "sqrt((to_q - from_q)² + (to_r - from_r)²)"
            },
            
            # Cechy strategiczne (Strategic features)
            "strategic_state": {
                "typ": "categorical",
                "opis": "Stan strategiczny (strategic state)",
                "encoding": "label",
                "kategorie": ["defensive", "offensive", "neutral", "expanding"]
            },
            "decision": {
                "typ": "categorical",
                "opis": "Typ decyzji (decision type)",
                "encoding": "onehot"
            },
            
            # Etykiety do predykcji (Target labels)
            "combat_dmg_dealt": {
                "typ": "target",
                "opis": "Zadane obrażenia (damage dealt)",
                "zadanie": "regression"
            },
            "combat_success": {
                "typ": "target", 
                "opis": "Sukces walki (combat success)",
                "zadanie": "classification"
            },
            "strategy_effectiveness": {
                "typ": "target",
                "opis": "Skuteczność strategii (strategy effectiveness)",
                "zadanie": "regression"
            }
        }
    
    def _utworz_transformacje(self) -> Dict[str, callable]:
        """Funkcje transformacji danych"""
        return {
            "minmax": lambda x, min_val=0, max_val=1: (x - x.min()) / (x.max() - x.min()) * (max_val - min_val) + min_val,
            "standard": lambda x: (x - x.mean()) / x.std(),
            "log": lambda x: np.log1p(x),
            "onehot": lambda x: pd.get_dummies(x, prefix=x.name),
            "label": lambda x: pd.Categorical(x).codes
        }
    
    def wczytaj_logi_z_katalogu(self, kategoria: Optional[KategoriaLog] = None) -> pd.DataFrame:
        """
        Wczytuje wszystkie logi z określonej kategorii lub wszystkie
        
        Args:
            kategoria: Kategoria logów do wczytania (None = wszystkie)
            
        Returns:
            DataFrame z połączonymi logami
        """
        wszystkie_logi = []
        
        if kategoria:
            katalogi = [self.katalog_logow / kategoria.value]
        else:
            katalogi = [self.katalog_logow / kat.value for kat in KategoriaLog]
        
        for katalog in katalogi:
            if not katalog.exists():
                continue
                
            # Wczytaj pliki JSON
            for plik_json in katalog.glob("dane_*.json"):
                try:
                    with open(plik_json, 'r', encoding='utf-8') as f:
                        dane = json.load(f)
                    
                    for wpis in dane:
                        if wpis.get('ml_dane'):
                            wpis.update(wpis['ml_dane'])
                        wszystkie_logi.append(wpis)
                        
                except Exception as e:
                    self.logger.warning(f"Błąd wczytywania {plik_json}: {e}")
            
            # Wczytaj pliki CSV jako fallback
            for plik_csv in katalog.glob("dane_*.csv"):
                try:
                    df_csv = pd.read_csv(plik_csv)
                    for _, row in df_csv.iterrows():
                        # Parsuj JSON z kolumn
                        wpis = row.to_dict()
                        
                        if row.get('ml_dane_json'):
                            try:
                                ml_dane = json.loads(row['ml_dane_json'])
                                wpis.update(ml_dane)
                            except json.JSONDecodeError:
                                pass
                                
                        wszystkie_logi.append(wpis)
                        
                except Exception as e:
                    self.logger.warning(f"Błąd wczytywania {plik_csv}: {e}")
        
        return pd.DataFrame(wszystkie_logi) if wszystkie_logi else pd.DataFrame()
    
    def przygotuj_dataset_ai_decyzje(self) -> MLDataset:
        """
        Przygotowuje dataset do predykcji decyzji AI
        (Prepares dataset for AI decision prediction)
        """
        # Wczytaj logi AI
        df = self.wczytaj_logi_z_katalogu()
        df_ai = df[df['kategoria'].str.startswith('ai/')].copy()
        
        if df_ai.empty:
            return self._pusty_dataset("ai_decyzje", "Brak danych AI")
        
        # Przygotuj cechy
        cechy = []
        dane_przetworzone = pd.DataFrame()
        
        # Cechy podstawowe
        podstawowe_cechy = ['tura', 'pe_start', 'pe_allocated', 'threat_level', 'aggression_level']
        for cecha in podstawowe_cechy:
            if cecha in df_ai.columns:
                dane_przetworzone[cecha] = pd.to_numeric(df_ai[cecha], errors='coerce')
                cechy.append(cecha)
        
        # Cechy kategoryczne
        if 'action_type' in df_ai.columns:
            action_dummies = pd.get_dummies(df_ai['action_type'], prefix='action')
            dane_przetworzone = pd.concat([dane_przetworzone, action_dummies], axis=1)
            cechy.extend(action_dummies.columns.tolist())
        
        if 'strategic_state' in df_ai.columns:
            strategy_encoded = pd.Categorical(df_ai['strategic_state']).codes
            dane_przetworzone['strategic_state_encoded'] = strategy_encoded
            cechy.append('strategic_state_encoded')
        
        # Etykiety
        etykiety = []
        if 'decision' in df_ai.columns:
            dane_przetworzone['target_decision'] = pd.Categorical(df_ai['decision']).codes
            etykiety.append('target_decision')
        
        # Czyszczenie danych
        dane_przetworzone = dane_przetworzone.fillna(0)
        dane_przetworzone = dane_przetworzone.replace([np.inf, -np.inf], 0)
        
        return MLDataset(
            nazwa="ai_decyzje",
            opis="Dataset do predykcji decyzji AI na podstawie stanu gry (AI decision prediction dataset)",
            cechy=cechy,
            etykiety=etykiety,
            dane_trenujace=dane_przetworzone,
            metadane={
                "rozmiar_datasetu": len(dane_przetworzone),
                "liczba_cech": len(cechy),
                "liczba_etykiet": len(etykiety),
                "zakres_tur": [df_ai['tura'].min(), df_ai['tura'].max()] if 'tura' in df_ai.columns else [0, 0],
                "typy_akcji": df_ai['action_type'].unique().tolist() if 'action_type' in df_ai.columns else [],
                "opis_cech": {cecha: self.mapowanie_cech.get(cecha, {}).get('opis', '') for cecha in cechy}
            },
            timestamp=datetime.now().isoformat()
        )
    
    def przygotuj_dataset_skutecznosc_walki(self) -> MLDataset:
        """
        Przygotowuje dataset do predykcji skuteczności walki
        (Prepares dataset for combat effectiveness prediction)
        """
        df = self.wczytaj_logi_z_katalogu(KategoriaLog.AI_WALKA)
        
        if df.empty:
            return self._pusty_dataset("skutecznosc_walki", "Brak danych o walkach")
        
        # Filtruj wpisy z danymi o walce
        df_walka = df[df['combat_dmg_dealt'].notna()].copy()
        
        if df_walka.empty:
            return self._pusty_dataset("skutecznosc_walki", "Brak danych o obrażeniach")
        
        dane_przetworzone = pd.DataFrame()
        cechy = []
        
        # Cechy jednostek
        numeryczne_cechy = ['threat_level', 'mp_before', 'fuel_before', 'aggression_level']
        for cecha in numeryczne_cechy:
            if cecha in df_walka.columns:
                dane_przetworzone[cecha] = pd.to_numeric(df_walka[cecha], errors='coerce')
                cechy.append(cecha)
        
        # Typ jednostki
        if 'unit_type' in df_walka.columns:
            unit_dummies = pd.get_dummies(df_walka['unit_type'], prefix='unit')
            dane_przetworzone = pd.concat([dane_przetworzone, unit_dummies], axis=1)
            cechy.extend(unit_dummies.columns.tolist())
        
        # Etykiety
        etykiety = ['combat_dmg_dealt', 'combat_success']
        dane_przetworzone['combat_dmg_dealt'] = pd.to_numeric(df_walka['combat_dmg_dealt'], errors='coerce')
        dane_przetworzone['combat_success'] = (dane_przetworzone['combat_dmg_dealt'] > 0).astype(int)
        
        # Czyszczenie
        dane_przetworzone = dane_przetworzone.fillna(0)
        dane_przetworzone = dane_przetworzone.replace([np.inf, -np.inf], 0)
        
        return MLDataset(
            nazwa="skutecznosc_walki",
            opis="Dataset do predykcji skuteczności walki AI (AI combat effectiveness prediction dataset)",
            cechy=cechy,
            etykiety=etykiety,
            dane_trenujace=dane_przetworzone,
            metadane={
                "rozmiar_datasetu": len(dane_przetworzone),
                "srednie_obrazenia": dane_przetworzone['combat_dmg_dealt'].mean(),
                "procent_sukcesow": dane_przetworzone['combat_success'].mean(),
                "typy_jednostek": df_walka['unit_type'].unique().tolist() if 'unit_type' in df_walka.columns else [],
                "zakresy_cech": {
                    cecha: [dane_przetworzone[cecha].min(), dane_przetworzone[cecha].max()] 
                    for cecha in cechy if cecha in dane_przetworzone.columns and dane_przetworzone[cecha].dtype in ['int64', 'float64']
                }
            },
            timestamp=datetime.now().isoformat()
        )
    
    def przygotuj_dataset_ekonomia_ai(self) -> MLDataset:
        """
        Przygotowuje dataset do analizy ekonomii AI
        (Prepares dataset for AI economy analysis)
        """
        df = self.wczytaj_logi_z_katalogu(KategoriaLog.AI_GENERAL)
        df_ekonomia = df[df['pe_start'].notna()].copy()
        
        if df_ekonomia.empty:
            return self._pusty_dataset("ekonomia_ai", "Brak danych ekonomicznych")
        
        dane_przetworzone = pd.DataFrame()
        cechy = []
        
        # Cechy ekonomiczne
        ekonomiczne_cechy = ['pe_start', 'pe_allocated', 'pe_spent_purchases', 'tura']
        for cecha in ekonomiczne_cechy:
            if cecha in df_ekonomia.columns:
                dane_przetworzone[cecha] = pd.to_numeric(df_ekonomia[cecha], errors='coerce')
                cechy.append(cecha)
        
        # Efektywność ekonomiczna (obliczona cecha)
        if 'pe_start' in dane_przetworzone.columns and 'pe_spent_purchases' in dane_przetworzone.columns:
            dane_przetworzone['efficiency_ratio'] = dane_przetworzone['pe_spent_purchases'] / (dane_przetworzone['pe_start'] + 1)
            cechy.append('efficiency_ratio')
        
        # Strategia
        if 'strategy_used' in df_ekonomia.columns:
            strategy_dummies = pd.get_dummies(df_ekonomia['strategy_used'], prefix='strategy')
            dane_przetworzone = pd.concat([dane_przetworzone, strategy_dummies], axis=1)
            cechy.extend(strategy_dummies.columns.tolist())
        
        # Etykiety
        etykiety = ['pe_efficiency', 'strategy_success']
        dane_przetworzone['pe_efficiency'] = dane_przetworzone.get('efficiency_ratio', 0)
        dane_przetworzone['strategy_success'] = (dane_przetworzone['pe_efficiency'] > 0.5).astype(int)
        
        dane_przetworzone = dane_przetworzone.fillna(0)
        dane_przetworzone = dane_przetworzone.replace([np.inf, -np.inf], 0)
        
        return MLDataset(
            nazwa="ekonomia_ai",
            opis="Dataset do analizy efektywności ekonomicznej AI (AI economic efficiency analysis dataset)",
            cechy=cechy,
            etykiety=etykiety,
            dane_trenujace=dane_przetworzone,
            metadane={
                "rozmiar_datasetu": len(dane_przetworzone),
                "srednia_efektywnosc": dane_przetworzone['pe_efficiency'].mean(),
                "strategie_uzyte": df_ekonomia['strategy_used'].unique().tolist() if 'strategy_used' in df_ekonomia.columns else [],
                "zakres_pe": [df_ekonomia['pe_start'].min(), df_ekonomia['pe_start'].max()] if 'pe_start' in df_ekonomia.columns else [0, 0]
            },
            timestamp=datetime.now().isoformat()
        )
    
    def _pusty_dataset(self, nazwa: str, powod: str) -> MLDataset:
        """Tworzy pusty dataset z informacją o błędzie"""
        return MLDataset(
            nazwa=nazwa,
            opis=f"Pusty dataset: {powod}",
            cechy=[],
            etykiety=[],
            dane_trenujace=pd.DataFrame(),
            metadane={"error": powod, "rozmiar_datasetu": 0},
            timestamp=datetime.now().isoformat()
        )
    
    def exportuj_dataset(self, dataset: MLDataset, format: str = "wszystkie") -> List[Path]:
        """
        Eksportuje dataset w określonych formatach
        
        Args:
            dataset: Dataset do eksportu
            format: "csv", "json", "parquet", "wszystkie"
            
        Returns:
            Lista ścieżek do eksportowanych plików
        """
        pliki_wyjsciowe = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if dataset.dane_trenujace.empty:
            self.logger.warning(f"Dataset {dataset.nazwa} jest pusty - pomijam eksport")
            return pliki_wyjsciowe
        
        # CSV
        if format in ["csv", "wszystkie"]:
            plik_csv = self.katalog_wyjsciowy / f"{dataset.nazwa}_{timestamp}.csv"
            dataset.dane_trenujace.to_csv(plik_csv, index=False, encoding='utf-8')
            pliki_wyjsciowe.append(plik_csv)
        
        # JSON  
        if format in ["json", "wszystkie"]:
            plik_json = self.katalog_wyjsciowy / f"{dataset.nazwa}_{timestamp}.json"
            with open(plik_json, 'w', encoding='utf-8') as f:
                json.dump(asdict(dataset), f, ensure_ascii=False, indent=2, default=str)
            pliki_wyjsciowe.append(plik_json)
        
        # Parquet (jeśli pandas ma wsparcie)
        if format in ["parquet", "wszystkie"]:
            try:
                plik_parquet = self.katalog_wyjsciowy / f"{dataset.nazwa}_{timestamp}.parquet"
                dataset.dane_trenujace.to_parquet(plik_parquet, index=False)
                pliki_wyjsciowe.append(plik_parquet)
            except ImportError:
                self.logger.warning("Parquet nie jest dostępny - pomijam")
        
        # Metadane osobno
        plik_meta = self.katalog_wyjsciowy / f"{dataset.nazwa}_{timestamp}_meta.json"
        with open(plik_meta, 'w', encoding='utf-8') as f:
            json.dump(dataset.metadane, f, ensure_ascii=False, indent=2, default=str)
        pliki_wyjsciowe.append(plik_meta)
        
        self.logger.info(f"Eksportowano dataset {dataset.nazwa} ({len(pliki_wyjsciowe)} plików)")
        return pliki_wyjsciowe
    
    def generuj_wszystkie_datasety(self) -> Dict[str, MLDataset]:
        """
        Generuje wszystkie dostępne datasety ML
        
        Returns:
            Słownik z datasetami
        """
        datasety = {}
        
        try:
            datasety["ai_decyzje"] = self.przygotuj_dataset_ai_decyzje()
        except Exception as e:
            self.logger.error(f"Błąd generowania datasetu ai_decyzje: {e}")
            
        try:
            datasety["skutecznosc_walki"] = self.przygotuj_dataset_skutecznosc_walki()
        except Exception as e:
            self.logger.error(f"Błąd generowania datasetu skutecznosc_walki: {e}")
            
        try:
            datasety["ekonomia_ai"] = self.przygotuj_dataset_ekonomia_ai()
        except Exception as e:
            self.logger.error(f"Błąd generowania datasetu ekonomia_ai: {e}")
        
        return datasety
    
    def exportuj_wszystkie_datasety(self, format: str = "wszystkie") -> Dict[str, List[Path]]:
        """
        Eksportuje wszystkie datasety
        
        Args:
            format: Format eksportu
            
        Returns:
            Słownik {nazwa_datasetu: [lista_plików]}
        """
        datasety = self.generuj_wszystkie_datasety()
        wyniki = {}
        
        for nazwa, dataset in datasety.items():
            wyniki[nazwa] = self.exportuj_dataset(dataset, format)
        
        # Podsumowanie
        plik_podsumowania = self.katalog_wyjsciowy / f"ml_export_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        podsumowanie = {
            "timestamp": datetime.now().isoformat(),
            "datasety": {
                nazwa: {
                    "rozmiar": dataset.metadane.get("rozmiar_datasetu", 0),
                    "cechy": len(dataset.cechy),
                    "pliki": [str(p) for p in pliki]
                }
                for nazwa, (dataset, pliki) in zip(datasety.keys(), [(datasety[k], wyniki[k]) for k in wyniki])
            },
            "lacznie_datasety": len(datasety),
            "lacznie_pliki": sum(len(pliki) for pliki in wyniki.values())
        }
        
        with open(plik_podsumowania, 'w', encoding='utf-8') as f:
            json.dump(podsumowanie, f, ensure_ascii=False, indent=2)
        
        return wyniki

# Export głównych klas
__all__ = ['MLDataExporter', 'MLDataset']