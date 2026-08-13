"""test_corpus.py: pytest entry point re-exporting validation_corpus's checks."""
from validation_corpus import (
    test_corpus_separation,
    test_windows_encoding_artifacts_are_not_ai_evidence,
)
