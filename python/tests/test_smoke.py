from bitcoin_utxo_lp import __version__


def test_version_exists() -> None:
    assert isinstance(__version__, str)
    assert __version__


def test_import() -> None:
    import bitcoin_utxo_lp  # noqa: F401
