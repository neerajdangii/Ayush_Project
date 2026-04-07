from __future__ import annotations

import re

_COA_TABLE_RE = re.compile(r"<table\b[^>]*>.*?</table>", flags=re.IGNORECASE | re.DOTALL)
_COA_TR_RE = re.compile(r"<tr\b[^>]*>.*?</tr>", flags=re.IGNORECASE | re.DOTALL)
_COA_BLOCK_RE = re.compile(r"<table\b[^>]*>.*?</table>|<p\b[^>]*>.*?</p>|<div\b[^>]*>.*?</div>", flags=re.IGNORECASE | re.DOTALL)


def normalize_report_table_html(html: str) -> str:
    if not html:
        return ""

    cleaned = html

    cleaned = _collapse_repeated_empty_paragraphs(cleaned)
    cleaned = _collapse_adjacent_duplicate_nonempty_rows(cleaned)
    cleaned = _collapse_repeated_table_suffixes(cleaned)
    cleaned = _collapse_repeated_block_suffixes(cleaned)
    cleaned = re.sub(r"\n\s*\n+", "\n", cleaned).strip()
    return cleaned


def _collapse_repeated_empty_paragraphs(html: str) -> str:
    return re.sub(
        r"(?:<(p|div|span)\b[^>]*>(?:\s|&nbsp;|&#160;|<br\s*/?>)*</\1>\s*){2,}",
        "",
        html,
        flags=re.IGNORECASE,
    )


def _collapse_adjacent_duplicate_nonempty_rows(html: str) -> str:
    def _row_signature(row_html: str) -> str:
        normalized = re.sub(r"\s+", " ", row_html)
        normalized = normalized.replace("&nbsp;", " ").replace("&#160;", " ")
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized.casefold()

    def _row_has_meaningful_content(row_html: str) -> bool:
        text = re.sub(r"<[^>]+>", " ", row_html)
        text = text.replace("&nbsp;", " ").replace("&#160;", " ")
        text = re.sub(r"\s+", " ", text).strip()
        return bool(text)

    def _dedupe_table(match):
        table_html = match.group(0)
        row_matches = list(_COA_TR_RE.finditer(table_html))
        if len(row_matches) < 2:
            return table_html

        rebuilt = []
        cursor = 0
        previous_signature = None
        previous_was_nonempty = False

        for row_match in row_matches:
            start, end = row_match.span()
            row_html = row_match.group(0)
            signature = _row_signature(row_html)
            is_nonempty = _row_has_meaningful_content(row_html)

            rebuilt.append(table_html[cursor:start])
            if not (is_nonempty and previous_was_nonempty and signature == previous_signature):
                rebuilt.append(row_html)

            cursor = end
            previous_signature = signature
            previous_was_nonempty = is_nonempty

        rebuilt.append(table_html[cursor:])
        return "".join(rebuilt)

    return _COA_TABLE_RE.sub(_dedupe_table, html)


def _collapse_repeated_table_suffixes(html: str) -> str:
    def _row_signature(row_html: str) -> str:
        normalized = re.sub(r"\s+", " ", row_html)
        normalized = normalized.replace("&nbsp;", " ").replace("&#160;", " ")
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized.casefold()

    def _dedupe_table(match):
        table_html = match.group(0)
        row_matches = list(_COA_TR_RE.finditer(table_html))
        row_count = len(row_matches)
        if row_count < 2:
            return table_html

        signatures = [_row_signature(row_match.group(0)) for row_match in row_matches]
        remove_from = None

        for block_size in range(row_count // 2, 0, -1):
            left_start = row_count - (block_size * 2)
            right_start = row_count - block_size
            if left_start < 0:
                continue
            if signatures[left_start:right_start] == signatures[right_start:row_count]:
                remove_from = right_start
                break

        if remove_from is None:
            return table_html

        rebuilt = []
        cursor = 0
        for index, row_match in enumerate(row_matches):
            if index >= remove_from:
                break
            start, end = row_match.span()
            rebuilt.append(table_html[cursor:start])
            rebuilt.append(table_html[start:end])
            cursor = end
        rebuilt.append(table_html[cursor:row_matches[remove_from].start()])
        rebuilt.append(table_html[row_matches[-1].end():])
        return "".join(rebuilt)

    previous = None
    current = html
    while previous != current:
        previous = current
        current = _COA_TABLE_RE.sub(_dedupe_table, current)
    return current


def _collapse_repeated_block_suffixes(html: str) -> str:
    def _block_signature(block_html: str) -> str:
        normalized = re.sub(r"\s+", " ", block_html)
        normalized = normalized.replace("&nbsp;", " ").replace("&#160;", " ")
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized.casefold()

    previous = None
    current = html

    while previous != current:
        previous = current
        block_matches = list(_COA_BLOCK_RE.finditer(current))
        block_count = len(block_matches)
        if block_count < 2:
            break

        signatures = [_block_signature(match.group(0)) for match in block_matches]
        remove_from = None

        for block_size in range(block_count // 2, 0, -1):
            left_start = block_count - (block_size * 2)
            right_start = block_count - block_size
            if left_start < 0:
                continue
            if signatures[left_start:right_start] == signatures[right_start:block_count]:
                remove_from = right_start
                break

        if remove_from is None:
            break

        current = current[:block_matches[remove_from].start()] + current[block_matches[-1].end():]

    return current
