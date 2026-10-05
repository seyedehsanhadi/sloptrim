"""Real file/CLI and hook processes; host event delivery is a separate check."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from xml.sax.saxutils import escape
from zipfile import ZipFile

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import detect
from test_office import make_docx, make_pptx, make_xlsx, make_odf, make_epub

SLOP = ("Great question! In today's fast-paced world, our comprehensive guide serves "
        "as a testament to the transformative power of leveraging cutting-edge solutions. "
        "It's not just about tools; it's about unlocking unprecedented value. It is worth "
        "noting that experts argue this journey is just beginning, paving the way for a "
        "brighter future. In conclusion, the future looks bright. I hope this helps!")
CLEAN = ("The parser reads one token at a time. If it sees an opening brace it pushes "
         "a new scope onto the stack. Closing braces pop it. Errors bubble up as "
         "exceptions, which the caller catches and reports with a line number. "
         "Most failures in practice come from unterminated strings.")


def hook(name, payload, workspace, mode='full'):
    state = workspace.parent / (workspace.name + '-state')
    state.mkdir(exist_ok=True)
    env = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(ROOT), CLAUDE_CONFIG_DIR=str(state),
               SLOPTRIM_DEFAULT_MODE=mode, PYTHONDONTWRITEBYTECODE='1')
    r = subprocess.run(['node', str(ROOT / 'hooks' / name)], input=json.dumps(payload),
                       text=True, encoding='utf-8', capture_output=True, cwd=workspace,
                       env=env, timeout=35)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout) if r.stdout.strip() else None


def create(path, text):
    ext = path.suffix
    if ext in ('.docx', '.docm'): make_docx(path, text)
    elif ext in ('.pptx', '.pptm'): make_pptx(path, text)
    elif ext in ('.xlsx', '.xlsm'): make_xlsx(path, text)
    elif ext in ('.odt', '.odp', '.ods'): make_odf(path, text)
    elif ext == '.epub': make_epub(path, text)
    elif ext == '.ipynb': path.write_text(json.dumps({'cells':[{'cell_type':'markdown','source':[text]}, {'cell_type':'code','source':[SLOP]}]}), encoding='utf-8')
    elif ext == '.tex': path.write_text('\\documentclass{article}\n\\begin{document}\n' + text + '\n\\end{document}\n', encoding='utf-8')
    else: path.write_text(text, encoding='utf-8')


FORMATS = ['.md', '.mdx', '.markdown', '.txt', '.text', '.rst', '.tex', '.org', '.adoc',
           '.docx', '.docm', '.pptx', '.pptm', '.xlsx', '.xlsm', '.odt', '.odp', '.ods', '.epub', '.ipynb']


@pytest.mark.parametrize('ext', FORMATS)
def test_all_advertised_formats_reach_cli_and_saved_file_guard(tmp_path, ext):
    path = tmp_path / ('article' + ext)
    for text, should_warn in [(SLOP, True), (CLEAN, False)]:
        create(path, text)
        before = path.read_bytes()
        r = subprocess.run([sys.executable, str(ROOT / 'scripts/detect.py'), str(path)], capture_output=True, timeout=8)
        assert r.returncode == 0, r.stderr
        score = json.loads(r.stdout)['_metrics']['ai_tell_score']
        assert (score > 40) == should_warn
        result = hook('sloptrim-guard.js', {'cwd':str(tmp_path),'session_id':'formats',
                       'tool_name':'Write','tool_input':{'file_path':str(path)}}, tmp_path)
        assert bool(result) == should_warn
        assert path.read_bytes() == before, 'The checker must never rewrite an artifact'


@pytest.mark.parametrize('literal', [
    '$\\mathrm{' + SLOP + '}$', '\\[' + SLOP + '\\]',
    '\\begin{verbatim}\n' + SLOP + '\n\\end{verbatim}',
    '\\begin{minted}{python}\n' + SLOP + '\n\\end{minted}',
    '\\newcommand{\\catchphrase}[1]{' + SLOP + '}',
    '% ' + SLOP, '\\verb|' + SLOP + '|',
    '\\cite{' + SLOP + '}',
    '\\lstinline|' + SLOP + '|', '\\lstinline[language=Python]|' + SLOP + '|',
    '\\mintinline{python}{' + SLOP + '}', '\\mintinline[breaklines]{python}|' + SLOP + '|',
    '\\\\% ' + SLOP,
])
def test_tex_syntax_is_not_prose_but_visible_body_still_is(tmp_path, literal):
    path = tmp_path / 'article.tex'
    path.write_text(literal + '\n' + CLEAN, encoding='utf-8')
    out = hook('sloptrim-guard.js', {'cwd':str(tmp_path),'session_id':'tex',
               'tool_input':{'file_path':str(path)}}, tmp_path)
    assert out is None
    report = detect.scan(path.read_text(encoding='utf-8'), syntax='latex')
    assert '1_ai_vocabulary' not in report
    assert '1_ai_vocabulary' in detect.scan(literal + '\n' + SLOP, syntax='latex')


def test_tex_clean_preserves_syntax_math_and_literal_bytes(tmp_path):
    text = ('\\documentclass{article}\n\\newcommand{\\name}{a\u200bb}\n'
            '\\begin{document}\nThe re\u200bport is ready.\n'
            '$a\u2062b$ and \\verb|a\u200bb|.\n'
            '\\begin{verbatim}\nx="a\u200bb"  \n\\end{verbatim}\n'
            '\\cite{p\u0430per}\n\\end{document}\n')
    path = tmp_path / 'article.tex'
    source = text.replace('\n', '\r\n').encode('utf-8')
    path.write_bytes(source)
    out = subprocess.run([sys.executable, str(ROOT/'scripts/detect.py'), '--clean', str(path)],capture_output=True,timeout=8)
    assert out.returncode == 0, out.stderr
    assert out.stdout == source.replace('re\u200bport'.encode(), b'report')
    assert path.read_bytes() == source


def test_tex_unclosed_math_cannot_hide_later_paragraphs():
    for opener in ('$', '$$', r'\(', r'\['):
        assert '1_ai_vocabulary' in detect.scan('It costs ' + opener + '5 today.\n\n' + SLOP, syntax='latex')
    assert '1_ai_vocabulary' not in detect.scan('$x$\n\n$' + SLOP.replace('.', '') + '$', syntax='latex')


def test_tex_escape_parity_and_visible_labels():
    assert '1_ai_vocabulary' in detect.scan(r'\$10. ' + SLOP,syntax='latex')
    assert '1_ai_vocabulary' in detect.scan(r'$$x\\$$ ' + SLOP,syntax='latex')
    assert '1_ai_vocabulary' in detect.scan(r'\href{https://example.org}{'+SLOP+'}',syntax='latex')


@pytest.mark.parametrize('properties', [
    '<w:pPr><w:pStyle w:val="Code"/></w:pPr><w:r>',
    '<w:r><w:rPr><w:rStyle w:val="CodeChar"/></w:rPr>',
])
def test_docx_marked_code_is_excluded_without_mutating_the_document(tmp_path, properties):
    p=tmp_path/'code.docx'
    xml=('<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
         '<w:body><w:p>'+properties+'<w:t>'+escape(SLOP)+' a\u200bb</w:t></w:r></w:p>'
         '<w:p><w:r><w:t>'+CLEAN+'</w:t></w:r></w:p></w:body></w:document>')
    with ZipFile(p,'w') as z:z.writestr('word/document.xml',xml)
    original=p.read_bytes()
    text=detect.read_input([str(p)])
    assert SLOP not in text and CLEAN in text
    result=hook('sloptrim-guard.js',{'cwd':str(tmp_path),'session_id':'word-code',
                'tool_input':{'file_path':str(p)}},tmp_path)
    assert result is None and p.read_bytes()==original


def test_docx_monospace_manuscript_is_still_readable(tmp_path):
    p=tmp_path/'manuscript.docx'
    xml=('<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
         '<w:body><w:p><w:r><w:rPr><w:rFonts w:ascii="Courier New"/></w:rPr>'
         '<w:t>'+escape(SLOP)+'</w:t></w:r></w:p></w:body></w:document>')
    with ZipFile(p,'w') as z:z.writestr('word/document.xml',xml)
    assert SLOP in detect.read_input([str(p)])
    assert detect.scan(detect.read_input([str(p)]))['_metrics']['ai_tell_score']>40
