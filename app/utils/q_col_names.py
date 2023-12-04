"""
Column names for q1, q2 etc.
e.g. q1_tokenized or q2_tokenized.
"""

from app.enums.question_code import QuestionCode


def get_lemmatized_col_name(q_code: QuestionCode) -> str:
    """Get lemmatized column name"""

    return f"{q_code.value}_lemmatized"


def get_tokenized_col_name(q_code: QuestionCode) -> str:
    """Get tokenized column name"""

    return f"{q_code.value}_tokenized"


def get_canonical_code_col_name(q_code: QuestionCode) -> str:
    """Get canonical code column name"""

    return f"{q_code.value}_canonical_code"


def get_parent_category_col_name(q_code: QuestionCode) -> str:
    """Get parent category column name"""

    return f"{q_code.value}_parent_category"


def get_raw_response_col_name(q_code: QuestionCode) -> str:
    """Get raw response column name"""

    return f"{q_code.value}_raw_response"


def get_label_col_name(q_code: QuestionCode) -> str:
    """Get label column name"""

    return f"{q_code.value}_label"


def get_count_col_name(q_code: QuestionCode) -> str:
    """Get count column name"""

    return f"{q_code.value}_count"


def get_code_col_name(q_code: QuestionCode) -> str:
    """Get code column name"""

    return f"{q_code.value}_code"


def get_description_col_name(q_code: QuestionCode) -> str:
    """Get description column name"""

    return f"{q_code.value}_description"


def get_original_language_col_name(q_code: QuestionCode) -> str:
    """Get original language column name"""

    return f"{q_code.value}_original_language"


def get_categories_set_col_name(q_code: QuestionCode) -> str:
    """Get categories set column name"""

    return f"{q_code.value}_categories_set"
