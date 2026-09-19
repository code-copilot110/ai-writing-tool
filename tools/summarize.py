from __future__ import annotations

import streamlit as st

from core import prompts, ui

TOOL_KEY = "summarize"
FORMATS = {
    "箇条書き": "要点を箇条書き（「- 」で始まる行）でまとめる",
    "一文で": "全体を1文（100字以内）で言い表す",
    "段落": "自然な文章の段落としてまとめる",
    "結論＋詳細": "冒頭に「結論（TL;DR）」を1〜2文で示し、その後に要点を箇条書きで補足する",
}
LENGTHS = {"短め": "原文の約10%", "標準": "原文の約20%", "詳しめ": "原文の約35%"}

SYSTEM = prompts.system_prompt(
    "あなたは文章要約の専門家です。原文の意味を歪めず、重要な情報を落とさずに要約します。"
)


def build_prompt(text: str, fmt: str, length: str, action_items: bool) -> str:
    task = (
        f"次の文章を要約してください。\n"
        f"- 形式: {FORMATS[fmt]}\n"
        f"- 長さ: {LENGTHS[length]}"
        "（「一文で」の場合は上記の一文の指定を優先）\n"
        "- 原文に書かれていないことは付け加えない"
    )
    if action_items:
        task += "\n- 最後に「## やるべきこと（アクションアイテム）」として、原文から読み取れる TODO を箇条書きで示す（無ければ「なし」）"
    return f"{task}\n\n--- 原文 ---\n{text.strip()}"


def render() -> None:
    st.title("要約")
    st.caption("長い文章を、読みやすい形に短くまとめます。")

    text = st.text_area("要約したい文章", height=280)
    st.caption(f"{len(text)} 文字")
    col1, col2 = st.columns(2)
    fmt = col1.selectbox("形式", list(FORMATS))
    length = col2.selectbox("長さ", list(LENGTHS), index=1)
    action_items = st.checkbox("アクションアイテム（やるべきこと）も抽出する")

    if st.button("要約する", type="primary", key="summarize_run"):
        if ui.require(text, "要約したい文章"):
            ui.generate(TOOL_KEY, build_prompt(text, fmt, length, action_items), SYSTEM)
    ui.show_result(TOOL_KEY, "summary")
