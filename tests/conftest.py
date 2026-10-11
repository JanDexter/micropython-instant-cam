"""Run dither.py on CPython: fake the micropython module and viper pointer types."""
import builtins, sys, types, pathlib

m = types.ModuleType("micropython")
m.viper = lambda f: f
m.const = lambda x: x
sys.modules["micropython"] = m
builtins.ptr8 = builtins.ptr16 = lambda x: x
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
