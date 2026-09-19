from __future__ import annotations

import streamlit as st

from core import prompts, ui

TOOL_KEY = "email"
MODE_REPLY = "返信する"
MODE_NEW = "新規作成"
RELATIONS = ["取引先・目上の人", "社内（上司）", "社内（同僚・部下）", "友人・知人", "初対面・問い合わせ先"]
TONES = ["丁寧なビジネス", "やや親しみのある丁寧語", "カジュアル"]
LENGTHS = ["短く簡潔に", "標準", "丁寧に詳しく"]

SYSTEM = prompts.system_prompt(
    "あなたは日本語のビジネスメールに精通したアシスタントです。"
    "相手との関係に合った敬語・言い回しで、そのまま送れる自然なメールを書きます。"
)


def build_prompt(
    mode: str,
    received: str,
    points: str,
    relation: str,
    tone: str,
    length: str,
    signature: str,
    variants: int,
) -> str:
    lines = [f"相手との関係: {relation}", f"文体: {tone}", f"長さ: {length}"]
    if mode == MODE_REPLY:
        lines.append(f"受信メール:\n{received.strip()}")
        lines.append(f"返信で伝えたい要点:\n{points.strip()}")
        task = "受信メールへの返信文を作成してください。"
    else:
        lines.append(f"メールの用件・伝えたい内容:\n{points.strip()}")
        task = "新規に送るメールを作成してください。"
    if signature.strip():
        lines.append(f"署名:\n{signature.strip()}")

    if variants == 1:
        fmt = "「件名」と「本文」を出力してください。"
    else:
        fmt = (
            f"トーンや切り口を少し変えた {variants} 案を出力してください。"
            "各案は「## 案N」の見出しの下に「件名」と「本文」を書いてください。"
        )
    if signature.strip():
        fmt += "本文の末尾に署名を付けてください。"
    else:
        fmt += "署名は付けないでください。"
    return "\n\n".join(["\n".join(lines[:3]), *lines[3:]]) + f"\n\n{task}{fmt}"


def render() -> None:
    st.title("メール返信・作成")
    st.caption("受信メールへの返信、または新規メールの文面を作ります。")

    mode = st.radio("モード", [MODE_REPLY, MODE_NEW], horizontal=True)
    received = ""
    if mode == MODE_REPLY:
        received = st.text_area("受信したメール", height=200)
        points = st.text_area(
            "返信で伝えたい要点（箇条書きでOK）",
            height=120,
            placeholder="例:\n・日程は来週火曜の午後で調整可能\n・資料は前日までに送付する",
        )
    else:
        points = st.text_area(
            "用件・伝えたい内容",
            height=160,
            placeholder="例: 先日の打ち合わせのお礼と、見積書送付のご連絡",
        )

    col1, col2, col3, col4 = st.columns(4)
    relation = col1.selectbox("相手との関係", RELATIONS)
    tone = col2.selectbox("文体", TONES)
    length = col3.selectbox("長さ", LENGTHS, index=1)
    variants = col4.slider("案の数", 1, 3, 1)
    signature = st.text_area("署名（任意）", height=80, placeholder="例:\n山田 太郎\nyamada@example.com")

    if st.button("生成する", type="primary", key="email_run"):
        ok = ui.require(points, "要点・用件")
        if mode == MODE_REPLY:
            ok = ui.require(received, "受信メール") and ok
        if ok:
            ui.generate(
                TOOL_KEY,
                build_prompt(mode, received, points, relation, tone, length, signature, variants),
                SYSTEM,
            )
    ui.show_result(TOOL_KEY, "email")
