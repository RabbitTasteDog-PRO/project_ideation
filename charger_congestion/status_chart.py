from __future__ import annotations

import pandas as pd
import streamlit as st


STATUS_LABELS = {
    "1": "통신 이상",
    "2": "충전 대기",
    "3": "충전 중",
    "4": "운영 중지",
    "5": "점검 중",
    "9": "상태 미확인",
}


def create_status_count_df(charger_data: pd.DataFrame) -> pd.DataFrame:
    # 상태 컬럼이 없으면 빈 표를 반환
    if charger_data.empty or "stat" not in charger_data.columns:
        return pd.DataFrame(columns=["상태", "충전기 수"])

    # 상태 코드를 문자열로 맞춰 코드별 개수를 계산
    status_counts = (
        charger_data["stat"]
        .astype(str)
        .value_counts()
        .rename_axis("상태코드")
        .reset_index(name="충전기 수")
    )

    # 상태 코드에 화면 표시용 라벨을 붙임
    status_counts["상태"] = status_counts["상태코드"].map(
        STATUS_LABELS
    ).fillna("기타")

    # 알려진 상태 코드 순서대로 그래프가 보이도록 정렬 기준 생성
    status_order = {
        status_code: index
        for index, status_code in enumerate(STATUS_LABELS)
    }
    status_counts["정렬순서"] = status_counts["상태코드"].map(
        status_order
    ).fillna(len(status_order))

    # 그래프에 필요한 컬럼만 반환
    return (
        status_counts.sort_values(["정렬순서", "상태코드"])
        [["상태", "충전기 수"]]
        .reset_index(drop=True)
    )


def render_status_count_chart(charger_data: pd.DataFrame) -> pd.DataFrame:
    # 상태별 충전기 개수 표를 생성
    status_count_df = create_status_count_df(charger_data)

    st.markdown("**충전기 상태별 개수**")

    # 상태 데이터가 없으면 안내 문구 표시
    if status_count_df.empty:
        st.info("상태별로 집계할 충전기 데이터가 없습니다.")
        return status_count_df

    # 상태별 충전기 개수를 막대그래프로 표시
    st.bar_chart(
        status_count_df,
        x="상태",
        y="충전기 수",
        x_label="충전기 상태",
        y_label="충전기 수",
    )

    return status_count_df
