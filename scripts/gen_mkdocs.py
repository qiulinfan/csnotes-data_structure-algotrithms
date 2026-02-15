from __future__ import annotations

import argparse
from pathlib import Path
import re
from urllib.parse import quote

import markdown

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
MKDOCS_FILE = ROOT / "mkdocs.yml"
INDEX_FILE = DOCS_DIR / "index.md"
README_FILE = DOCS_DIR / "README.md"


def sort_key(path: Path) -> tuple[int, int | str]:
    match = re.match(r"^(\d+)", path.stem)
    if match:
        return (0, int(match.group(1)))
    return (1, path.name.lower())


def display_title(path: Path) -> str:
    title = path.stem.replace("-", " ").replace("_", " ").strip()
    title = re.sub(r"\s+", " ", title)
    return title


def yaml_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def collect_sections(path: Path, max_depth: int) -> list[dict[str, object]]:
    text = path.read_text(encoding="utf-8")
    md = markdown.Markdown(extensions=["toc"])
    md.convert(text)

    sections: list[dict[str, object]] = []

    def walk(tokens: list[dict], parent: list[dict[str, object]]) -> None:
        for token in tokens:
            level = int(token.get("level", 0))
            node: dict[str, object] | None = None
            if 2 <= level <= max_depth:
                name = str(token.get("name", "")).strip()
                anchor = str(token.get("id", "")).strip()
                if name and anchor:
                    node = {"title": name, "anchor": anchor, "children": []}
                    parent.append(node)
            children = token.get("children", [])
            if children:
                target = node["children"] if node is not None else parent
                walk(children, target)

    walk(getattr(md, "toc_tokens", []), sections)
    return sections


def page_url(path: Path) -> str:
    return f"<{path.name}>"


def page_anchor_url(path: Path, anchor: str) -> str:
    page = quote(path.stem, safe="-_.") + ".html"
    return f"{page}#{anchor}"


def get_site_name() -> str:
    if README_FILE.exists():
        for line in README_FILE.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    return "CS Notes"


def collect_markdown_files() -> list[Path]:
    files = [
        path
        for path in DOCS_DIR.glob("*.md")
        if path.name.lower() not in {"index.md", "readme.md"}
    ]
    return sorted(files, key=sort_key)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate mkdocs.yml and docs/index.md from markdown files."
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=2,
        help="Maximum heading level to include in nav (minimum 2).",
    )
    return parser.parse_args()


def write_sections(
    lines: list[str],
    md: Path,
    sections: list[dict[str, object]],
    indent: str,
) -> None:
    for section in sections:
        title = str(section["title"])
        anchor = str(section["anchor"])
        children = section.get("children", [])

        if children:
            lines.append(f"{indent}- {yaml_quote(title)}:")
            lines.append(f"{indent}    - {yaml_quote('Overview')}: {page_anchor_url(md, anchor)}")
            write_sections(lines, md, children, indent + "    ")
        else:
            lines.append(f"{indent}- {yaml_quote(title)}: {page_anchor_url(md, anchor)}")


def generate_mkdocs_yaml(
    site_name: str,
    markdown_files: list[Path],
    max_depth: int,
) -> str:
    lines = [
        f"site_name: {yaml_quote(site_name)}",
        "docs_dir: docs",
        "theme:",
        "  name: readthedocs",
        "markdown_extensions:",
        "  - toc",
        "  - pymdownx.arithmatex:",
        "      generic: true",
        "extra_javascript:",
        "  - javascripts/mathjax.js",
        "  - https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js",
        "use_directory_urls: false",
        "nav:",
        "  - Home: index.md",
    ]

    for md in markdown_files:
        title = display_title(md)
        sections = collect_sections(md, max_depth)

        if not sections:
            lines.append(f"  - {yaml_quote(title)}: {md.name}")
            continue

        lines.append(f"  - {yaml_quote(title)}:")
        lines.append(f"      - {yaml_quote('Overview')}: {md.name}")
        write_sections(lines, md, sections, "      ")

    return "\n".join(lines) + "\n"


def generate_index_md(markdown_files: list[Path]) -> str:
    sections: list[str] = []

    if README_FILE.exists():
        readme_text = README_FILE.read_text(encoding="utf-8").strip()
        if readme_text:
            sections.append(readme_text)

    note_lines = ["## Notes", ""]
    for md in markdown_files:
        note_lines.append(f"- [{display_title(md)}]({page_url(md)})")
    sections.append("\n".join(note_lines))

    return "\n\n".join(sections).rstrip() + "\n"


def main() -> None:
    args = parse_args()
    max_depth = max(2, args.depth)

    markdown_files = collect_markdown_files()
    site_name = get_site_name()

    MKDOCS_FILE.write_text(
        generate_mkdocs_yaml(site_name, markdown_files, max_depth),
        encoding="utf-8",
    )
    INDEX_FILE.write_text(generate_index_md(markdown_files), encoding="utf-8")

    print(f"Generated {MKDOCS_FILE}")
    print(f"Generated {INDEX_FILE}")
    print(f"Included {len(markdown_files)} markdown files.")
    print(f"Heading depth: {max_depth}")


if __name__ == "__main__":
    main()
