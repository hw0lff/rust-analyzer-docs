#!/usr/bin/env bash
set -euo pipefail

repo_dir=$(readlink -f -- "$(dirname "$(readlink -f -- "$0")")"/../)
out="$repo_dir/out"
build="$repo_dir/build"
ra="$build/rust_analyzer"
scripts="$repo_dir/scripts"

pandoc_opts=(
    --standalone
    --from markdown --to html
    --metadata title='Reference Documentation for Rust Analyzer Options'
    --metadata maxwidth='55em'
    --template "$repo_dir/pandoc.html.template"
    -V "date-meta=$(date +%F)"
)

clone_ra() {
    if [[ -d "$ra" ]]; then
        cd "$ra"
        git fetch
    else
        git clone https://github.com/rust-lang/rust-analyzer.git "$ra"
    fi
}

generate_index() {
    rm -f "$build/index.md" "$build/index.rev.md"
    for tag in $(git tag); do
        echo "- [$tag]($tag/index.html)" >> "$build/index.rev.md"
    done
    echo "# Rust Analyzer Tags" > "$build/index.md"
    tac "$build/index.rev.md" >> "$build/index.md"
}

build_docs_single() {
    local release_date="$1"
    local input_package_json="$2"
    local output_html="$3"

    local build_single
    build_single="$build/single-$(date +%FT%T)"
    mkdir -p "$build_single"
    mkdir -p "$(dirname "$output_html")"
    local rendered_md="$build_single/rendered.md"

    "$scripts/md_formatter.py" "$input_package_json" "$rendered_md"

    local pandoc_page_opts=(
        -V "date=$release_date"
        "$rendered_md"
        -o "$output_html"
    )
    pandoc "${pandoc_opts[@]}" "${pandoc_page_opts[@]}"
}

gather_package_json() {
    local pids=()
    echo "[$(date +%FT%T)] Gathering package.json"
    for tag in $(git tag); do
        mkdir -p "$build/$tag"
        git show "$tag":editors/code/package.json > "$build/$tag/package.json" &
        pids+=("$!")
    done
    wait "${pids[@]}"
}

generate_markdown() {
    local pids=()
    echo "[$(date +%FT%T)] Generating markdown"
    for tag in $(git tag); do
        "$scripts/md_formatter.py" "$build/$tag/package.json" "$build/$tag/rendered.md" &
        pids+=("$!")
    done
    wait "${pids[@]}"
}

render_html() {
    local pids=()
    echo "[$(date +%FT%T)] Rendering HTML"
    for tag in $(git tag); do
        mkdir -p "$out/$tag"

        local pandoc_tag_opts=(
            -V "date=$tag"
            "$build/$tag/rendered.md"
            -o "$out/$tag/index.html"
        )
        pandoc "${pandoc_opts[@]}" "${pandoc_tag_opts[@]}" &
        pids+=("$!")
    done

    pandoc "${pandoc_opts[@]}" "$build/index.md" -o "$out/index.html" &
    pids+=("$!")

    wait "${pids[@]}"
}
build_docs_all() {
    mkdir -p "$build"
    mkdir -p "$out"
    clone_ra
    cd "$ra"

    generate_index

    gather_package_json

    generate_markdown

    render_html

    echo "[$(date +%FT%T)] All finished"
}

usage() {
    cat << EOF
Usage:
    all   - build docs for all tags
    clean - remove all build artifacts
    single <release date> <input package.json path> <output html path>
          - build a single package.json
EOF
}


if [[ $# -eq 1 ]]; then
    case $1 in
        all)
            build_docs_all
            exit 0;;
        clean)
            rm -rf "$out"
            rm -rf "$build"
            exit 0;;
        *)
            usage
            exit 1;;
    esac
elif [[ $# -eq 4 ]]; then
    case $1 in
        single)
            shift
            build_docs_single "$@"
            exit 0;;
        *)
            usage
            exit 1;;
    esac
fi

usage
exit 1
