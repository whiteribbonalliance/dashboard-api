from app.enums.question_code import QuestionCode


def get_lemmatized_col_name(q_code: QuestionCode) -> str:
    """Get lemmatized column name"""

    return f"q{q_code.value}_lemmatized"


def get_tokenized_col_name(q_code: QuestionCode) -> str:
    """Get tokenized column name"""

    return f"q{q_code.value}_tokenized"


def get_canonical_code_col_name(q_code: QuestionCode) -> str:
    """Get canonical code column name"""

    return f"q{q_code.value}_canonical_code"


def get_top_level_col_name(q_code: QuestionCode) -> str:
    """Get top level column name"""

    return f"q{q_code.value}_top_level"


def get_raw_response_col_name(q_code: QuestionCode) -> str:
    """Get raw response column name"""

    return f"q{q_code.value}_raw_response"


def get_label_col_name(q_code: QuestionCode) -> str:
    """Get label column name"""

    return f"q{q_code.value}_label"


def get_count_col_name(q_code: QuestionCode) -> str:
    """Get count column name"""

    return f"q{q_code.value}_count"


def get_code_col_name(q_code: QuestionCode) -> str:
    """Get code column name"""

    return f"q{q_code.value}_code"


def get_description_col_name(q_code: QuestionCode) -> str:
    """Get description column name"""

    return f"q{q_code.value}_description"


def get_original_language_col_name(q_code: QuestionCode) -> str:
    """Get original language column name"""

    return f"q{q_code.value}_original_language"
