from topolab import __version__


def test_package_imports() -> None:
    assert __version__ == "1.0.0"
