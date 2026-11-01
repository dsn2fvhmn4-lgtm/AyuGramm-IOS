"""Compile the actual vendored Lua engine and exercise it on Linux or macOS."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile


def run(source):
    source = source.resolve()
    engine = source / "submodules/AyuPluginEngines"
    compiler = os.environ.get("CC", "clang")
    with tempfile.TemporaryDirectory(prefix="ayu-lua-tests-") as temporary:
        output = Path(temporary)
        includes = ["-I", str(engine / "PublicHeaders"), "-I", str(engine / "Vendor/lua")]
        engine_object = output / "engine.o"
        subprocess.run([compiler, "-std=gnu11", "-Wall", "-Wextra", "-Werror", "-O1", *includes,
                        "-c", str(engine / "Sources/AyuLuaEngine.c"), "-o", str(engine_object)], check=True)
        test_object = output / "tests.o"
        subprocess.run([compiler, "-std=gnu11", "-Wall", "-Wextra", "-Werror", "-O1", *includes,
                        "-c", str(source / "tools/ayu-tests/lua/main.c"), "-o", str(test_object)], check=True)
        binary = output / "lua-tests"
        subprocess.run([compiler, "-std=gnu11", "-O1", *includes,
                        *map(str, sorted((engine / "Vendor/lua").glob("*.c"))), str(engine_object),
                        str(test_object), "-lm", "-o", str(binary)], check=True)
        subprocess.run([str(binary)], check=True, timeout=30)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, nargs="?")
    parser.add_argument("--patch", type=Path, help="Extract only the new engine and test files from the port patch")
    args = parser.parse_args()
    if (args.source is None) == (args.patch is None):
        parser.error("provide either source or --patch")
    if args.patch:
        with tempfile.TemporaryDirectory(prefix="ayu-lua-source-") as temporary:
            subprocess.run(["git", "apply", "--whitespace=nowarn", "--include=submodules/AyuPluginEngines/*",
                            "--include=tools/ayu-tests/lua/*", str(args.patch.resolve())], cwd=temporary, check=True)
            run(Path(temporary))
    else:
        run(args.source)
