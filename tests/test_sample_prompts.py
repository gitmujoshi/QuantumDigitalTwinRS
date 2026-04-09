"""Catalog consistency (no PyO3)."""

from __future__ import annotations

from twin_sentry.sample_prompts import SAMPLE_PROMPTS, SIDEBAR_PRESETS, prompts_by_label


def test_sidebar_presets_non_empty() -> None:
    assert len(SIDEBAR_PRESETS) >= 4
    for _name, text in SIDEBAR_PRESETS.items():
        assert len(text.strip()) > 10


def test_sample_prompts_unique_labels() -> None:
    labels = [label for label, _ in SAMPLE_PROMPTS]
    assert len(labels) == len(set(labels))


def test_prompts_by_label_matches() -> None:
    m = prompts_by_label()
    assert len(m) == len(SAMPLE_PROMPTS)
    for label, text in SAMPLE_PROMPTS:
        assert m[label] == text
