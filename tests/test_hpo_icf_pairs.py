"""HPO->ICF explicit code pairs have one source of truth (bridges.HPO_ICF_PAIRS)."""
from pathlib import Path

import bridges

ROOT = Path(__file__).resolve().parent.parent


def test_pair_count_and_uniqueness():
    assert len(bridges.HPO_ICF_PAIRS) == 9
    assert len(set(bridges.HPO_ICF_PAIRS)) == 9


def test_gait_terms_map_to_gait_pattern_functions():
    pairs = set(bridges.HPO_ICF_PAIRS)
    assert ("HP:0002066", "b770") in pairs  # Gait ataxia
    assert ("HP:0001288", "b770") in pairs  # Gait disturbance


def test_known_bad_pairs_stay_removed():
    pairs = set(bridges.HPO_ICF_PAIRS)
    for bad in [("HP:0002093", "d450"), ("HP:0001250", "b235"),
                ("HP:0002066", "b455"), ("HP:0001252", "b130")]:
        assert bad not in pairs


def test_loaders_use_shared_pairs_not_local_copies():
    for name in ("add_additional_data.py", "build_csvs.py"):
        text = (ROOT / name).read_text()
        assert '"HP:0002066"' not in text, f"{name} has a local copy of the pairs"
