#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SZCZEGÓŁOWY WPŁYW PROFILI AI NA ZACHOWANIE GENERAŁA
==================================================

🎯 KRÓTKIEJ ODPOWIEDŹ NA PYTANIE:

Wybór profilu dla Generała wpływa na WSZYSTKIE ASPEKTY jego strategii:
- 💰 Ekonomię i budżet
- 🎯 Strategię (priorytety VP vs ekonomia)  
- 📍 Deployment (gdzie wysyła jednostki)
- ⚔️ Combat (kiedy i jak atakuje)
- 🚛 Logistykę (zaopatrzenie)

═══════════════════════════════════════════════════════════════════

🔥 AGGRESSIVE GENERAŁ (próg ataku 0.6):

💰 EKONOMIA:
- MIN_BUY: 21 zamiast 30 (kupuje jednostki już przy 21 punktach)
- BUDGET_STRATEGIES.EKSPANSJA.purchase: +20% na zakupy wojskowe
- BUDGET_STRATEGIES.EKSPANSJA.reserve: -50% rezerwy (ryzykuje więcej)

🎯 STRATEGIA:
- STRATEGY_MULTIPLIERS.victory_points: 1.3x (priorytet VP nad ekonomią!)
- STRATEGY_MULTIPLIERS.economy: 0.8x (mniej dbałości o ekonomię)

📍 DEPLOYMENT:
- DEFAULT_VP_WEIGHT: 1.5x (+50% waga punktów zwycięstwa)
- DEFAULT_ECON_WEIGHT: 0.8x (-20% waga ekonomii)
- Wysyła jednostki agresywnie na VP zamiast chronić ekonomię

⚔️ COMBAT:
- COUNTER_ATTACK_MAX_PENALTY: 0.4 (mniejszy strach przed kontatakiem)
- THREAT_RETREAT_THRESHOLD: 7 (wyższy próg odwrotu - rzadziej ucieka)
- MINIMUM_ATTACK_RATIO: 0.6 (atakuje przy 60% przewagi zamiast 120%!)

🚛 LOGISTYKA:
- MAX_UNITS_PER_TURN: 1.5x (kupuje 3 jednostki zamiast 2)
- PURCHASES.artillery.max_ratio: 1.2x (+20% artylerii)

═══════════════════════════════════════════════════════════════════

🛡️ DEFENSIVE GENERAŁ (próg ataku 1.4):

💰 EKONOMIA:
- MIN_ALLOCATE: 1.3x (alokuje więcej - 78 zamiast 60)
- BUDGET_STRATEGIES.OCHRONA.reserve: +50% rezerwy (ostrożność)
- BUDGET_STRATEGIES.OCHRONA.purchase: -30% na zakupy (oszczędność)

🎯 STRATEGIA:
- STRATEGY_MULTIPLIERS.economy: 1.5x (priorytet ekonomii!)
- STRATEGY_MULTIPLIERS.victory_points: 0.7x (mniej agresji na VP)

📍 DEPLOYMENT:
- DEFAULT_ECON_WEIGHT: 1.4x (+40% waga ekonomii)
- DEFAULT_VP_WEIGHT: 0.6x (-40% waga VP)
- GARRISON_LIMITS.default: 1.5x (większe garnizony)
- Koncentruje się na obronie ekonomii, nie ekspansji

⚔️ COMBAT:
- THREAT_RETREAT_THRESHOLD: 3 (niski próg - szybko się wycofuje)
- KEYPOINT_DEFENSE_RANGE: 1.5x (większy zasięg obrony)
- MINIMUM_ATTACK_RATIO: 1.4 (atakuje dopiero przy 140% przewagi!)

🚛 LOGISTYKA:
- LOW_FUEL_UNITS_RATIO_TRIGGER: 0.8 (24% zamiast 30% - wcześniej tankuje)
- RESUPPLY_RATIOS.WOJNA: 1.1x (+10% na resupply)

═══════════════════════════════════════════════════════════════════

🎯 BALANCED GENERAŁ (próg ataku 1.0):

Wszystkie parametry = 1.0 (standardowe wartości)
- Zbalansowane podejście do wszystkich aspektów
- MINIMUM_ATTACK_RATIO: 1.0 (atakuje przy 100% przewagi)
- Uniwersalny styl, adaptuje się do sytuacji

═══════════════════════════════════════════════════════════════════

🎮 PRAKTYCZNE RÓŻNICE W GRE:

🔥 AGGRESSIVE GENERAŁ:
✅ Szybko ekspanduje na VP
✅ Kupuje dużo jednostek bojowych
✅ Atakuje przy małej przewadze (0.6)
✅ Ryzykuje ekonomią dla szybkich zwycięstw
❌ Może zostać bez rezerw ekonomicznych
❌ Jednostki mogą być niedozaopatrzone

🛡️ DEFENSIVE GENERAŁ:
✅ Buduje silną ekonomię
✅ Duże garnizony i rezerwy
✅ Lepsze zaopatrzenie jednostek
✅ Stabilna pozycja długoterminowa
❌ Powolna ekspansja na VP
❌ Może przegrywać przez pasywność

🎯 BALANCED GENERAŁ:
✅ Uniwersalność
✅ Adaptuje się do sytuacji
❌ Brak specjalizacji
❌ Może być przewidywalny

═══════════════════════════════════════════════════════════════════

🔍 JAK TO WYGLĄDA W PRAKTYCE:

SCENARIUSZ: Walka o miasto strategiczne

🔥 AGGRESSIVE: 
- Atakuje natychmiast przy 60% przewagi
- Kupuje artilerię do wsparcia (+20%)  
- Alokuje wszystkie środki na atak
- Ryzykuje straty dla szybkiego zwycięstwa

🛡️ DEFENSIVE:
- Czeka na 140% przewagi przed atakiem
- Buduje większy garnizon w pobliskich miastach
- Zachowuje rezerwy ekonomiczne
- Koncentruje się na obronie własnych pozycji

🎯 BALANCED:
- Atakuje przy 100% przewagi  
- Standardowa alokacja środków
- Balansuje między atakiem a obroną

═══════════════════════════════════════════════════════════════════

💡 WNIOSEK:

Profile AI wpływają na KOMPLEKSOWE zachowanie Generała:
- 💰 Jak zarządza ekonomią i budżetem
- 🎯 Jakie ma priorytety strategiczne (VP vs ekonomia)
- 📍 Gdzie i jak rozmieszcza jednostki
- ⚔️ Kiedy i jak prowadzi walki
- 🚛 Jak dba o zaopatrzenie

To nie tylko zmiana progu ataku - to kompletnie inny STYL GRY!
"""

if __name__ == "__main__":
    print(__doc__)