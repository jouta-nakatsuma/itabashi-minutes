
from ingest.text_normalizer import JapaneseTextNormalizer

def test_quote_and_bracket_normalization():
    s = "“（高島平）”"
    got = JapaneseTextNormalizer().normalize(s)
    # 例: 期待値（実装の仕様に合わせて調整）
    assert got == '" (高島平)"'
