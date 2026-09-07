"""Allow ``python -m ion_td`` to use the same CLI as ``ion-td``."""

from .cli import main  # pragma: no cover


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())  # pragma: no cover
