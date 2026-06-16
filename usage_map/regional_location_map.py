from __future__ import annotations

import time

import pandas as pd
import streamlit as st
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable


# 주소를 위도와 경도로 변환
def get_lat_lon(address, geolocator):
    # 좌표 검색 오류를 안전하게 처리
    try:
        # 입력 주소의 위치를 검색
        location = geolocator.geocode(address)

        # 위치를 찾았으면 좌표 반환
        if location:
            return location.latitude, location.longitude

    # 연결 실패와 시간초과 처리
    except (GeocoderUnavailable, GeocoderTimedOut):
        st.warning(f"좌표 조회 실패: {address}")

    # 찾지 못하면 빈 좌표 반환
    return None, None


def load_or_create_coords(df, data_dir, coords_path, geolocator):
    # 저장한 좌표 파일이 있는지 확인
    if coords_path.exists():
        # 기존 좌표 파일을 재사용
        coord_df = pd.read_csv(coords_path)
        # 좌표 불러오기 완료 안내
        st.success("저장된 좌표 파일을 불러왔습니다.")
        return coord_df

    # 최초 좌표 검색 안내
    st.info("좌표 파일이 없어 처음 1회 좌표를 조회합니다.")
    # 좌표 파일을 저장할 데이터 디렉터리 생성
    data_dir.mkdir(parents=True, exist_ok=True)

    # 중복 주소를 제거해 목록 생성
    unique_addresses = df["address"].drop_duplicates().tolist()

    # 좌표 결과를 담을 빈 목록
    coord_list = []
    # 좌표 검색 진행률 표시
    progress = st.progress(0)

    # 각 주소를 순서대로 좌표 변환
    for i, address in enumerate(unique_addresses):
        # 현재 주소의 좌표 조회
        lat, lon = get_lat_lon(address, geolocator)

        # 주소와 좌표를 목록에 추가
        coord_list.append({
            "address": address,
            "lat": lat,
            "lon": lon,
        })

        # 처리된 주소 비율 갱신
        progress.progress((i + 1) / len(unique_addresses))
        # 검색 서버 보호를 위해 대기
        time.sleep(1)

    # 좌표 목록을 표로 변환
    coord_df = pd.DataFrame(coord_list)
    # 다음 실행을 위해 좌표 저장
    coord_df.to_csv(coords_path, index=False, encoding="utf-8-sig")

    # 좌표 저장 완료 안내
    st.success("좌표 파일 저장 완료")
    return coord_df


def render_region_location_map(df, data_dir, coords_path, geolocator):
    coord_df = load_or_create_coords(df, data_dir, coords_path, geolocator)

    # 사용량 데이터에 좌표 결합
    merged_df = df.merge(coord_df, on="address", how="left")

    # 좌표가 있는 데이터만 선택
    map_df = merged_df.dropna(subset=["lat", "lon"])

    # 지도 영역 제목 표시
    st.subheader("지역별 위치 지도")

    # 지도 데이터가 비었는지 확인
    if map_df.empty:
        # 표시할 좌표가 없음을 안내
        st.error("지도에 표시할 좌표가 없습니다.")
    else:
        # 충전소 좌표를 지도에 표시
        st.map(map_df, latitude="lat", longitude="lon")
        # 지도에 사용한 좌표를 표로 표시
        st.dataframe(map_df[["광역지자체", "시군구", "lat", "lon"]])

    return map_df

