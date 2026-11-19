import pytest

from research.baselines import persistence


def test_persistence_uses_only_the_prior_month():
    result = persistence([100.0, 200.0, 201.0, 199.0], holdout=2)
    assert result["mae"] == 1.5
    assert result["rmse"] == pytest.approx(2.5**0.5)


@pytest.mark.parametrize("values", [[1.0, float("nan"), 2.0], [1.0, 2.0]])
def test_persistence_rejects_invalid_series(values):
    with pytest.raises(ValueError):
        persistence(values, holdout=2)
