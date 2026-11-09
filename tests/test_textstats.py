from toolbox_bot.textstats import analyze, format_stats, words


def test_basic_counts():
    s = analyze("The cat sat. The cat ran!\nDone?")
    assert s.words == 7
    assert s.unique_words == 5
    assert s.sentences == 3
    assert s.lines == 2
    assert s.top_words[0] == ("cat", 2)


def test_persian_words_and_apostrophes():
    assert words("سلام دنیا") == ["سلام", "دنیا"]
    assert words("don't stop") == ["don't", "stop"]


def test_empty_text():
    s = analyze("")
    assert (s.words, s.sentences, s.lines, s.characters) == (0, 0, 0, 0)
    assert "Top words" not in format_stats(s)


def test_reading_time():
    assert analyze("word " * 200).reading_seconds == 60


def test_format_contains_fields():
    out = format_stats(analyze("Hello hello world."))
    assert "Words: 3 (2 unique)" in out
    assert "Top words: hello ×2, world ×1" in out
