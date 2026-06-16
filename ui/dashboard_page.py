"""기존 전기차 충전소 사용량 대시보드 페이지.

CSV 기반 충전소 사용량 데이터를 불러와 지역 위치 지도, 지역별 사용량 차트,
충전 용량 필터를 한 화면에 렌더링한다.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st
from geopy.geocoders import Nominatim

import charger_capacity.capacity_filter as capacity_filter
import usage_chart.regional_usage_chart as regional_usage_chart
import usage_data.charger_usage_data as charger_usage_data
import usage_map.regional_location_map as regional_location_map


def render_dashboard_page() -> None:
    """지도, 사용량 차트, 충전용량 필터 화면을 렌더링한다.

    데이터 파일 경로를 구성하고 사용량 데이터를 로드한 뒤,
    지도와 차트, 충전 용량 필터 컴포넌트를 순서대로 출력한다.
    """
    st.title("전기차 충전소 사용량 지도")

    # 프로젝트 기준 경로에서 대시보드 입력 데이터와 좌표 캐시 파일 위치를 찾는다.
    project_root = Path(__file__).resolve().parents[1]
    data_dir = project_root / "data"
    csv_path = data_dir / "test_data.csv"
    coords_path = data_dir / "coords.csv"

    # 충전소 사용량 CSV를 읽고, 실제 사용량 값이 들어 있는 컬럼명을 함께 가져온다.
    df, usage_column = charger_usage_data.load_usage_data(csv_path)

    # 원본 데이터가 정상적으로 로드됐는지 빠르게 확인할 수 있도록 상위 5개 행을 보여준다.
    st.dataframe(df.head())

    # 좌표가 없는 지역명을 위도/경도로 변환할 때 사용할 지오코더를 준비한다.
    geolocator = Nominatim(
        user_agent="ev_charger_dashboard",
        timeout=10,
    )

    # 지역별 충전소 위치를 지도에 표시하고, 계산된 좌표는 coords.csv에 재사용한다.
    regional_location_map.render_region_location_map(
        df=df,
        data_dir=data_dir,
        coords_path=coords_path,
        geolocator=geolocator,
    )

    # 지역별 충전소 사용량을 차트로 시각화한다.
    regional_usage_chart.render_region_usage_chart(
        df=df,
        usage_column=usage_column,
    )

    # 충전 용량 기준으로 데이터를 필터링하고 선택 결과를 보여준다.
    capacity_filter.render_capacity_filter(
        df=df,
        usage_column=usage_column,
    )
