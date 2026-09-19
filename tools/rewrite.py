from __future__ import annotations

import streamlit as st

from core import prompts, ui

TOOL_KEY = "rewrite"
MODE_TONE = "トーンを変える"
MODES = {
    "誤字脱字・文法の校正": "誤字脱字・文法・表記ゆれ・不自然な言い回しだけを直す。文体や内容は変えない",
    "読みやすく整える": "意味は変えずに、文の長さ・構成・接続を整えて読みやすくする",
    "簡潔にする": "意味を保ったまま、冗長な表現を削って簡潔にする",
    "敬語を正す": "敬語の誤用（二重敬語・尊敬語と謙譲語の取り違えなど）を直し、自然な敬語にする",
    MODE_TONE: "指定したトーンに文体を書き換える",
}
TONES = ["丁寧・フォーマル", "親しみやすい", "カジュアル", "専門的・論理的", "力強く説得力のある"]

SYSTEM = prompts.system_prompt(
    "あなたは経験豊富な日本語の編集者・校正者です。元の意図を尊重しつつ文章を改善します。"
)


def build_prompt(text: str, mode: str, tone: str, explain: bool) -> str:
    task = f"次の文章を修正してください。\n- 方針: {MODES[mode]}"
    if mode == MODE_TONE:
        task += f"\n- 目標のトーン: {tone}"
    if explain:
        task += (
            "\n- 出力は「## 修正後」の見出しの下に修正後の全文、"
            "続けて「## 主な変更点」の見出しの下に変更点の箇条書き（なぜ直したか）を書く"
        )
    else:
        task += "\n- 修正後の全文だけを出力する"
    return f"{task}\n\n--- 元の文章 ---\n{text.strip()}"


def render() -> None:
    st.title("校正・リライト")
    st.caption("誤字脱字の校正や、読みやすさ・トーンの調整をします。")

    text = st.text_area("文章", height=260)
    col1, col2 = st.columns(2)
    mode = col1.selectbox("修正の種類", list(MODES))
    tone = col2.selectbox("トーン", TONES, disabled=mode != MODE_TONE)
    explain = st.checkbox("変更点の説明を付ける", value=True)

    if st.button("修正する", type="primary", key="rewrite_run"):
        if ui.require(text, "文章"):
            ui.generate(TOOL_KEY, build_prompt(text, mode, tone, explain), SYSTEM)
    ui.show_result(TOOL_KEY, "rewrite")
