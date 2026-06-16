from __future__ import annotations

import re

import pandas as pd
import streamlit as st


ALL_OPTION = "전체"
DISTRICT_SUFFIXES = ("시", "군", "구")
SUB_DISTRICT_SUFFIXES = ("구", "군")
DONG_PATTERN = re.compile(r".+(동|읍|면|리|가)$")


def _split_address(address: str) -> list[str]:
    # 주소 문자열을 공백 기준으로 나누고 빈 값은 제거
    return [
        token.strip()
        for token in str(address).split()
        if token.strip()
    ]


def _remove_region_token(tokens: list[str], selected_region: str) -> list[str]:
    # 주소 첫 토큰이 선택한 시/도면 하위 행정구역만 남김
    if tokens and selected_region and tokens[0] == selected_region:
        return tokens[1:]

    return tokens


def _district_token_count(tokens: list[str]) -> int:
    # 도 단위 주소의 "시 구" 조합은 하나의 시군구로 취급
    if (
        len(tokens) >= 2
        and tokens[0].endswith("시")
        and tokens[1].endswith(SUB_DISTRICT_SUFFIXES)
    ):
        return 2

    # 일반적인 시/군/구 단위
    if tokens and tokens[0].endswith(DISTRICT_SUFFIXES):
        return 1

    return 0


def extract_district(address: str, selected_region: str = "") -> str:
    # 선택한 시/도 아래의 시군구를 주소에서 추출
    tokens = _split_address(address)
    tokens = _remove_region_token(tokens, selected_region)

    district_count = _district_token_count(tokens)

    if district_count == 0:
        return ""

    return " ".join(tokens[:district_count])


def extract_neighborhood(address: str, selected_region: str = "") -> str:
    # 시군구 뒤에서 동/읍/면/리/가로 끝나는 첫 토큰을 읍면동 단위로 사용
    tokens = _split_address(address)
    tokens = _remove_region_token(tokens, selected_region)
    district_count = _district_token_count(tokens)

    for token in tokens[district_count:]:
        if DONG_PATTERN.fullmatch(token):
            return token

    return ""


def add_location_columns(
    charger_data: pd.DataFrame,
    selected_region: str = "",
) -> pd.DataFrame:
    # 주소가 없으면 원본을 그대로 반환
    if charger_data.empty or "addr" not in charger_data.columns:
        return charger_data.copy()

    filtered_data = charger_data.copy()
    filtered_data["district"] = filtered_data["addr"].apply(
        lambda address: extract_district(address, selected_region)
    )
    filtered_data["neighborhood"] = filtered_data["addr"].apply(
        lambda address: extract_neighborhood(address, selected_region)
    )

    return filtered_data


def render_location_filter(
    charger_data: pd.DataFrame,
    *,
    key_suffix: str,
    selected_region: str,
    district_container=None,
    neighborhood_container=None,
) -> pd.DataFrame:
    # 주소에서 시군구/동 컬럼을 추가
    location_data = add_location_columns(charger_data, selected_region)

    if location_data.empty or "district" not in location_data.columns:
        return location_data

    district_options = [
        ALL_OPTION,
        *sorted(
            location_data["district"]
            .replace("", pd.NA)
            .dropna()
            .unique()
            .tolist()
        ),
    ]

    if district_container is None:
        district_container = st

    district_key = f"charger_district_{key_suffix}_{selected_region}"

    if st.session_state.get(district_key) not in district_options:
        st.session_state[district_key] = ALL_OPTION

    with district_container:
        selected_district = st.selectbox(
            "시군구",
            options=district_options,
            key=district_key,
        )

    district_filtered_data = location_data

    if selected_district != ALL_OPTION:
        district_filtered_data = district_filtered_data[
            district_filtered_data["district"] == selected_district
        ]

    neighborhood_options = [
        ALL_OPTION,
        *sorted(
            district_filtered_data["neighborhood"]
            .replace("", pd.NA)
            .dropna()
            .unique()
            .tolist()
        ),
    ]

    if neighborhood_container is None:
        neighborhood_container = st

    neighborhood_key = (
        f"charger_neighborhood_"
        f"{key_suffix}_{selected_region}_{selected_district}"
    )

    if st.session_state.get(neighborhood_key) not in neighborhood_options:
        st.session_state[neighborhood_key] = ALL_OPTION

    with neighborhood_container:
        selected_neighborhood = st.selectbox(
            "읍면동",
            options=neighborhood_options,
            key=neighborhood_key,
        )

    if selected_neighborhood != ALL_OPTION:
        district_filtered_data = district_filtered_data[
            district_filtered_data["neighborhood"] == selected_neighborhood
        ]

    return district_filtered_data


def render_disabled_location_filter(
    *,
    key_suffix: str,
    district_container=None,
    neighborhood_container=None,
) -> None:
    # API 조회 전에는 상세 지역 목록을 만들 수 없으므로 비활성 상태로 표시
    if district_container is None:
        district_container = st

    if neighborhood_container is None:
        neighborhood_container = st

    with district_container:
        st.selectbox(
            "시군구",
            options=[ALL_OPTION],
            disabled=True,
            key=f"charger_district_disabled_{key_suffix}",
        )

    with neighborhood_container:
        st.selectbox(
            "읍면동",
            options=[ALL_OPTION],
            disabled=True,
            key=f"charger_neighborhood_disabled_{key_suffix}",
        )
