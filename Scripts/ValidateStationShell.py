"""Fresh read-only persisted candidate checks; run in a separate editor process."""
from pathlib import Path
import importlib.util

path=Path(__file__).resolve().with_name('AuthorStationShell.py')
spec=importlib.util.spec_from_file_location('station_shell_author',path)
author=importlib.util.module_from_spec(spec)
spec.loader.exec_module(author)


def main():
    return author.main(validate_only=True)


if __name__=='__main__':
    main()
