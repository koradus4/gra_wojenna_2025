# -*- coding: utf-8 -*-
"""
Konfiguracja dla polskojęzycznego systemu logowania AI Commander
"""

# 🇵🇱 POLSKIE NAZWY PLIKÓW
NAZWY_PLIKOW = {
    'strategiczne': 'decyzje_strategiczne',
    'taktyczne': 'akcje_taktyczne',
    'ekonomiczne': 'decyzje_ekonomiczne',
    'wywiad': 'analiza_wywiadu',
    'wydajnosc': 'wydajnosc_ai',
    'zwyciestwo': 'analiza_zwyciestwa'
}

# 🗺️ MAPOWANIE KOLUMN ANGIELSKI -> POLSKI
POLISH_COLUMN_MAPPING = {
    'timestamp': 'data_czas',
    'turn': 'tura',
    'phase': 'faza',
    'nation': 'nacja',
    'decision_type': 'typ_decyzji',
    'decision_scope': 'zakres_decyzji',
    'priority_level': 'priorytet',
    'context_factors': 'czynniki_kontekstu',
    'expected_outcome': 'oczekiwany_efekt',
    'actual_outcome': 'rzeczywisty_efekt',
    'confidence_level': 'poziom_pewnosci',
    'time_horizon': 'horyzont_czasowy',
    'resource_commitment': 'zaangazowane_zasoby',
    'alternative_considered': 'rozwazone_alternatywy',
    'decision_rationale': 'uzasadnienie_decyzji',
    'risk_assessment': 'ocena_ryzyka',
    'success_probability': 'prawdopodobienstwo_sukcesu',
    'strategic_goal_alignment': 'zgodnosc_ze_strategia',
    'vp_impact_projection': 'przewidywany_wplyw_vp',
    'economic_impact': 'wplyw_ekonomiczny',
    'action_category': 'kategoria_akcji',
    'unit_primary': 'jednostka_glowna',
    'units_supporting': 'jednostki_wspierajace',
    'action_complexity': 'zlozonsc_akcji',
    'coordination_required': 'wymagana_koordynacja',
    'formation_type': 'typ_formacji',
    'terrain_advantage': 'przewaga_terenu',
    'enemy_response_expected': 'oczekiwana_reakcja_wroga',
    'success_indicators': 'wskazniki_sukcesu',
    'execution_time_ms': 'czas_wykonania_ms',
    'micro_decisions_count': 'liczba_mikro_decyzji',
    'unit_synergy_score': 'wspolpraca_jednostek',
    'tactical_innovation': 'innowacja_taktyczna',
    'risk_mitigation': 'ograniczenie_ryzyka',
    'fallback_plan_ready': 'plan_awaryjny_gotowy',
    'budget_available': 'dostepny_budzet',
    'budget_allocated': 'przydzielony_budzet',
    'spending_category': 'kategoria_wydatkow',
    'cost_per_action': 'koszt_na_akcje',
    'expected_roi': 'oczekiwany_zwrot',
    'actual_roi': 'rzeczywisty_zwrot',
    'opportunity_cost': 'koszt_alternatywny',
    'budget_pressure_level': 'presja_budzetowa',
    'pe_efficiency_score': 'efektywnosc_pe',
    'resource_scarcity_factor': 'niedobor_zasobow',
    'emergency_spending': 'wydatki_awaryjne',
    'investment_horizon': 'horyzont_inwestycji',
    'cost_benefit_analysis': 'analiza_koszt_korzysci',
    'budget_variance': 'odchylenie_budzetowe',
    'economic_strategy_alignment': 'zgodnosc_ze_strategia_ekonomiczna',
    'intelligence_type': 'typ_informacji',
    'source_reliability': 'wiarygodnosc_zrodla',
    'information_freshness': 'swiezosc_informacji',
    'enemy_units_spotted': 'wykryte_jednostki_wroga',
    'enemy_movements_predicted': 'przewidziane_ruchy_wroga',
    'threat_assessment_change': 'zmiana_oceny_zagrozenia',
    'counter_intelligence_detected': 'wykryty_kontrwywiad',
    'strategic_surprise_probability': 'prawdopodobienstwo_niespodzianki',
    'information_gaps': 'luki_informacyjne',
    'intel_confidence_level': 'poziom_pewnosci_wywiadu',
    'actionable_intelligence': 'przydatne_informacje',
    'intelligence_sharing': 'wymiana_informacji',
    'prediction_accuracy_historical': 'dokladnosc_przewidywan_historyczna',
    'enemy_pattern_recognition': 'rozpoznanie_wzorcow_wroga',
    'deception_likelihood': 'prawdopodobienstwo_oszustwa',
    'decision_latency_ms': 'opoznienie_decyzji_ms',
    'calculations_performed': 'wykonane_obliczenia',
    'algorithms_used': 'uzyte_algorytmy',
    'memory_usage_mb': 'zuzycie_pamieci_mb',
    'cpu_utilization_pct': 'wykorzystanie_cpu_proc',
    'decision_tree_depth': 'glebokosc_drzewa_decyzji',
    'alternatives_evaluated': 'ocenione_alternatywy',
    'optimization_iterations': 'iteracje_optymalizacji',
    'ai_confidence_score': 'pewnosc_ai',
    'learning_rate_applied': 'zastosowana_szybkosc_uczenia',
    'model_accuracy_current': 'obecna_dokladnosc_modelu',
    'prediction_success_rate': 'wskaznik_sukcesu_przewidywan',
    'adaptive_behavior_triggered': 'wyzwolone_zachowanie_adaptacyjne',
    'error_recovery_attempts': 'proby_odzyskania_po_bledzie',
    'system_stability_index': 'wskaznik_stabilnosci_systemu',
    'vp_trajectory': 'trajektoria_vp',
    'vp_gap_analysis': 'analiza_luki_vp',
    'victory_probability': 'prawdopodobienstwo_zwyciestwa',
    'path_to_victory_identified': 'zidentyfikowana_sciezka_zwyciestwa',
    'victory_conditions_progress': 'postep_warunkow_zwyciestwa',
    'time_pressure_factor': 'czynnik_presji_czasu',
    'endgame_strategy_active': 'aktywna_strategia_koncowki',
    'victory_point_opportunities': 'mozliwosci_punktow_zwyciestwa',
    'elimination_targets_priority': 'priorytety_celow_eliminacji',
    'key_points_strategic_value': 'wartosc_strategiczna_kluczowych_punktow',
    'victory_timeline_projection': 'przewidywany_harmonogram_zwyciestwa',
    'defeat_risk_assessment': 'ocena_ryzyka_porazki'
}

# 🎯 TYPY DECYZJI STRATEGICZNYCH
TYPY_DECYZJI_STRATEGICZNYCH = {
    'Ofensywa_Agresywna': 'Rozpoczęcie wielkiego natarcia',
    'Przejscie_Do_Obrony': 'Zajęcie pozycji obronnych',
    'Zmiana_Obszaru_Koncentracji': 'Przekierowanie głównych sił',
    'Przegrupowanie_Zasobow': 'Przekierowanie sił do innego obszaru',
    'Wycofanie_I_Konsolidacja': 'Strategiczne wycofanie',
    'Ekspansja_Kontroli': 'Rozszerzenie strefy kontroli',
    'Konsolidacja_Pozycji': 'Umocnienie obecnych pozycji'
}

# 🎖️ KATEGORIE AKCJI TAKTYCZNYCH
KATEGORIE_AKCJI_TAKTYCZNYCH = {
    'Skoordynowany_Atak': 'Wspólny atak kilku jednostek',
    'Manewr_Oskrzydlajacy': 'Obejście skrzydła przeciwnika',
    'Przygotowanie_Obrony': 'Zajęcie pozycji obronnych',
    'Rozpoznanie_Bojowe': 'Zbieranie informacji o wrogu',
    'Operacja_Zaopatrzeniowa': 'Dostarczanie zaopatrzenia',
    'Manewry_Odwrotu': 'Kontrolowane wycofanie',
    'Akcja_Dywersyjna': 'Działania zakłócające'
}

# 📊 POZIOMY PEWNOŚCI
POZIOMY_PEWNOSCI = {
    'Bardzo_Wysoki': '95-100%',
    'Wysoki': '80-94%',
    'Sredni': '60-79%',
    'Niski': '40-59%',
    'Bardzo_Niski': '0-39%'
}

# ⚔️ STAN STRATEGICZNY
STAN_STRATEGICZNY = {
    'Wygrywamy': 'Przewaga strategiczna',
    'Remis': 'Równowaga sił',
    'Przegrywamy': 'Sytuacja niekorzystna',
    'Niepewny': 'Stan niejednoznaczny'
}

# 💰 KATEGORIE WYDATKÓW
KATEGORIE_WYDATKOW = {
    'Ruch_Jednostek': 'Koszty przemieszczania',
    'Walka_Bezposrednia': 'Koszty ataków',
    'Zaopatrzenie': 'Koszty resupply',
    'Rozpoznanie': 'Koszty intelligence',
    'Obrona': 'Koszty umocnień',
    'Rezerwowa': 'Wydatki awaryjne'
}

# 🕵️ TYPY INFORMACJI WYWIADOWCZYCH
TYPY_INFORMACJI_WYWIAD = {
    'Ruch_Wroga': 'Obserwacja przemieszczeń przeciwnika',
    'Pozycje_Obronne': 'Identyfikacja umocnień',
    'Sily_Nieprzyjaciela': 'Ocena potencjału bojowego',
    'Intencje_Strategiczne': 'Przewidywanie planów wroga',
    'Slabe_Punkty': 'Identyfikacja podatności',
    'Zaopatrzenie_Wroga': 'Stan logistyczny przeciwnika'
}

# 🎯 KOMPLETNA KONFIGURACJA
POLISH_CONFIG = {
    'nazwy_plikow': NAZWY_PLIKOW,
    'nazwy_kolumn': POLISH_COLUMN_MAPPING,
    'wartosci_enum': {
        'poziomy_pewnosci': POZIOMY_PEWNOSCI,
        'stan_strategiczny': STAN_STRATEGICZNY,
        'typy_decyzji': TYPY_DECYZJI_STRATEGICZNYCH,
        'kategorie_akcji': KATEGORIE_AKCJI_TAKTYCZNYCH,
        'kategorie_wydatkow': KATEGORIE_WYDATKOW,
        'typy_wywiadu': TYPY_INFORMACJI_WYWIAD
    }
}