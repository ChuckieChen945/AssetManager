"""Test AssetManager."""

import assetmanager


def test_import() -> None:
    """Test that the app can be imported."""
    assert isinstance(assetmanager.__name__, str)
