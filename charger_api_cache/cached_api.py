from __future__ import annotations

import streamlit as st

from src.api import get_charger_info, get_charger_status


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

