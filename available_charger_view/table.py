from __future__ import annotations

import streamlit as st


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

