# Reference Documentation for Rust Analyzer Options

This is a proof of concept for [rust analyzer issue #13178](https://github.com/rust-lang/rust-analyzer/issues/13178)

This project can also be used to render abitrary vscode package.json files.
This is more of a side effect than an intented use case.
There is no guarantee it will work with your package.json as this project targets rust-analyzers package.json.

Anyway have fun:
```shell
scripts/build.sh single <release date> <package.json> <output.html>
# example values
scripts/build.sh single 2024-06-09 path/to/package.json path/to/rendered/output.html
```
