import pytest
from model_loader import load_model, model_cache


def test_unsupported_model_raises():
    with pytest.raises(ValueError):
        load_model('unsupported_model')

# Skeleton for supported model test; requires Magenta dependency
# def test_load_model_caches(monkeypatch):
#     # monkeypatch actual Magenta classes or functions here
#     pass
