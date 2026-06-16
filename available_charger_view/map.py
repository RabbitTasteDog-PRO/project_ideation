from __future__ import annotations

import pydeck as pdk
import streamlit as st


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

