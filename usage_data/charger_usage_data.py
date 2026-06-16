from __future__ import annotations

import pandas as pd
import streamlit as st


def load_usage_data(csv_path):
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

    return df, usage_column

