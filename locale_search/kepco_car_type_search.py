"""한전 API 기반 지원 차종 조회 화면."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.kepco_api import (
    KepcoAPIError,
    get_kepco_ev_charge_data,
    kepco_items_to_dataframe,
    load_kepco_api_key,
)


def render_kepco_car_type_search(*, project_root: Path) -> None:
    """한전 API로 충전소별 지원 차종 데이터를 조회한다."""
    st.divider()
    st.subheader("한전 충전소 지원 차종 조회")

    st.caption(
        "한전 빅데이터 API에서 충전소명, 주소, 급속/완속 충전기 수, "
        "지원 차종(carType)을 조회합니다."
    )

    metro_col, city_col = st.columns(2)

    with metro_col:
        metro_cd = st.text_input(
            "광역시도 코드(metroCd)",
            value="11",
            max_chars=10,
        )

    with city_col:
        city_cd = st.text_input(
            "시군구 코드(cityCd)",
            value="11",
            max_chars=10,
        )

    if not st.button("한전 API 조회", key="fetch_kepco_car_type"):
        return

    api_key = load_kepco_api_key(project_root / ".env")

    if not api_key:
        st.warning(
            "한전 API 키가 없습니다. `.env.example`을 참고하여 "
            "`.env` 파일에 `KEPCO_API_KEY`를 입력해주세요."
        )
        return

    try:
        with st.spinner("한전 충전소 지원 차종 데이터를 조회하고 있습니다."):
            items = get_kepco_ev_charge_data(
                api_key=api_key,
                metro_cd=metro_cd.strip(),
                city_cd=city_cd.strip(),
            )
            kepco_df = kepco_items_to_dataframe(items)

    except KepcoAPIError as exc:
        st.error(str(exc))
        return

    if kepco_df.empty:
        st.info("조회된 한전 충전소 데이터가 없습니다.")
        return

    st.metric("조회 결과", f"{len(kepco_df):,}건")

    display_columns = [
        column
        for column in [
            "metro",
            "city",
            "stnPlace",
            "stnAddr",
            "rapidCnt",
            "slowCnt",
            "carType",
        ]
        if column in kepco_df.columns
    ]

    column_names = {
        "metro": "시/도",
        "city": "시군구",
        "stnPlace": "충전소명",
        "stnAddr": "주소",
        "rapidCnt": "급속",
        "slowCnt": "완속",
        "carType": "지원 차종",
    }

    st.dataframe(
        kepco_df[display_columns].rename(columns=column_names),
        hide_index=True,
        width="stretch",
    )
