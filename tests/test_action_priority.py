import pytest
from app.services.pfmea_service import calculate_action_priority


@pytest.mark.parametrize(
    "s, o, d, expected",
    [
        # Severity 9-10
        (10, 10, 10, "H"),
        (9, 6, 8, "H"),
        (10, 5, 2, "H"),
        (9, 4, 1, "M"),
        (10, 3, 7, "H"),
        (9, 2, 4, "M"),
        (10, 1, 7, "H"),
        (9, 1, 5, "M"),
        (10, 1, 3, "L"),
        # Severity 7-8
        (8, 9, 8, "H"),
        (7, 7, 2, "H"),
        (8, 6, 1, "M"),
        (7, 5, 5, "H"),
        (8, 4, 3, "M"),
        (7, 3, 8, "M"),
        (8, 2, 4, "L"),
        (7, 1, 9, "M"),
        (8, 1, 4, "L"),
        # Severity 4-6
        (6, 10, 8, "H"),
        (5, 8, 1, "M"),
        (4, 7, 6, "H"),
        (6, 6, 3, "M"),
        (5, 5, 8, "H"),
        (4, 4, 5, "M"),
        (6, 4, 1, "L"),
        (5, 3, 9, "M"),
        (4, 2, 3, "L"),
        (6, 1, 8, "M"),
        (5, 1, 4, "L"),
        # Severity 2-3
        (3, 10, 9, "M"),
        (2, 8, 1, "L"),
        (3, 7, 5, "M"),
        (2, 6, 4, "L"),
        (3, 5, 8, "M"),
        (2, 4, 2, "L"),
        (3, 3, 10, "L"),
        (2, 1, 6, "L"),
        # Severity 1
        (1, 10, 10, "L"),
        (1, 5, 5, "L"),
        (1, 1, 1, "L"),
    ],
)
def test_calculate_action_priority(s, o, d, expected):
    assert calculate_action_priority(s, o, d) == expected


def test_all_shared_combinations():
    import json
    from pathlib import Path

    data = json.loads(
        (
            Path(__file__).resolve().parents[1] / "app/data/action_priority.json"
        ).read_text()
    )
    assert len(data) == 1000
    for key, expected in data.items():
        s, o, d = map(int, key.split(","))
        assert calculate_action_priority(s, o, d) == expected


@pytest.mark.parametrize("values", [(0, 1, 1), (1, 11, 1), (1, 1, 0), (1.5, 2, 3)])
def test_invalid_ratings_rejected(values):
    with pytest.raises(ValueError):
        calculate_action_priority(*values)
