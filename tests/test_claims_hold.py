"""Coverage the documents describe, checked against what the code does."""
import importlib.util
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def detector():
    spec = importlib.util.spec_from_file_location(
        "claims_detect", REPO / "scripts" / "detect.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def epub(path, body, decl='xmlns="http://www.w3.org/1999/xhtml"'):
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "chapter.xhtml",
            '<?xml version="1.0"?><html %s><body>%s</body></html>' % (decl, body))
    return str(path)


def test_epub_excludes_navigation_style_and_script(tmp_path):
    text = detector().read_input([epub(
        tmp_path / "a.epub",
        "<nav><ol><li>NAVLEAK toc entry</li></ol></nav>"
        "<style>STYLELEAK{color:red}</style>"
        "<script>var x = 'SCRIPTLEAK';</script>"
        "<p>Real prose paragraph.</p>")])
    for excluded in ("NAVLEAK", "STYLELEAK", "SCRIPTLEAK"):
        assert excluded not in text
    assert "Real prose paragraph." in text


def test_epub_keeps_inline_formatting_in_reading_order(tmp_path):
    text = detector().read_input([epub(
        tmp_path / "b.epub",
        '<p>Keep <em>this emphasized text</em> and <a href="#">this link</a>.</p>'
        "<ul><li>List item prose</li></ul>")])
    assert "Keep this emphasized text and this link." in text
    assert "List item prose" in text


def test_epub_reads_a_chapter_with_an_undeclared_prefix(tmp_path):
    """`epub:type` is ordinary EPUB3 and may appear without a declaration."""
    text = detector().read_input([epub(
        tmp_path / "c.epub",
        '<nav epub:type="toc"><ol><li>NAVLEAK</li></ol></nav>'
        '<p epub:type="bridgehead">Real prose survives.</p>')])
    assert "Real prose survives." in text
    assert "NAVLEAK" not in text


def test_the_scan_window_applies_to_every_layer():
    """The score covers the first `_SCAN_CAP` bytes, character rules included."""
    module = detector()
    past_the_window = "word " * 200000 + "​​​"
    assert len(past_the_window) > module._SCAN_CAP
    fired = {k for k in module.scan(past_the_window) if not k.startswith("_")}
    assert "62_invisible_chars" not in fired


def test_one_catalogue_family_pays_the_diversity_term_once():
    """Family 32 emits a lead-in and a pivot. Density counts both; diversity
    counts the family."""
    module = detector()
    text = (
        "The survey used several methods. These methods provide information about "
        "how residents travel between the river district and the central station "
        "on ordinary weekdays. Consider the following: cost, schedule, risk. "
        "Twelve volunteers counted bicycles at the bridge from six in the morning "
        "until the last school bus passed. At the same time, three clerks checked "
        "paper tickets on buses that entered the square. Rain stopped the work "
        "briefly. When counting resumed the team kept morning and afternoon "
        "separate because school traffic changed the totals after three, and "
        "mixing those periods would have hidden the difference between commuter "
        "trips and short journeys made by pupils. The final table lists each "
        "observation and records the date.")
    result = module.scan(text)
    keys = {k for k in result if not k.startswith("_")}
    assert keys == {"32_catalog_leadin", "32_catalog_pivot"}
    assert {k.split("_", 1)[0] for k in keys} == {"32"}
    assert result["_metrics"]["ai_tell_score"] == 15


def test_an_archive_member_is_size_checked(tmp_path):
    module = detector()
    assert module._ZIP_MEMBER_CAP <= 64 * 1024 * 1024
    path = tmp_path / "big.docx"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", "<w:t>" + "a" * 200 + "</w:t>")
    assert isinstance(module.extract_office_text(str(path)), str)
