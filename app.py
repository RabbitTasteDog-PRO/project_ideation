import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable, GeocoderTimedOut
from pathlib import Path
import time
import pydeck as pdk

from src.api import (
    ChargerAPIError,
    get_charger_info,
    get_charger_status,
    load_api_key,
)
from src.constants import AVAILABLE_STATUS_LABEL, REGION_CODES
from src.preprocess import (
    filter_available_chargers,
    get_output_options,
    merge_charger_data,
)


# 사용할 공공데이터 API 주소
# 충전소 상태 : http://apis.data.go.kr/B552584/EvCharger/getChargerStatus
# 충전소 정보 : http://apis.data.go.kr/B552584/EvCharger/getChargerInfo


# 기본정보를 한 시간 동안 저장
@st.cache_data(ttl=3600, show_spinner=False)
def load_charger_info(api_key, zcode):
    # 선택 지역의 기본정보 요청
    return get_charger_info(api_key, zcode)


# 상태정보를 5분 동안 저장
@st.cache_data(ttl=300, show_spinner=False)
def load_charger_status(api_key, zcode):
    # 선택 지역의 상태정보 요청
    return get_charger_status(api_key, zcode)


# 주소를 위도와 경도로 변환
def get_lat_lon(address):
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


# 사용 가능한 충전기 지도를 표시
def render_available_charger_map(available_df, selected_row=None):
    map_columns = {"lat", "lng"}

    if not map_columns.issubset(available_df.columns):
        return

    available_map_df = available_df.dropna(
        subset=["lat", "lng"]
    ).copy()

    if available_map_df.empty:
        return

    if selected_row is None:
        selected_row = available_map_df.iloc[0]

    view_state = pdk.ViewState(
        latitude=float(selected_row["lat"]),
        longitude=float(selected_row["lng"]),
        zoom=15,
        pitch=0,
    )

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=available_map_df,
        get_position="[lng, lat]",
        get_radius=80,
        get_fill_color=[0, 255, 0, 180],
        pickable=True,
    )

    deck = pdk.Deck(
        map_style=None,
        initial_view_state=view_state,
        layers=[layer],
        tooltip={
            "text": "{statNm}\n{addr}\n{output} kW"
        },
    )

    st.pydeck_chart(deck, use_container_width=True)

    st.info(
        f"선택 위치: {selected_row['statNm']} / {selected_row['addr']}"
    )


# 사용 가능한 충전기 상세 표를 표시 : 전부출력
# def render_available_charger_table(available_df):
#     # 상세 표에 보여줄 열 선택
#     detail_columns = [
#         column
#         for column in [
#             "statNm",
#             "addr",
#             "output",
#             "method",
#             "useTime",
#         ]
#         if column in available_df.columns
#     ]
#
#     # API 열 이름을 한글로 변경
#     column_names = {
#         "statNm": "충전소명",
#         "addr": "주소",
#         "output": "충전용량(kW)",
#         "method": "충전방식",
#         "useTime": "이용시간",
#     }
#
#     # 사용 가능한 충전기 표 표시
#     st.dataframe(
#         available_df[detail_columns].rename(columns=column_names),
#         width="stretch",
#         hide_index=True,
#     )

# 페이지 출력
def render_available_charger_table(available_df, key_suffix):
    detail_columns = [
        column
        for column in [
            "statNm",
            "addr",
            "output",
            "method",
            "useTime",
        ]
        if column in available_df.columns
    ]

    column_names = {
        "statNm": "충전소명",
        "addr": "주소",
        "output": "충전용량(kW)",
        "method": "충전방식",
        "useTime": "이용시간",
    }

    page_size = 100
    total_count = len(available_df)
    total_pages = max((total_count - 1) // page_size + 1, 1)

    page_key = f"available_charger_page_{key_suffix}"

    if page_key not in st.session_state:
        st.session_state[page_key] = 1

    current_page = st.session_state[page_key]

    start_index = (current_page - 1) * page_size
    end_index = start_index + page_size

    page_df = available_df.iloc[start_index:end_index].copy()

    st.caption(
        f"전체 {total_count:,}건 중 "
        f"{start_index + 1:,} ~ {min(end_index, total_count):,}건 표시"
    )

    selected_event = st.dataframe(
        page_df[detail_columns].rename(columns=column_names),
        width="stretch",
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=f"available_charger_table_{key_suffix}",
    )

    selected_row = None

    selected_rows = selected_event.selection.rows

    if selected_rows:
        selected_index = selected_rows[0]
        selected_row = page_df.iloc[selected_index]

    st.markdown("#### 페이지")

    start_page = max(1, current_page - 2)
    end_page = min(total_pages, current_page + 2)

    outer_left, center, outer_right = st.columns([3, 4, 3])

    with center:
        button_count = (end_page - start_page + 1) + 4
        cols = st.columns(button_count)

        with cols[0]:
            if st.button(
                "⏮",
                key=f"{page_key}_first",
                disabled=current_page == 1,
            ):
                st.session_state[page_key] = 1
                st.rerun()

        with cols[1]:
            if st.button(
                "◀",
                key=f"{page_key}_prev",
                disabled=current_page == 1,
            ):
                st.session_state[page_key] = current_page - 1
                st.rerun()

        column_index = 2

        for page_number in range(start_page, end_page + 1):
            with cols[column_index]:
                button_type = (
                    "primary"
                    if page_number == current_page
                    else "secondary"
                )

                if st.button(
                    str(page_number),
                    key=f"{page_key}_{page_number}",
                    type=button_type,
                ):
                    st.session_state[page_key] = page_number
                    st.rerun()

            column_index += 1

        with cols[column_index]:
            if st.button(
                "▶",
                key=f"{page_key}_next",
                disabled=current_page == total_pages,
            ):
                st.session_state[page_key] = current_page + 1
                st.rerun()

        column_index += 1

        with cols[column_index]:
            if st.button(
                "⏭",
                key=f"{page_key}_last",
                disabled=current_page == total_pages,
            ):
                st.session_state[page_key] = total_pages
                st.rerun()

    return selected_row


# 현재 사용 가능한 충전기 검색 영역 표시
def render_available_charger_search(enable_move_map=False):
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
        )

    # 사용 가능한 충전기 상세 표 표시
    # render_available_charger_table(available_df)
    # 페이지 출력
    # render_available_charger_table(available_df, key_suffix)


# 앱의 가장 큰 제목 표시
st.title("전기차 충전소 사용량 지도")

# app.py가 있는 프로젝트 루트를 기준으로 경로 설정
project_root = Path(__file__).resolve().parent
data_dir = project_root / "Data"
# 사용량 CSV 파일 경로
csv_path = data_dir / "test_data.csv"
# 저장된 좌표 CSV 파일 경로
coords_path = data_dir / "coords.csv"

# 충전소 사용량 CSV 읽기
if not csv_path.exists():
    st.error(f"사용량 데이터 파일을 찾을 수 없습니다: {csv_path}")
    st.stop()

df = pd.read_csv(csv_path, encoding="cp949")
# 열 이름 양쪽 공백 제거
df.columns = df.columns.str.strip()

# 사용량 열 이름을 변수로 저장
usage_column = "사용량(키로와트시)"
# 사용량 문자를 숫자로 변환
df[usage_column] = pd.to_numeric(
    # 쉼표를 제거한 문자열 사용
    df[usage_column].astype(str).str.replace(",", "", regex=False),
    # 변환 실패 값은 결측치 처리
    errors="coerce"
    # 결측 사용량을 0으로 변경
).fillna(0)

# 지도 검색용 주소 만들기
df["address"] = df["광역지자체"] + " " + df["시군구"] + " 대한민국"

# 원본 데이터의 앞부분 표시
st.dataframe(df.head())

# 주소를 좌표로 바꿀 도구 생성
geolocator = Nominatim(
    # 서비스 식별용 앱 이름
    user_agent="ev_charger_dashboard",
    # 좌표 검색 제한시간 설정
    timeout=10
)

# 저장한 좌표 파일이 있는지 확인
if coords_path.exists():
    # 기존 좌표 파일을 재사용
    coord_df = pd.read_csv(coords_path)
    # 좌표 불러오기 완료 안내
    st.success("저장된 좌표 파일을 불러왔습니다.")
else:
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
        lat, lon = get_lat_lon(address)

        # 주소와 좌표를 목록에 추가
        coord_list.append({
            "address": address,
            "lat": lat,
            "lon": lon
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

# 기존 방식의 현재 사용 가능한 충전기 검색 영역 표시
# render_available_charger_search(enable_move_map=False)

# 위치 이동이 가능한 현재 사용 가능한 충전기 검색 영역 표시
render_available_charger_search(enable_move_map=True)
