# Sloptrim confirmed-bug fixes

Date: 2026-08-17

## Scope

Fix the five reproduced defects without changing detector weights, band boundaries,
thresholds, or unrelated prose rules.

## Confirmed failures

1. A short document can report `confidence: none` and still be flagged by the
   save hook. Reproduction: a 61-byte document scores 45, says the score is
   noise, and receives a rewrite instruction.
2. Valid XLSX workbooks using worksheet `inlineStr` cells return empty text
   because only `xl/sharedStrings.xml` is read.
3. EPUB XHTML loses text inside ordinary inline and list tags. Reproduction:
   `Keep <em>this emphasized text</em> and <a>this link</a>` extracts as
   `Keep  and .`.
4. Confidence counts detector keys instead of unique numbered catalogue
   families. Two family-32 detectors therefore turn one independent family
   into two and promote confidence from low to moderate.
5. The save hook silently ignores plain files above 512 KB and archives above
   4 MB, while the product claims every saved prose file is scored.

## Design

### Document extraction

Include XLSX/XLSM worksheet XML in the existing archive scan. The existing
`t`-element handling will then read inline strings while continuing to ignore
shared-string indexes and numeric cell values.

For EPUB only, retain every XHTML element's direct text and tail text. Insert
line boundaries around block elements so words survive inline formatting
without joining separate paragraphs. Other Office/OpenDocument extraction
keeps its current tag rules.

### Confidence behavior

Build the confidence evidence count from unique numeric catalogue prefixes,
after the existing score-only filters. This changes only the confidence label;
it does not change the score.

The save hook may record a `confidence: none` result but must not request a
rewrite from it. `/sloptrim check` will show the confidence and its reason so a
raw short-text score is not presented without its warning. Low, moderate, and
high confidence retain existing threshold behavior.

### Oversized files

Keep the current resource caps. When a file exceeds one, add a session-ledger
record with kind `skipped`, its size, and the applicable limit. `/sloptrim show`
will state that the file was not scored because it exceeded the limit.

Replace unconditional “every saved prose file is scored” claims with wording
that identifies supported save tools and size limits. No large file will be
read merely to satisfy a marketing claim.

## Test design

Each defect gets an isolated regression that fails before production changes:

- XLSX A/B: shared-string workbook remains readable; equivalent inline-string
  workbook becomes readable.
- EPUB A/B: plain paragraph remains readable; formatted inline/link/list text
  is preserved in reading order.
- Confidence A/B: two different catalogue families remain independent; two
  detector keys from family 32 count as one family.
- Short hook A/B: an actionable document above the threshold is still flagged;
  an above-threshold document with `confidence: none` is recorded but silent.
- Size A/B: an in-limit file is scored; an oversized file is logged as skipped
  and appears accurately in `/sloptrim show`.

Verification runs the focused tests in RED and GREEN states, then the complete
Python suite, hook suite, documentation checker, Python compilation, Node
syntax checks, and a clean-worktree inspection.

## Non-goals

- Recalibrating detector weights, bands, or thresholds.
- Reading numeric XLSX cells, formulas, charts, headers, or speaker notes.
- Removing size caps or adding streaming archive support.
- Refactoring the detector or hook architecture.
- Adding dependencies.

## Acceptance criteria

- Every confirmed reproduction has an automated regression test that was seen
  failing before its fix and passing afterward.
- Existing supported inputs and threshold behavior remain unchanged.
- All project checks pass with counts and documentation updated consistently.
- No network or runtime dependency is added.
