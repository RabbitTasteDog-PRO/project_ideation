# 파일과 폴더 경로를 안전하게 다루기 위한 도구
from pathlib import Path

# Streamlit 화면을 만들기 위한 라이브러리
import streamlit as st
# 주소를 좌표로 변환하기 위한 지오코더
from geopy.geocoders import Nominatim

# 사용 가능한 충전기 지도 렌더링 모듈
import available_charger_view.map as available_map
# 사용 가능한 충전기 표 렌더링 모듈
import available_charger_view.table as available_table
# 공공데이터 API 결과 캐시 모듈
import charger_api_cache.cached_api as cached_api
# 충전용량 필터 화면 모듈
import charger_capacity.capacity_filter as capacity_filter
# 지역 기반 사용 가능 충전기 검색 모듈
import locale_search.available_charger_search as available_charger_search
# 지역별 사용량 차트 모듈
import usage_chart.regional_usage_chart as regional_usage_chart
# CSV 사용량 데이터 로딩 모듈
import usage_data.charger_usage_data as charger_usage_data
# 지역 좌표 지도 화면 모듈
import usage_map.regional_location_map as regional_location_map
# .env에서 API 키를 읽는 함수
from src.api import load_api_key


# 충전소 기본정보 API 캐시 함수를 짧은 이름으로 연결
load_charger_info = cached_api.load_charger_info
# 충전기 상태정보 API 캐시 함수를 짧은 이름으로 연결
load_charger_status = cached_api.load_charger_status
# 사용량 CSV 로딩 함수를 짧은 이름으로 연결
usage_data = charger_usage_data.load_usage_data
# 지역 좌표 지도 렌더링 함수를 짧은 이름으로 연결
region_map = regional_location_map.render_region_location_map
# 지역별 사용량 차트 렌더링 함수를 짧은 이름으로 연결
usage_chart = regional_usage_chart.render_region_usage_chart
# 충전용량 필터 렌더링 함수를 짧은 이름으로 연결
capacity = capacity_filter.render_capacity_filter
# 사용 가능한 충전기 지도 렌더링 함수를 짧은 이름으로 연결
available_charger_map = available_map.render_available_charger_map
# 사용 가능한 충전기 표 렌더링 함수를 짧은 이름으로 연결
available_charger_table = available_table.render_available_charger_table
# 지역 기반 사용 가능 충전기 검색 화면을 짧은 이름으로 연결
locale_search = available_charger_search.render_available_charger_search


# 앱의 가장 큰 제목 표시
st.title("전기차 충전소 사용량 지도")

# app.py가 있는 프로젝트 루트를 기준으로 경로 설정
project_root = Path(__file__).resolve().parent
# 데이터 파일이 들어 있는 폴더 경로
data_dir = project_root / "Data"
# 사용량 CSV 파일 경로
csv_path = data_dir / "test_data.csv"
# 저장된 좌표 CSV 파일 경로
coords_path = data_dir / "coords.csv"

# CSV 데이터를 읽고 사용량 열 이름을 함께 받음
df, usage_column = usage_data(csv_path)

# 원본 데이터의 앞부분 표시
st.dataframe(df.head())

# 주소를 좌표로 바꿀 도구 생성
geolocator = Nominatim(
    # 서비스 식별용 앱 이름
    user_agent="ev_charger_dashboard",
    # 좌표 검색 제한시간 설정
    timeout=10,
)

# 지역 주소 좌표를 만들고 지도와 좌표 표를 표시
region_map(
    # 지도에 표시할 사용량 데이터
    df=df,
    # 좌표 파일을 저장할 데이터 폴더
    data_dir=data_dir,
    # 재사용할 좌표 CSV 파일 경로
    coords_path=coords_path,
    # 주소를 위도/경도로 변환할 지오코더
    geolocator=geolocator,
)

# 광역지자체별 총 사용량 막대그래프와 표를 표시
usage_chart(
    # 차트에 사용할 사용량 데이터
    df=df,
    # 합산 기준이 되는 사용량 열 이름
    usage_column=usage_column,
)

# 충전용량 체크박스 필터와 상세 표를 표시
capacity(
    # 필터링할 사용량 데이터
    df=df,
    # 표에 함께 보여줄 사용량 열 이름
    usage_column=usage_column,
)

# 기존 방식의 현재 사용 가능한 충전기 검색 영역 표시
# locale_search(
#     project_root=project_root,
#     load_api_key=load_api_key,
#     load_charger_info=load_charger_info,
#     load_charger_status=load_charger_status,
#     render_available_charger_table=available_charger_table,
#     render_available_charger_map=available_charger_map,
#     enable_move_map=False,
# )

# 위치 이동이 가능한 현재 사용 가능한 충전기 검색 영역 표시
locale_search(
    # .env 파일을 찾기 위한 프로젝트 루트
    project_root=project_root,
    # API 키 로딩 함수
    load_api_key=load_api_key,
    # 충전소 기본정보 조회 함수
    load_charger_info=load_charger_info,
    # 충전기 실시간 상태 조회 함수
    load_charger_status=load_charger_status,
    # 검색 결과 표 렌더링 함수
    render_available_charger_table=available_charger_table,
    # 검색 결과 지도 렌더링 함수
    render_available_charger_map=available_charger_map,
    # 표에서 선택한 충전소 위치로 지도를 이동할지 여부
    enable_move_map=True,
)
