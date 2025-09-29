import pathlib
import sys

from dtx_to_wif.wpo_reader import read_wpo

if len(sys.argv) < 2:
    raise RuntimeError("To use: provide a path to the wpo file")

filepath = pathlib.Path(sys.argv[1])
print(filepath)
with filepath.open("rb") as f:
    data = read_wpo(f, filepath.name)
print(data)
