from __future__ import annotations

import streamlit as st


def render_region_usage_chart(df, usage_column):
    # 지역별 사용량 차트 영역
    st.divider()
    st.subheader("광역지자체별 전기차 충전소 사용량")

    # 지역별 사용량을 합산 후 정렬
    usage_by_region = (
        # 광역지자체별로 데이터 묶기
        df.groupby("광역지자체", as_index=False)[usage_column]
        # 지역별 사용량 합계 계산
        .sum()
        # 사용량이 큰 지역부터 정렬
        .sort_values(usage_column, ascending=False)
    )

    # 지역별 사용량 막대그래프 표시
    st.bar_chart(
        usage_by_region,
        x="광역지자체",
        y=usage_column,
        x_label="광역지자체",
        y_label="사용량(kWh)",
    )

    # 지역별 사용량을 표로 표시
    st.dataframe(
        usage_by_region,
        width="stretch",
        hide_index=True,
        # 사용량 열의 표시 방식을 설정
        column_config={
            usage_column: st.column_config.NumberColumn(
                "총 사용량(kWh)",
                format="localized",
            )
        },
    )

    return usage_by_region

