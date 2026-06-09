from paper_agent.text_utils import keywords, normalize_space, safe_filename, score_text, split_sentences


def test_normalize_space_collapses_whitespace() -> None:
    # 换行、多个空格和制表符都应该被压缩成一个普通空格。
    assert normalize_space("a\n\n  b\tc") == "a b c"


def test_keywords_are_unique_and_lowercase() -> None:
    # 关键词需要小写、去重，并过滤长度小于 3 的短词。
    assert keywords("RAG RAG Retrieval AI") == ["rag", "retrieval"]


def test_split_sentences_returns_chunks() -> None:
    # 句号和感叹号后的空白会被当作句子边界。
    assert split_sentences("One sentence. Another one!") == ["One sentence.", "Another one!"]


def test_score_text_counts_terms() -> None:
    # rag 出现 2 次，retrieval 出现 2 次，所以总分是 4。
    assert score_text("RAG uses retrieval. Retrieval helps RAG.", ["rag", "retrieval"]) == 4


def test_safe_filename_removes_unsafe_characters() -> None:
    # 斜杠、冒号和空格不适合直接做文件名，所以会被转换成下划线。
    assert safe_filename("2301.12345/v2: bad") == "2301.12345_v2_bad"
