from balance.model import build_unit_names, UNIFIED_LABELS


def test_unified_labels_flag():
    assert UNIFIED_LABELS is True, "UNIFIED_LABELS powinno być True po wdrożeniu kroku D"


def test_label_equals_full_name_when_unified():
    if not UNIFIED_LABELS:
        return  # pomijamy gdy tryb wyłączony
    sample = build_unit_names("Polska", "P", "Pluton")
    assert sample["label"] == sample["unit_full_name"], "Label i unit_full_name muszą być identyczne w trybie unified"
    assert "short_label" in sample, "Powinien istnieć short_label jako alternatywa"
