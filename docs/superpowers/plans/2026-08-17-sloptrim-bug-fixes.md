# Sloptrim Confirmed-Bug Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix five reproduced extraction, confidence, and oversized-file defects with isolated RED/GREEN evidence and no score recalibration.

**Architecture:** Keep the existing detector and hook boundaries. Extend archive extraction only where valid document text is currently lost, correct confidence evidence at its source, and make hook callers respect or report the detector's confidence. Preserve resource caps but make skipped files observable and public claims accurate.

**Tech Stack:** Python 3.9+ standard library, Node.js hooks, Bash hook harness, pytest.

## Global Constraints

- Do not change detector weights, score bands, thresholds, or unrelated prose rules.
- Do not add runtime dependencies or network capability.
- Keep plain-text save-hook limit at 512 KB and supported-archive limit at 4 MB.
- Keep numeric XLSX cells, formulas, charts, headers, and speaker notes out of scope.
- Every production change must follow RED, GREEN, then full regression verification.

## File map

- `scripts/detect.py`: archive text extraction and confidence-family calculation.
- `hooks/sloptrim-guard.js`: save-hook confidence gate and oversized-file ledger records.
- `hooks/sloptrim-tracker.js`: `/sloptrim check`, `/sloptrim show`, and doctor wording.
- `hooks/sloptrim-activate.js`: first-run size/scope wording.
- `tests/test_office.py`: XLSX and EPUB A/B extraction regressions.
- `tests/test_detect.py`: confidence-family regression.
- `tests/test_hooks.sh`: real hook A/B regressions.
- `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`: live claims and suite counts.

---

### Task 1: Read XLSX inline strings

**Files:**
- Modify: `tests/test_office.py`
- Modify: `scripts/detect.py:1957-1961`

**Interfaces:**
- Consumes: `detect.read_input(paths: list) -> str` and `_ZIP_DOC` archive-member selectors.
- Produces: XLSX/XLSM extraction that reads both shared-string tables and worksheet `inlineStr` text.

- [ ] **Step 1: Write the failing XLSX A/B test**

Add this builder and test to `tests/test_office.py`:

```python
def make_inline_xlsx(path, text=SLOP):
    items = "".join(
        '<row r="%d"><c r="A%d" t="inlineStr"><is><t>%s</t></is></c></row>'
        % (i, i, p)
        for i, p in enumerate(_paras(text), 1)
    )
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types/>')
        z.writestr(
            "xl/worksheets/sheet1.xml",
            '<?xml version="1.0"?><worksheet xmlns="%s"><sheetData>%s'
            '</sheetData></worksheet>' % (P, items),
        )
    return path


def test_xlsx_shared_and_inline_strings_are_read(tmp_path):
    shared = detect.read_input([str(make_xlsx(tmp_path / "shared.xlsx"))])
    inline = detect.read_input([str(make_inline_xlsx(tmp_path / "inline.xlsx"))])
    assert "delve" in shared and "game-changer" in shared
    assert "delve" in inline and "game-changer" in inline
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `python -m pytest tests/test_office.py::test_xlsx_shared_and_inline_strings_are_read -q`

Expected: FAIL because `inline` is empty while `shared` contains the prose.

- [ ] **Step 3: Add worksheet XML to the existing selector**

Change the XLSX/XLSM entries in `scripts/detect.py` to:

```python
    ".xlsx": ("xl/sharedStrings.xml", "xl/worksheets/sheet"),
    ".xlsm": ("xl/sharedStrings.xml", "xl/worksheets/sheet"),
```

- [ ] **Step 4: Run focused and Office tests for GREEN**

Run: `python -m pytest tests/test_office.py::test_xlsx_shared_and_inline_strings_are_read tests/test_office.py -q`

Expected: all selected tests PASS.

- [ ] **Step 5: Commit the isolated fix**

```bash
git add tests/test_office.py scripts/detect.py
git commit -m "fix: read inline xlsx strings"
```

---

### Task 2: Preserve EPUB inline and list text

**Files:**
- Modify: `tests/test_office.py`
- Modify: `scripts/detect.py:1963-2024`

**Interfaces:**
- Consumes: `extract_office_text(path: str) -> str` and ElementTree element `text`/`tail` fields.
- Produces: EPUB text in reading order with inline formatting retained and block elements separated.

- [ ] **Step 1: Write the failing EPUB A/B test**

Add to `tests/test_office.py`:

```python
def make_epub(path, body):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(
            "chapter.xhtml",
            '<?xml version="1.0"?><html xmlns="http://www.w3.org/1999/xhtml">'
            "<body>%s</body></html>" % body,
        )
    return path


def test_epub_plain_and_formatted_text_stay_in_reading_order(tmp_path):
    plain = detect.read_input([
        str(make_epub(tmp_path / "plain.epub", "<p>Plain paragraph text.</p>"))
    ])
    formatted = detect.read_input([
        str(make_epub(
            tmp_path / "formatted.epub",
            '<p>Keep <em>this emphasized text</em> and '
            '<a>this link</a>.</p><ul><li>List item prose</li></ul>',
        ))
    ])
    assert plain == "Plain paragraph text."
    assert "Keep this emphasized text and this link." in formatted
    assert "List item prose" in formatted
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `python -m pytest tests/test_office.py::test_epub_plain_and_formatted_text_stay_in_reading_order -q`

Expected: FAIL because formatted output is `Keep  and .` and omits the list item.

- [ ] **Step 3: Add EPUB-specific visible-text handling**

Add near `_BLOCK_TAGS`:

```python
_EPUB_BLOCK_TAGS = {
    "address", "article", "aside", "blockquote", "br", "caption", "div",
    "footer", "h1", "h2", "h3", "h4", "h5", "h6", "header", "li",
    "main", "nav", "p", "section", "table", "td", "th", "title", "tr",
}
```

In `extract_office_text`, set `epub = ext == ".epub"`, then replace the element loop with:

```python
            for el in root.iter():
                tag = _local(el.tag)
                if epub:
                    if tag in _EPUB_BLOCK_TAGS and buf and buf[-1] != "\n":
                        buf.append("\n")
                    if el.text:
                        buf.append(el.text)
                elif tag in _TEXT_TAGS and el.text:
                    buf.append(el.text)
                elif tag in _BLOCK_TAGS:
                    if buf and buf[-1] != "\n":
                        buf.append("\n")
                    if el.text:
                        buf.append(el.text)
                if el.tail and (epub or el.tail.strip()):
                    buf.append(el.tail)
```

Normalize EPUB indentation before appending the chunk:

```python
            chunk = "".join(buf)
            if epub:
                chunk = re.sub(r"[ \t]+\n", "\n", chunk)
```

- [ ] **Step 4: Run focused and Office tests for GREEN**

Run: `python -m pytest tests/test_office.py::test_epub_plain_and_formatted_text_stay_in_reading_order tests/test_office.py -q`

Expected: all selected tests PASS, including existing DOCX/PPTX/XLSX/ODF behavior.

- [ ] **Step 5: Commit the isolated fix**

```bash
git add tests/test_office.py scripts/detect.py
git commit -m "fix: preserve formatted epub text"
```

---

### Task 3: Count independent catalogue families once

**Files:**
- Modify: `tests/test_detect.py`
- Modify: `scripts/detect.py:1913-1921`

**Interfaces:**
- Consumes: detector result keys in `<catalogue-number>_<detector-name>` form.
- Produces: `score_confidence(words, families)` called with unique scored catalogue numbers.

- [ ] **Step 1: Write the failing confidence test**

Add after `run_detect` in `tests/test_detect.py`:

```python
def test_confidence_counts_catalogue_families_not_detector_keys():
    text = """The survey used several methods. These methods provide information about how residents travel between the river district and the central station on ordinary weekdays. Twelve volunteers counted bicycles at the bridge from six in the morning until the last school bus passed shortly after nine, pausing only when traffic officers closed one lane. At the same time, three clerks checked paper tickets on buses that entered the square, while another clerk recorded delays caused by road repairs near the library. Rain stopped the work briefly. When counting resumed, the team kept the morning and afternoon results separate because school traffic changed the totals after three o'clock, and mixing those periods would have hidden the difference between commuter trips and short journeys made by pupils. The final table lists each observation. It also records the date, location, direction of travel, and weather at the time, giving later readers enough detail to check the arithmetic without relying on the summary. No estimate was added where a count was missing."""
    result = run_detect(text)
    keys = {k for k in result if not k.startswith("_")}
    assert keys == {"32_catalog_leadin", "32_catalog_pivot"}
    assert result["_metrics"]["confidence"] == "low"
    assert "1 scored pattern" in result["_metrics"]["confidence_reason"]
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `python -m pytest tests/test_detect.py::test_confidence_counts_catalogue_families_not_detector_keys -q`

Expected: FAIL with confidence `moderate` because both family-32 keys are counted.

- [ ] **Step 3: Replace the key count with a unique family set**

In `scripts/detect.py` use:

```python
    scored_fams = {
        int(k.split("_", 1)[0])
        for k in result
        if not k.startswith("_")
        and k not in _SCORE_REPORT_ONLY
        and k not in _SCORE_STYLE_ONLY
    }
    result["_metrics"].update(score_confidence(count_words(text), len(scored_fams)))
```

- [ ] **Step 4: Run focused and detector tests for GREEN**

Run: `python -m pytest tests/test_detect.py::test_confidence_counts_catalogue_families_not_detector_keys tests/test_detect.py -q`

Expected: both selected tests PASS and the score remains unchanged.

- [ ] **Step 5: Commit the isolated fix**

```bash
git add tests/test_detect.py scripts/detect.py
git commit -m "fix: count confidence families once"
```

---

### Task 4: Respect zero confidence in hook callers

**Files:**
- Modify: `tests/test_hooks.sh`
- Modify: `hooks/sloptrim-guard.js:104-112`
- Modify: `hooks/sloptrim-tracker.js:52-62`

**Interfaces:**
- Consumes: `_metrics.confidence` and `_metrics.confidence_reason` from detector JSON.
- Produces: no automatic rewrite request for `confidence: none`; `/sloptrim check` reports confidence explicitly.

- [ ] **Step 1: Add failing hook A/B checks**

After the existing clean-file guard check in `tests/test_hooks.sh`, add:

```bash
SHORT="$CLAUDE_CONFIG_DIR/short.md"
cat > "$SHORT" <<'EOF'
I hope this helps. As an AI language model, I cannot assist.
EOF
out="$(printf '{"tool_name":"Write","tool_input":{"file_path":"%s"},"session_id":"short"}' "$SHORT" | node "$REPO/hooks/sloptrim-guard.js")"
[ -z "$out" ]; check "guard does not act on a score with no confidence" $?
out="$(printf '{"prompt":"/sloptrim check %s"}' "$SHORT" | node "$REPO/hooks/sloptrim-tracker.js")"
echo "$out" | grep -q "confidence: none"; check "check exposes zero-confidence scores" $?
```

The existing slop-file checks remain the positive A-side proving actionable text is still flagged.

- [ ] **Step 2: Run hook suite and verify RED**

Run: `bash tests/test_hooks.sh`

Expected: two new checks FAIL; the existing actionable slop checks PASS.

- [ ] **Step 3: Gate the guard and expose confidence in check output**

In `hooks/sloptrim-guard.js` change:

```javascript
const flagged = score > threshold && m.confidence !== 'none';
```

In `hooks/sloptrim-tracker.js`, add before the return from `check`:

```javascript
  const confidence = m.confidence || 'unknown';
  const confidenceLine = m.confidence_reason
    ? `confidence: ${confidence} - ${m.confidence_reason}`
    : `confidence: ${confidence}`;
```

Include `confidenceLine` between the score and tells lines:

```javascript
  return [
    `${path.basename(p)} - ${verdict(m.ai_tell_score)} (score ${m.ai_tell_score}/100, band: ${m.ai_tell_band})`,
    confidenceLine,
    tells.length ? `tells: ${tells.slice(0, 8).join('; ')}` : 'tells: none',
    'report only - say "sloptrim this file" for the rewrite.',
  ].join('\n');
```

- [ ] **Step 4: Run hook suite for GREEN**

Run: `bash tests/test_hooks.sh`

Expected: 69 passed, 0 failed at this task boundary.

- [ ] **Step 5: Commit the isolated fix**

```bash
git add tests/test_hooks.sh hooks/sloptrim-guard.js hooks/sloptrim-tracker.js
git commit -m "fix: respect zero-confidence scores"
```

---

### Task 5: Record oversized skips and make claims truthful

**Files:**
- Modify: `tests/test_hooks.sh`
- Modify: `hooks/sloptrim-guard.js:68-83`
- Modify: `hooks/sloptrim-tracker.js:89-104,137-157`
- Modify: `hooks/sloptrim-activate.js:19-23`
- Modify: `README.md`
- Modify: `CONTRIBUTING.md`
- Modify: `CHANGELOG.md`
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: existing per-session ledger and guard size limits.
- Produces: `{kind: "skipped", reason: "size", size, limit}` records and accurate `/sloptrim show` text.

- [ ] **Step 1: Add the failing oversized-file A/B check**

After session-ledger checks in `tests/test_hooks.sh`, add:

```bash
LARGE="$CLAUDE_CONFIG_DIR/large.md"
node -e 'require("fs").writeFileSync(process.argv[1], "ordinary prose ".repeat(40000))' "$LARGE"
printf '{"session_id":"large","tool_input":{"file_path":"%s"}}' "$LARGE" | node "$REPO/hooks/sloptrim-guard.js" >/dev/null
out="$(echo '{"session_id":"large","prompt":"/sloptrim show"}' | node "$REPO/hooks/sloptrim-tracker.js")"
echo "$out" | grep -q "not scored.*512 KB limit"; check "show reports an oversized prose file as skipped" $?
```

The existing in-limit slop-file and ledger checks are the positive A-side.

- [ ] **Step 2: Run hook suite and verify RED**

Run: `bash tests/test_hooks.sh`

Expected: the oversized-file check FAILS because no ledger exists for session `large`.

- [ ] **Step 3: Record size skips in the guard**

Replace the guard's stat/size block with:

```javascript
let text = '';
try {
  const stat = fs.statSync(filePath);
  if (!stat.isFile()) process.exit(0);
  const limit = isOffice ? 4 * 1024 * 1024 : 512 * 1024;
  if (stat.size > limit) {
    logDeliverable({ t: Date.now(), file: base, kind: 'skipped',
                     reason: 'size', size: stat.size, limit }, sid);
    process.exit(0);
  }
  if (!isOffice) text = readTextFile(filePath);
} catch (e) {
  process.exit(0);
}
```

- [ ] **Step 4: Display skipped records**

Add the first branch inside `showLedger`'s loop:

```javascript
    if (r.kind === 'skipped' && r.reason === 'size') {
      lines.push(`  ${r.file} - not scored: exceeds the ${r.limit / 1024} KB limit`);
    } else if (r.kind === 'binary') {
```

- [ ] **Step 5: Replace unconditional claims and update suite counts**

Use this factual scope everywhere the unconditional claim appears:

```text
Scores prose files saved through supported file-edit tools: plain text up to 512 KB and supported archives up to 4 MB.
```

Apply equivalent grammar to `README.md`, both plugin descriptions,
`hooks/sloptrim-activate.js`, and the successful doctor message in
`hooks/sloptrim-tracker.js`. Preserve the README's existing disclosure that
Bash writes bypass hooks.

Update live suite counts after collection:

- `README.md`: 103 Python tests, 72 hook checks, 175 total.
- `CONTRIBUTING.md`: 103 Python tests and 72 hook checks.
- `CHANGELOG.md`: replace the historical numeric “99/67” bullet with
  “Expanded Python and hook regression suites” so release history does not
  falsely claim today's live count.

- [ ] **Step 6: Run focused hooks and documentation verification**

Run:

```bash
bash tests/test_hooks.sh
python scripts/check_docs.py
```

Expected: 72 hook checks pass; documentation checker reports zero failures and derives 103 Python tests, 72 hook checks, 175 together.

- [ ] **Step 7: Commit the isolated fix**

```bash
git add tests/test_hooks.sh hooks/sloptrim-guard.js hooks/sloptrim-tracker.js hooks/sloptrim-activate.js README.md CONTRIBUTING.md CHANGELOG.md .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "fix: report files skipped by size limits"
```

---

### Task 6: Deep A/B and full verification

**Files:**
- Verify only; modify files only if a failing check identifies a regression in this scope.

**Interfaces:**
- Consumes: all prior task outputs.
- Produces: fresh evidence for every acceptance criterion.

- [ ] **Step 1: Run every focused regression**

```bash
python -m pytest \
  tests/test_office.py::test_xlsx_shared_and_inline_strings_are_read \
  tests/test_office.py::test_epub_plain_and_formatted_text_stay_in_reading_order \
  tests/test_detect.py::test_confidence_counts_catalogue_families_not_detector_keys -q
bash tests/test_hooks.sh
```

Expected: 3 focused Python tests pass; 72 hook checks pass with 0 failures.

- [ ] **Step 2: Run the full project verification**

```bash
python -m pytest tests/ -q
bash tests/test_hooks.sh
python scripts/check_docs.py
python -m compileall -q scripts tests
node --check hooks/sloptrim-activate.js
node --check hooks/sloptrim-guard.js
node --check hooks/sloptrim-lib.js
node --check hooks/sloptrim-stats.js
node --check hooks/sloptrim-subagent.js
node --check hooks/sloptrim-tracker.js
```

Expected: 103 Python tests pass, 72 hook checks pass, documentation verification reports zero failures, and every syntax command exits 0.

- [ ] **Step 3: Inspect the final delta and repository state**

```bash
git diff --check HEAD~5..HEAD
git status --short
git log -6 --oneline
```

Expected: no whitespace errors; only intended files changed; five implementation commits follow the approved design/plan commits.

- [ ] **Step 4: Record the verdict**

Summarize each defect's RED and GREEN run, complete suite counts, documentation status, residual limitations, and whether the worktree is clean. Do not claim benchmark accuracy; the private corpora remain outside this repository.
