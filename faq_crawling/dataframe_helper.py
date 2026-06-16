"""FAQ 크롤링 결과를 DataFrame으로 변환하는 도우미."""

from __future__ import annotations

from typing import Any

import pandas as pd


def questions_to_dataframe(results: list[dict[str, Any]]) -> pd.DataFrame:
    """크롤링 결과 리스트를 pandas DataFrame으로 변환합니다."""
    return pd.DataFrame(results)


def build_display_dataframe(question_df: pd.DataFrame) -> pd.DataFrame:
    """Streamlit 화면에 보여줄 최소 컬럼만 가진 DataFrame을 만듭니다."""
    if question_df.empty:
        return pd.DataFrame(columns=["인덱스", "제목", "링크"])

    return pd.DataFrame(
        {
            "인덱스": range(1, len(question_df) + 1),
            "제목": question_df["title"],
            "링크": question_df["url"],
        }
    )
