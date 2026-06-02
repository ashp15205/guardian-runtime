"""Tests for LocalStorage."""

from guardian.core.storage import LocalStorage


def test_save_and_load_license(tmp_path):
    storage = LocalStorage(base_dir=tmp_path)
    storage.save_license("gdn_test_key", plan="free", limit=100)
    config = storage.load_license()
    assert config is not None
    assert config["license_key"] == "gdn_test_key"
    assert config["check_limit"] == 100


def test_increment_usage(tmp_path):
    storage = LocalStorage(base_dir=tmp_path)
    assert storage.increment_usage() == 1
    assert storage.increment_usage() == 2
    assert storage.get_usage()["checks"] == 2


def test_usage_limit(tmp_path):
    storage = LocalStorage(base_dir=tmp_path)
    storage.save_license("key", limit=2)
    storage.increment_usage()
    storage.increment_usage()
    allowed, used, limit = storage.check_usage_limit()
    assert used == 2
    assert limit == 2
    assert allowed is False
