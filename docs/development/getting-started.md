# Your first Pear contribution

This tutorial gives you a small local success before choosing runtime work. You
need Git and Python 3 for documentation checks. AI tools, a Steam account, games
and Apple signing credentials are not required for these checks.

The repository is being prepared for public access. Until it opens, cloning
requires existing access. Do not treat a private URL as a public download.

## Get the source

```sh
git clone https://github.com/postmelee/pear.git
cd pear
```

Use the current `master` branch as the base for contributions. Read the
[contributor guide](../contributing.md), agree a change's scope in an Issue and
work on your own branch. Do not copy anyone's authenticated runtime environment.

## Run your first check

```sh
python3 tools/check_governance.py
python3 -m unittest discover -s tests/docs -p 'test_*.py' -v
python3 tools/compatibility.py --check
```

The first command checks local documentation links and governance. The second
runs portable synthetic tests. The third confirms that reviewed JSON and the
committed compatibility table agree. A successful exit establishes those checks,
not game compatibility. No Wine, GPU, Steam or native runtime is launched.

A small first contribution can fix a confusing sentence or improve a redistributable
fixture. Run the relevant checks again, then open a PR with the problem, change,
actual results and any untested behavior. Internal stage reports are not required
from external contributors.

## Build the Rosetta Preview

Use Apple Silicon, macOS 26+, Xcode command-line tools and Rust 1.94 or later.
The current build has been exercised with Rust 1.94.1 and Swift 6.3.3.

```sh
cargo fetch --manifest-path preview/Cargo.toml --locked
sh preview/build.sh
.build/task47/preview/cargo/release/pear-preview --help
```

The build runs the Rust tests, builds the shared CLI and Swift window, converts
the supplied icon, and produces `.build/task47/preview/Pear.app` with a
local ad-hoc signature. `--help` is a safe first inspection and does not prepare
Steam. The release script's `.build/task47` output is a development location.

Running the app or the CLI without `--help` downloads runtime/Steam components
and prepares private data under `~/Library/Application Support/Pear Preview`.
Read the [Preview guide](../rosetta-preview.md) before an intentional runtime test;
Rosetta and legitimate Steam access are needed. Preserve any existing data.
Local signing does not qualify ordinary-user delivery. Maintainers use the
[release procedure](preview-release.md) for authorized Developer ID signing.

## Choose the next step

- Improve the Preview: inspect `preview/src/main.rs`, `preview/Launcher.swift`
  and the [current delivery Issue](https://github.com/postmelee/pear/issues/47).
- Work on the final native goal: use the [Rosetta-free guide](rosetta-free.md).
- Improve public records: follow the [reviewed report process](../compatibility/README.md).
- Ask about a task in [Q&A](https://github.com/postmelee/pear/discussions/categories/q-a).

Use [build diagnostics](build-diagnostics.md) only when investigating engineering
builds; it does not replace the checks required by your specific change.
