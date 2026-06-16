from __future__ import annotations

from pathlib import Path
import sys
from typing import Callable

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from charger_congestion.status_chart import render_status_count_chart
from locale_search.location_filter import (
    ALL_OPTION,
    add_location_columns,
    render_disabled_location_filter,
    render_location_filter,
)
from src.api import ChargerAPIError
from src.constants import AVAILABLE_STATUS_LABEL, REGION_CODES
from src.db import (
    DatabaseConfigError,
    DatabaseError,
    init_db,
    load_valid_locale_search_cache,
    save_locale_search_cache,
)
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

    # 기본 검색과 위치 이동 검색의 위젯 키를 분리
    key_suffix = "move" if enable_move_map else "basic"

    # 광역시도, 시군구, 읍면동 선택 영역을 한 줄로 표시
    st.markdown("**지역 선택**")
    region_col, district_col, neighborhood_col = st.columns(3)

    # 조회할 광역지역 선택
    with region_col:
        selected_region = st.selectbox(
            "시/도",
            options=list(REGION_CODES),
            key=f"available_charger_region_{key_suffix}",
        )

    # 환경설정 파일에서 API 키 읽기
    api_key = load_api_key(project_root / ".env")

    # 조회 결과를 세션에 저장할 키
    data_key = f"charger_search_data_{key_suffix}"
    region_key = f"charger_search_region_{key_suffix}"
    info_count_key = f"charger_search_info_count_{key_suffix}"
    status_count_key = f"charger_search_status_count_{key_suffix}"

    # 이전에 조회한 데이터 가져오기
    charger_data = st.session_state.get(data_key)
    # 이전에 조회한 지역 가져오기
    searched_region = st.session_state.get(region_key)

    region_code = REGION_CODES[selected_region]
    action_columns = st.columns(2)

    with action_columns[0]:
        load_from_db = st.button(
            "DB 불러오기",
            key=f"load_available_chargers_from_db_{key_suffix}",
        )

    with action_columns[1]:
        fetch_from_api = st.button(
            "API 조회/새로고침",
            type="primary",
            key=f"fetch_available_chargers_from_api_{key_suffix}",
        )

    if load_from_db:
        try:
            init_db(project_root)
            cached_result = load_valid_locale_search_cache(
                project_root,
                region_code,
            )

            if cached_result is None:
                st.info("최근 30분 이내 저장된 DB 데이터가 없습니다.")
            else:
                charger_data, saved_selection = cached_result
                searched_region = selected_region
                st.session_state[data_key] = charger_data
                st.session_state[region_key] = searched_region
                st.session_state[info_count_key] = 0
                st.session_state[status_count_key] = 0
                _restore_location_selection(
                    key_suffix=key_suffix,
                    selected_region=selected_region,
                    saved_selection=saved_selection,
                )
                st.success("DB에서 저장된 데이터를 불러왔습니다.")

        except DatabaseConfigError as exc:
            st.warning(str(exc))
        except DatabaseError as exc:
            st.error(str(exc))

    if fetch_from_api:
        if not api_key:
            st.warning(
                "API 키가 없습니다. `.env.example`을 참고하여 프로젝트 폴더에 "
                "`.env` 파일을 만들고 `EV_CHARGER_API_KEY`를 입력해주세요."
            )
        else:
            try:
                cached_loaders = (load_charger_info, load_charger_status)

                for cached_loader in cached_loaders:
                    clear_cache = getattr(cached_loader, "clear", None)
                    if callable(clear_cache):
                        clear_cache()

                with st.spinner("충전소 정보와 실시간 상태를 조회하고 있습니다."):
                    info_items = load_charger_info(api_key, region_code)
                    status_items = load_charger_status(api_key, region_code)
                    charger_data = merge_charger_data(info_items, status_items)
                    charger_data = add_location_columns(
                        charger_data,
                        selected_region,
                    )
                    searched_region = selected_region
                    st.session_state[data_key] = charger_data
                    st.session_state[region_key] = searched_region
                    st.session_state[info_count_key] = len(info_items)
                    st.session_state[status_count_key] = len(status_items)

                st.success("API에서 데이터를 조회했습니다.")

            except ChargerAPIError as exc:
                st.error(str(exc))

    # 시/도가 바뀌면 이전 지역의 결과를 화면에 섞어 보여주지 않음
    if searched_region != selected_region:
        charger_data = None

    # 아직 조회하거나 불러온 데이터가 없으면 하위 필터만 비활성 표시
    if charger_data is None:
        render_disabled_location_filter(
            key_suffix=key_suffix,
            district_container=district_col,
            neighborhood_container=neighborhood_col,
        )
        return

    # 아직 조회하지 않았거나 현재 선택 지역의 결과가 아니면 종료
    if charger_data is None or searched_region != selected_region:
        render_disabled_location_filter(
            key_suffix=key_suffix,
            district_container=district_col,
            neighborhood_container=neighborhood_col,
        )
        return

    # 조회 결과가 비었는지 확인
    if charger_data.empty:
        render_disabled_location_filter(
            key_suffix=f"{key_suffix}_empty",
            district_container=district_col,
            neighborhood_container=neighborhood_col,
        )
        st.info("최근 상태 정보가 있는 충전기를 찾지 못했습니다.")
        return

    # 조회된 지역 안에서 시군구와 읍면동을 한 번 더 선택
    filtered_charger_data = render_location_filter(
        charger_data,
        key_suffix=key_suffix,
        selected_region=selected_region,
        district_container=district_col,
        neighborhood_container=neighborhood_col,
    )

    # 선택한 지역 조건과 현재 조회 데이터를 DB에 저장
    if st.button(
        "DB 저장",
        key=f"save_available_chargers_to_db_{key_suffix}",
    ):
        selected_district, selected_neighborhood = _get_location_selection(
            key_suffix=key_suffix,
            selected_region=selected_region,
        )

        try:
            init_db(project_root)
            save_locale_search_cache(
                project_root,
                region_code=region_code,
                region_name=selected_region,
                selected_district=selected_district,
                selected_neighborhood=selected_neighborhood,
                info_count=st.session_state.get(info_count_key, 0),
                status_count=st.session_state.get(status_count_key, 0),
                charger_data=charger_data,
            )
            st.success("현재 데이터와 선택한 지역 조건을 DB에 저장했습니다.")
        except DatabaseConfigError as exc:
            st.warning(str(exc))
        except DatabaseError as exc:
            st.error(str(exc))

    # 상세 지역 조건에 맞는 데이터가 없으면 안내 후 종료
    if filtered_charger_data.empty:
        st.info("선택한 상세 지역에 해당하는 충전기 데이터가 없습니다.")
        return

    # 조회된 전체 충전기 데이터로 상태별 개수를 표시
    render_status_count_chart(filtered_charger_data)

    # 조회된 충전용량 목록 생성
    output_options = get_output_options(filtered_charger_data)
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
        filtered_charger_data,
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


def _get_location_selection(
    *,
    key_suffix: str,
    selected_region: str,
) -> tuple[str | None, str | None]:
    district_key = f"charger_district_{key_suffix}_{selected_region}"
    selected_district = st.session_state.get(district_key, ALL_OPTION)

    neighborhood_key = (
        f"charger_neighborhood_"
        f"{key_suffix}_{selected_region}_{selected_district}"
    )
    selected_neighborhood = st.session_state.get(
        neighborhood_key,
        ALL_OPTION,
    )

    return selected_district, selected_neighborhood


def _restore_location_selection(
    *,
    key_suffix: str,
    selected_region: str,
    saved_selection: dict[str, str | None],
) -> None:
    selected_district = (
        saved_selection.get("selected_district")
        or ALL_OPTION
    )
    selected_neighborhood = (
        saved_selection.get("selected_neighborhood")
        or ALL_OPTION
    )

    district_key = f"charger_district_{key_suffix}_{selected_region}"
    neighborhood_key = (
        f"charger_neighborhood_"
        f"{key_suffix}_{selected_region}_{selected_district}"
    )

    st.session_state[district_key] = selected_district
    st.session_state[neighborhood_key] = selected_neighborhood
