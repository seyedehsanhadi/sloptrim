"""test_office.py: text must come out of real zip-based documents, with no dependencies."""
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import detect

SLOP = ("In today's fast-paced digital landscape, it is crucial to delve into the "
        "multifaceted tapestry of pivotal solutions. This comprehensive guide will "
        "showcase a robust, seamless framework that empowers teams to unlock their "
        "full potential. It is not just a tool, it is a game-changer.")

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
ODF_T = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
ODF_O = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"


def _paras(text):
    return [s.strip() + "." for s in text.split(". ") if s.strip()]


def make_docx(path, text=SLOP):
    body = "".join('<w:p><w:r><w:t>%s</w:t></w:r></w:p>' % p for p in _paras(text))
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types/>')
        z.writestr("word/document.xml",
                   '<?xml version="1.0"?><w:document xmlns:w="%s"><w:body>%s</w:body></w:document>'
                   % (W, body))
    return path


def make_pptx(path, text=SLOP):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types/>')
        for i, p in enumerate(_paras(text), 1):
            z.writestr("ppt/slides/slide%d.xml" % i,
                       '<?xml version="1.0"?><sld xmlns:a="%s"><a:p><a:r><a:t>%s</a:t></a:r></a:p></sld>'
                       % (A, p))
    return path


def make_xlsx(path, text=SLOP):
    items = "".join("<si><t>%s</t></si>" % p for p in _paras(text))
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types/>')
        z.writestr("xl/sharedStrings.xml",
                   '<?xml version="1.0"?><sst xmlns="%s">%s</sst>' % (P, items))
    return path


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


def make_odf(path, text=SLOP):
    body = "".join('<text:p>%s</text:p>' % p for p in _paras(text))
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/vnd.oasis.opendocument.text")
        z.writestr("content.xml",
                   '<?xml version="1.0"?><office:document-content xmlns:office="%s" '
                   'xmlns:text="%s"><office:body><office:text>%s</office:text>'
                   '</office:body></office:document-content>' % (ODF_O, ODF_T, body))
    return path


BUILDERS = [("docx", make_docx), ("pptx", make_pptx),
            ("xlsx", make_xlsx), ("odt", make_odf),
            ("odp", make_odf), ("ods", make_odf)]


@pytest.mark.parametrize("ext,build", BUILDERS)
def test_text_comes_out(tmp_path, ext, build):
    p = build(tmp_path / ("sample." + ext))
    text = detect.read_input([str(p)])
    assert "delve" in text, "%s: extraction lost the body text" % ext
    assert "game-changer" in text, "%s: extraction truncated the document" % ext
    assert "<" not in text, "%s: xml markup leaked into the text" % ext


@pytest.mark.parametrize("ext,build", BUILDERS)
def test_slop_is_scored(tmp_path, ext, build):
    p = build(tmp_path / ("sample." + ext))
    score = detect.scan(detect.read_input([str(p)]))["_metrics"]["ai_tell_score"]
    assert score >= 40, "%s: dense slop scored only %d" % (ext, score)


def test_xlsx_shared_and_inline_strings_are_read(tmp_path):
    shared = detect.read_input([str(make_xlsx(tmp_path / "shared.xlsx"))])
    inline = detect.read_input([str(make_inline_xlsx(tmp_path / "inline.xlsx"))])
    assert "delve" in shared and "game-changer" in shared
    assert "delve" in inline and "game-changer" in inline


def test_human_prose_in_a_docx_is_not_flagged(tmp_path):
    human = ("The bridge carried coal until 1958. Its six arches were built from "
             "stone quarried two miles upstream, and the mortar has been repointed "
             "twice, once in 1904 and again after the flood. Nobody has found the "
             "original drawings. What survives is a contractor's invoice and a "
             "photograph of the opening, taken from the far bank.")
    p = make_docx(tmp_path / "human.docx", human)
    score = detect.scan(detect.read_input([str(p)]))["_metrics"]["ai_tell_score"]
    assert score < 40, "human prose in a docx scored %d" % score


def test_a_broken_archive_reports_an_error_and_no_traceback(tmp_path):
    """The invocation the README documents, on a file that is not a zip: a
    renamed .doc, a truncated download, a Word lock file."""
    p = tmp_path / "broken.docx"
    p.write_bytes(b"this is not a zip file")
    r = subprocess.run([sys.executable, str(REPO / "scripts" / "detect.py"), str(p)],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 1, "expected a clean failure, got %d" % r.returncode
    assert "Traceback" not in r.stderr, r.stderr
    assert "error" in json.loads(r.stderr), r.stderr


def test_an_empty_archive_returns_empty(tmp_path):
    p = tmp_path / "empty.docx"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types/>')
    assert detect.read_input([str(p)]) == ""


def test_pdf_is_not_claimed(tmp_path):
    assert ".pdf" not in detect._ZIP_DOC, (
        "PDF is not a zip archive and has no stdlib parser; it must not be listed "
        "as supported")
