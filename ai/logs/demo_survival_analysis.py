"""Demo analizy przetrwania jednostek z 1 CV.

Symuluje dane z wcześniejszej sesji do przetestowania mechaniki.
"""
from raport_starcia import PlayerStats, analyze_survival_mechanics

# Symulacja Human stats
human = PlayerStats(player_name="Polska", player_type="HUMAN", nation="Polska")

# Symulacja ataków na jednostkę niemiecką TŚ_Batalion__6_Panzer_Regiment
# która wielokrotnie przetrwała z 1 CV

human.attack_details = [
    # Tura 1, Atak 1 - sprowadzenie do 1 CV
    {
        "turn": 1,
        "attacker": "TŚ_Batalion__2_Pluton_Czo_g_w",
        "defender": "TŚ_Batalion__6_Panzer_Regiment",
        "success": True,
        "damage_dealt": 29,
        "damage_taken": 27,
        "counterattack": True,
        "attacker_cv_before": 14,
        "attacker_cv_after": 14,
        "defender_cv_before": 30,  # Pełne HP
        "defender_cv_after": 1,    # PRZETRWAŁ!
        "defender_position_before": (32, -5),
        "defender_position_after": (32, -5),  # Nie wycofał się jeszcze
    },
    # Tura 1, Atak 2 - kolejny atak na tę samą jednostkę z 1 CV
    {
        "turn": 1,
        "attacker": "TŚ_Batalion__2_Pluton_Czo_g_w_20251009173147",
        "defender": "TŚ_Batalion__6_Panzer_Regiment",
        "success": True,
        "damage_dealt": 29,
        "damage_taken": 27,
        "counterattack": True,
        "attacker_cv_before": 14,
        "attacker_cv_after": 14,
        "defender_cv_before": 1,   # Już był na 1 CV
        "defender_cv_after": 1,    # ZNOWU PRZETRWAŁ! (szczęściarz)
        "defender_position_before": (32, -5),
        "defender_position_after": (31, -6),  # WYCOFAŁ SIĘ!
    },
    # Tura 2 - jednostka odzyskała CV (uzupełnienie)
    {
        "turn": 2,
        "attacker": "P_Batalion__2_Pu_k_Piechoty",
        "defender": "TŚ_Batalion__6_Panzer_Regiment",
        "success": True,
        "damage_dealt": 12,
        "damage_taken": 8,
        "counterattack": True,
        "attacker_cv_before": 11,
        "attacker_cv_after": 3,
        "defender_cv_before": 16,  # ODZYSKAŁ CV! (z 1 do 16)
        "defender_cv_after": 4,
        "defender_position_before": (31, -6),
        "defender_position_after": (31, -6),
    },
    # Tura 2 - kolejny atak, znowu sprowadzenie do 1 CV
    {
        "turn": 2,
        "attacker": "TŚ_Batalion__2_Pluton_Czo_g_w",
        "defender": "TŚ_Batalion__6_Panzer_Regiment",
        "success": True,
        "damage_dealt": 30,
        "damage_taken": 35,
        "counterattack": True,
        "attacker_cv_before": 14,
        "attacker_cv_after": 14,
        "defender_cv_before": 4,
        "defender_cv_after": 1,    # TRZECI RAZ Z 1 CV!
        "defender_position_before": (31, -6),
        "defender_position_after": (30, -7),  # Znowu się wycofał
    },
    # Tura 3 - jednostka znowu odzyskała CV
    {
        "turn": 3,
        "attacker": "TL_Batalion__2_Kompania_Czo_g_w_Lekkich",
        "defender": "TŚ_Batalion__6_Panzer_Regiment",
        "success": True,
        "damage_dealt": 18,
        "damage_taken": 15,
        "counterattack": True,
        "attacker_cv_before": 10,
        "attacker_cv_after": 10,
        "defender_cv_before": 8,   # DRUGIE ODZYSKANIE! (z 1 do 8)
        "defender_cv_after": 1,    # CZWARTY RAZ z 1 CV!!!
        "defender_position_before": (30, -7),
        "defender_position_after": (29, -7),  # Kolejne wycofanie
    },
    # Inna jednostka - K_Batalion__5_Kavaleria_Einheit
    {
        "turn": 1,
        "attacker": "TŚ_Batalion__2_Pluton_Czo_g_w_20251009173147",
        "defender": "K_Batalion__5_Kavaleria_Einheit",
        "success": True,
        "damage_dealt": 29,
        "damage_taken": 13,
        "counterattack": True,
        "attacker_cv_before": 14,
        "attacker_cv_after": 14,
        "defender_cv_before": 8,
        "defender_cv_after": 1,    # Też przetrwał z 1 CV (raz)
        "defender_position_before": (33, -4),
        "defender_position_after": (33, -4),
    },
]

# AI stats (puste dla tego demo)
ai = PlayerStats(player_name="Niemcy", player_type="AI", nation="Niemcy")

# Uruchom analizę
print("🔍 ANALIZA PRZETRWANIA JEDNOSTEK Z 1 CV\n")
print("=" * 70)

survival_data = analyze_survival_mechanics(human, ai)

# Wyniki
print("\n🎲 CUDOWNE PRZETRWANIA (wielokrotnie z 1 CV):")
if survival_data["miraculous_survivals"]:
    for miracle in survival_data["miraculous_survivals"]:
        print(f"\n📍 {miracle['unit']}")
        print(f"   Przetrwał z 1 CV: {miracle['survivals']} razy!")
        print(f"   Odzyskał CV: {'TAK ✅' if miracle['recovered'] else 'NIE ❌'}")
        print(f"   Wycofał się: {'TAK ✅' if miracle['retreated'] else 'NIE ❌'}")
else:
    print("   Brak")

print("\n💚 ODZYSKANIE CV:")
if survival_data["cv_recoveries"]:
    for recovery in survival_data["cv_recoveries"]:
        print(f"   {recovery['unit']} (tura {recovery['turn']}): "
              f"{recovery['recovered_from']} CV → {recovery['recovered_to']} CV")
else:
    print("   Brak")

print("\n🏃 WYCOFANIA PO OBRAŻENIACH:")
if survival_data["retreat_after_damage"]:
    for retreat in survival_data["retreat_after_damage"]:
        print(f"   {retreat['unit']} (tura {retreat['turn']}, CV={retreat['cv_after']}): "
              f"{retreat['from']} → {retreat['to']}")
else:
    print("   Brak")

print(f"\n📊 WSZYSTKIE PRZYPADKI 1 CV: {len(survival_data['units_with_1cv'])}")
for i, case in enumerate(survival_data['units_with_1cv'], 1):
    print(f"   {i}. Tura {case['turn']}: {case['unit']} "
          f"({case['damage']} dmg od {case['attacker']})")

print("\n" + "=" * 70)
print("\n✅ WNIOSKI:")
print("\n1. TŚ_Batalion__6_Panzer_Regiment przetrwał 4 razy z 1 CV!")
print("2. Jednostka DWUKROTNIE odzyskała CV (z 1 do 16, potem z 1 do 8)")
print("3. Jednostka TRZYKROTNIE się wycofała po otrzymaniu obrażeń")
print("\n🎯 TO WSKAZUJE NA:")
print("   • Mechanikę 'lucky survival' działa (losowanie przy 1 CV)")
print("   • AI skutecznie uzupełnia CV jednostkom z 1 CV")
print("   • AI poprawnie wycofuje uszkodzone jednostki")
print("\n⚠️ PYTANIE: Czy to zamierzone zachowanie czy bug?")
print("   • 4 razy przetrwać z 1 CV to bardzo wysokie prawdopodobieństwo")
print("   • Może warto sprawdzić czy mechanika 'finish off' działa?")
