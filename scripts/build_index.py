"""Build the local document index from catalog PDFs.

Usage:  python -m scripts.build_index [--refresh]

Downloads each catalog resource with content_type "pdf" into data/documents/
(skipped if already present unless --refresh), extracts text per page, chunks it,
and writes data/index/chunks.json. Portals and webpages are skipped.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests

from reslink.catalog import CatalogError, load_catalog
from reslink.config import DEFAULT_CATALOG_PATH, DEFAULT_INDEX_PATH, DOCUMENTS_DIR
from reslink.ingest import chunk_pages, extract_pdf_pages, save_index
from reslink.models import Chunk, Resource

USER_AGENT = "ResLinkAI-hackathon-indexer/0.1"


def download_pdf(resource: Resource, dest: Path, refresh: bool) -> Path:
    if dest.is_file() and not refresh:
        return dest
    response = requests.get(resource.url, timeout=30, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    if not response.content.startswith(b"%PDF"):
        raise ValueError(f"{resource.url} did not return a PDF (content-type {response.headers.get('content-type')})")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(response.content)
    return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--refresh", action="store_true", help="re-download documents")
    args = parser.parse_args(argv)

    try:
        resources = load_catalog(DEFAULT_CATALOG_PATH)
    except CatalogError as error:
        print(error, file=sys.stderr)
        return 1

    chunks: list[Chunk] = []
    failures = 0
    for resource in resources:
        if resource.content_type != "pdf":
            print(f"skip   {resource.id} ({resource.content_type}: not ingestible)")
            continue
        try:
            path = download_pdf(resource, DOCUMENTS_DIR / f"{resource.id}.pdf", args.refresh)
            pages = extract_pdf_pages(path)
        except Exception as exc:  # report and continue with other resources
            failures += 1
            print(f"FAIL   {resource.id}: {type(exc).__name__}: {exc}", file=sys.stderr)
            continue
        new = chunk_pages(resource.id, pages)
        if not new:
            failures += 1
            print(f"FAIL   {resource.id}: no extractable text (scanned PDF?)", file=sys.stderr)
            continue
        chunks.extend(new)
        print(f"index  {resource.id}: {len(pages)} pages -> {len(new)} chunks")

    save_index(chunks, resources, DEFAULT_INDEX_PATH)
    print(f"wrote  {DEFAULT_INDEX_PATH} ({len(chunks)} chunks, {failures} failure(s))")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
