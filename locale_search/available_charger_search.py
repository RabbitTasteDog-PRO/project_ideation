from __future__ import annotations

from pathlib import Path
from typing import Callable

import pandas as pd
import streamlit as st

from src.api import ChargerAPIError
from src.constants import AVAILABLE_STATUS_LABEL, REGION_CODES
from src.preprocess import (
    filter_available_chargers,
    get_output_options,
    merge_charger_data,
)


def render_available_charger_search(
    *,
    project_root: Path,
    load_api_key: Callable[[Path], str | None],
    load_charger_info: Callable[[str, str], list[dict[str, str]]],
    load_charger_status: Callable[[str, str], list[dict[str, str]]],
    render_available_charger_table: Callable[[pd.DataFrame, str], pd.Series | None],
    render_available_charger_map: Callable[[pd.DataFrame, pd.Series | None], None],
    enable_move_map: bool = False,
) -> None:
    # 위치 이동 기능 사용 여부에 따라 제목 변경
    title = (
        "현재 사용 가능한 충전기 찾기:위치이동가능"
        if enable_move_map
        else "현재 사용 가능한 충전기 찾기"
    )

    # 검색 영역 구분선과 제목 표시
    st.divider()
    st.subheader(title)

    # 검색 기능의 기준을 설명
    st.caption(
        "선택한 지역에서 최근 10분 이내 상태가 갱신된 "
        f"'{AVAILABLE_STATUS_LABEL}' 충전기를 조회합니다."
    )

    # 환경설정 파일에서 API 키 읽기
    api_key = load_api_key(project_root / ".env")

    # API 키가 있는지 확인
    if not api_key:
        # API 키 설정 방법 안내
        st.warning(
            "API 키가 없습니다. `.env.example`을 참고하여 프로젝트 폴더에 "
            "`.env` 파일을 만들고 `EV_CHARGER_API_KEY`를 입력해주세요."
        )
        return

    # 기본 검색과 위치 이동 검색의 위젯 키를 분리
    key_suffix = "move" if enable_move_map else "basic"

    # 조회할 광역지역 선택
    selected_region = st.selectbox(
        "지역",
        options=list(REGION_CODES),
        key=f"available_charger_region_{key_suffix}",
    )

    # 조회 버튼을 눌렀는지 확인
    if st.button(
        "사용 가능한 충전기 조회",
        type="primary",
        key=f"search_available_chargers_{key_suffix}",
    ):
        # API 오류를 화면에 표시
        try:
            # 조회 중 로딩 문구 표시
            with st.spinner("충전소 정보와 실시간 상태를 조회하고 있습니다."):
                # 지역명을 API 코드로 변환
                region_code = REGION_CODES[selected_region]
                # 충전소 기본정보 조회
                info_items = load_charger_info(api_key, region_code)
                # 충전기 실시간 상태 조회
                status_items = load_charger_status(api_key, region_code)
                # 두 API 결과를 합쳐 저장
                st.session_state[f"charger_search_data_{key_suffix}"] = (
                    merge_charger_data(info_items, status_items)
                )
                # 조회한 지역도 함께 저장
                st.session_state[f"charger_search_region_{key_suffix}"] = (
                    selected_region
                )

        # API 전용 오류 메시지 처리
        except ChargerAPIError as exc:
            st.error(str(exc))

    # 이전에 조회한 데이터 가져오기
    charger_data = st.session_state.get(f"charger_search_data_{key_suffix}")
    # 이전에 조회한 지역 가져오기
    searched_region = st.session_state.get(
        f"charger_search_region_{key_suffix}"
    )

    # 아직 조회하지 않았거나 현재 선택 지역의 결과가 아니면 종료
    if charger_data is None or searched_region != selected_region:
        return

    # 조회 결과가 비었는지 확인
    if charger_data.empty:
        st.info("최근 상태 정보가 있는 충전기를 찾지 못했습니다.")
        return

    # 조회된 충전용량 목록 생성
    output_options = get_output_options(charger_data)
    # 선택 용량을 담을 빈 목록
    selected_outputs = []

    # 충전용량 항목이 있을 때 표시
    if output_options:
        st.markdown("**충전용량 선택**")
        # 체크박스를 네 열로 배치
        output_columns = st.columns(4)

        # 용량마다 체크박스 생성
        for index, output in enumerate(output_options):
            # 화면에 표시할 용량 문구
            label = f"{output:g} kW"
            # 체크박스를 네 열에 분배
            with output_columns[index % 4]:
                # 선택한 용량을 목록에 추가
                if st.checkbox(
                    label,
                    value=True,
                    key=f"api_output_{key_suffix}_{selected_region}_{output}",
                ):
                    selected_outputs.append(output)

    # 대기 상태와 용량으로 필터링
    available_df = filter_available_chargers(
        charger_data,
        selected_outputs,
    )

    # 요약 수치를 두 열로 배치
    metric_columns = st.columns(2)
    # 사용 가능한 충전기 수 표시
    metric_columns[0].metric(
        "사용 가능한 충전기",
        f"{len(available_df):,}대",
    )
    # 중복을 뺀 충전소 수 표시
    metric_columns[1].metric(
        "충전소",
        (
            f"{available_df['statId'].nunique():,}곳"
            if "statId" in available_df.columns
            else "0곳"
        ),
    )

    # 용량 데이터가 없는 경우 안내
    if not output_options:
        st.info("조회된 데이터에 충전용량 정보가 없습니다.")
        return

    # 체크박스를 모두 해제한 경우
    if not selected_outputs:
        st.info("충전용량을 하나 이상 선택해주세요.")
        return

    # 조건에 맞는 결과가 없는 경우
    if available_df.empty:
        st.info("선택 조건에 맞는 사용 가능한 충전기가 없습니다.")
        return

    # 사용 가능한 충전기 지도 표시
    selected_row = render_available_charger_table(
        available_df,
        key_suffix,
    )

    if enable_move_map:
        render_available_charger_map(
            available_df,
            selected_row,
        )
    else:
        render_available_charger_map(
            available_df,
            None,
        )
