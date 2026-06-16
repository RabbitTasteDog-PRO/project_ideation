"""Streamlit 앱의 진입점.

이 파일은 화면을 직접 구현하지 않고, 페이지를 등록하고 실행하는 역할만 담당한다.
"""

import streamlit as st

from ui.dashboard_page import render_dashboard_page
from ui.faq_search_page import render_faq_search_page
from ui.locale_search_page import render_locale_search_page


st.set_page_config(
    page_title="전기차 충전소 대시보드",
    layout="wide",
)

dashboard_page = st.Page(
    render_dashboard_page,
    title="대시보드",
    default=True,
)

locale_search_page = st.Page(
    render_locale_search_page,
    title="실시간 사용가능한 충전기 조회",
)

faq_search_page = st.Page(
    render_faq_search_page,
    title="FAQ검색",
)

navigation = st.navigation(
    [dashboard_page, locale_search_page, faq_search_page],
    position="sidebar",
)

navigation.run()
