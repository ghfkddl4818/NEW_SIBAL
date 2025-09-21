import pytest

from client_discovery.m4_filter import FilterManager


@pytest.fixture
def base_config():
    return {
        "output": {"csv_file": "targets_{date}.csv"},
        "filters": {},
        "search": {
            "review_min": 0,
            "review_max": 1000,
            "follower_min": 0,
            "follower_max": 10000,
        },
        "blocklist": ["블랙리스트"],
    }


def test_blocklist_detection(tmp_path, monkeypatch, base_config):
    monkeypatch.setattr(
        FilterManager,
        "_get_output_file",
        lambda self: tmp_path / "targets.csv",
        raising=False,
    )
    manager = FilterManager(base_config)

    assert manager.is_blocklisted("블랙리스트 스토어") is True
    assert manager.is_blocklisted("일반 스토어") is False


def test_multi_store_detection(tmp_path, monkeypatch, base_config):
    monkeypatch.setattr(
        FilterManager,
        "_get_output_file",
        lambda self: tmp_path / "targets.csv",
        raising=False,
    )
    manager = FilterManager(base_config)

    assert manager.is_multi_store("가격비교 외 3")
    assert manager.is_multi_store("스토어/11번가")
    assert not manager.is_multi_store("단일매장")


def test_review_and_interest_range(tmp_path, monkeypatch, base_config):
    monkeypatch.setattr(
        FilterManager,
        "_get_output_file",
        lambda self: tmp_path / "targets.csv",
        raising=False,
    )
    manager = FilterManager(base_config)

    assert manager.passes_review_range(10)
    assert manager.passes_interest_range(500)
    assert not manager.passes_review_range(None)
    assert not manager.passes_interest_range(None)
