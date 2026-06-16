"""지역 기반 사용 가능 충전기 조회 페이지."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

import available_charger_view.map as available_map
import available_charger_view.table as available_table
import charger_api_cache.cached_api as cached_api
import locale_search.available_charger_search as available_charger_search
import locale_search.kepco_car_type_search as kepco_car_type_search
from src.api import load_api_key


def render_locale_search_page() -> None:
    """사용 가능한 충전기 조회 화면을 렌더링한다."""
    project_root = Path(__file__).resolve().parents[1]

    st.title("전기차 충전소 조회")

    available_charger_search.render_available_charger_search(
        project_root=project_root,
        load_api_key=load_api_key,
        load_charger_info=cached_api.load_charger_info,
        load_charger_status=cached_api.load_charger_status,
        render_available_charger_table=available_table.render_available_charger_table,
        render_available_charger_map=available_map.render_available_charger_map,
        enable_move_map=True,
    )

    kepco_car_type_search.render_kepco_car_type_search(
        project_root=project_root,
    )
