"""Meaning-preserving comparisons and source-position checks; no service calls."""
import math
import unicodedata


def exact_text(text):
    """Allow whitespace reflow; retain case, signs, decimals, units and punctuation."""
    return ' '.join(unicodedata.normalize('NFC', text).split())


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def check_words(text, words):
    """Verify ordered source spans, timing and coverage of meaning-bearing characters.

    Providers may omit sentence punctuation from word events. Numeric separators,
    signs, currency, ratios, units and letters must still be represented. Use
    explicitly spoken numbers in narration if a provider cannot align a symbol.
    """
    if not words:
        raise ValueError('No measured words')
    covered = set()
    cursor, previous_time = 0, 0.
    for word in words:
        a, b = word['charStart'], word['charEnd']
        if not (type(a) is int and type(b) is int and cursor <= a < b <= len(text)):
            raise ValueError('Word source positions overlap or are invalid')
        if text[a:b].casefold() != word['text'].casefold():
            raise ValueError('Word source positions differ from narration')
        if not (finite(word['start']) and finite(word['end'])
                and previous_time <= word['start'] < word['end']):
            raise ValueError('Word timings overlap or are invalid')
        covered.update(range(a, b))
        cursor, previous_time = b, word['end']
    for i, character in enumerate(text):
        if i in covered:
            continue
        category = unicodedata.category(character)
        significant = character.isalnum() or category[0] == 'M' or category in {'Sc', 'Sm'}
        significant |= character in '%‰/\\^'
        if character in '.,' and 0 < i < len(text) - 1:
            significant |= text[i - 1].isdigit() and text[i + 1].isdigit()
        if character in '-−+' and text[i + 1:].lstrip()[:1].isdigit():
            significant = True
        if significant:
            raise ValueError(f'Meaning-bearing narration character is not aligned at position {i}')
