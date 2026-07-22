from __future__ import annotations

from typing import Iterable


def levenshtein_distance(seq1: Iterable[str], seq2: Iterable[str]) -> int:
    a = list(seq1)
    b = list(seq2)

    if not a:
        return len(b)
    if not b:
        return len(a)

    previous_row = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current_row = [i]
        for j, cb in enumerate(b, start=1):
            insertion = previous_row[j] + 1
            deletion = current_row[j - 1] + 1
            substitution = previous_row[j - 1] + (0 if ca == cb else 1)
            current_row.append(min(insertion, deletion, substitution))
        previous_row = current_row

    return previous_row[-1]


def evaluate_pair(gt_text: str, pred_text: str) -> dict[str, float | int]:
    gt_chars = list(gt_text)
    pred_chars = list(pred_text)
    char_dist = levenshtein_distance(gt_chars, pred_chars)
    char_total = max(1, len(gt_chars))

    gt_words = gt_text.split()
    pred_words = pred_text.split()
    word_dist = levenshtein_distance(gt_words, pred_words)
    word_total = max(1, len(gt_words))

    return {
        "char_dist": char_dist,
        "char_total": char_total,
        "cer": char_dist / char_total,
        "word_dist": word_dist,
        "word_total": word_total,
        "wer": word_dist / word_total,
    }
