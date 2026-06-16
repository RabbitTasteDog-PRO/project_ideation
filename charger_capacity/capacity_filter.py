from __future__ import annotations

import streamlit as st


def render_capacity_filter(df, usage_column):
    st.divider()

    # 충전용량 필터 영역 제목
    st.subheader("충전용량 선택")
    # 원본 데이터를 별도로 복사
    filtered_df = df.copy()
    # 키로와트가 포함된 열만 찾기
    charger_columns = [
        column
        for column in filtered_df.columns
        if "키로와트" in column and column != usage_column
    ]

    # 사용자가 고른 용량을 저장
    selected_chargers = []

    # 체크박스를 세 열로 배치
    checkbox_columns = st.columns(3)

    # 충전용량마다 체크박스 생성
    for index, charger in enumerate(charger_columns):
        # 체크박스를 세 열에 나누어 배치
        with checkbox_columns[index % 3]:
            # 선택한 용량 열을 목록에 추가
            if st.checkbox(charger.strip(), value=index == 0):
                selected_chargers.append(charger)

    # 하나 이상의 용량이 선택됐는지 확인
    if selected_chargers:
        # 표에 보여줄 열 순서 지정
        display_columns = [
            "광역지자체",
            "시군구",
            *selected_chargers,
            usage_column,
        ]

        # 필터 대상 데이터 수 표시
        st.caption(f"선택된 데이터: {len(filtered_df):,}건")
        # 선택한 충전용량 열만 표시
        st.dataframe(
            filtered_df[display_columns],
            width="stretch",
            hide_index=True,
        )
    else:
        # 선택 항목이 없을 때 안내
        st.info("표시할 충전용량을 하나 이상 선택해주세요.")

    return selected_chargers
