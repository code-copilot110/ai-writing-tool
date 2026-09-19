from __future__ import annotations

import streamlit as st

from core import prompts, ui

TOOL_KEY = "translate"
DIRECTIONS = {
    "日本語 → 英語": "日本語から英語へ翻訳する",
    "英語 → 日本語": "英語から日本語へ翻訳する",
    "自動判定": "原文が日本語なら英語へ、日本語以外なら日本語へ翻訳する",
}
TONES = ["自然な文章", "フォーマル・ビジネス", "カジュアル", "技術文書"]

SYSTEM = prompts.system_prompt(
    "あなたはプロの翻訳者です。直訳ではなく、訳文の言語として自然で、原文の意図とニュアンスを保った翻訳をします。"
    "（翻訳ツールでは、訳文は翻訳先の言語で書く。）"
)


def build_prompt(text: str, direction: str, tone: str, notes: bool) -> str:
    task = f"次の文章を翻訳してください。\n- 翻訳の向き: {DIRECTIONS[direction]}\n- 文体: {tone}"
    if notes:
        task += "\n- 訳文のあとに「## 補足」として、訳し方に迷った点やニュアンスの注意点を日本語で簡潔に添える"
    else:
        task += "\n- 訳文だけを出力する"
    return f"{task}\n\n--- 原文 ---\n{text.strip()}"


def render() -> None:
    st.title("翻訳")
    st.caption("日本語と英語を、自然な文体で翻訳します。")

    text = st.text_area("翻訳したい文章", height=240)
    col1, col2 = st.columns(2)
    direction = col1.radio("翻訳の向き", list(DIRECTIONS), index=2, horizontal=True)
    tone = col2.selectbox("文体", TONES)
    notes = st.checkbox("ニュアンスの補足を付ける")

    if st.button("翻訳する", type="primary", key="translate_run"):
        if ui.require(text, "翻訳したい文章"):
            ui.generate(TOOL_KEY, build_prompt(text, direction, tone, notes), SYSTEM)
    ui.show_result(TOOL_KEY, "translation")
