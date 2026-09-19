from __future__ import annotations

import streamlit as st

from core import prompts, ui

TOOL_KEY = "sns_title"
MEDIA = {
    "X（旧Twitter）投稿": "全角140字以内。冒頭で目を引き、最後に行動を促す一言や問いかけを入れる",
    "Instagram キャプション": "改行を活用して読みやすくし、冒頭の1行で興味を引く。末尾に関連ハッシュタグを付ける",
    "Facebook・LinkedIn 投稿": "ストーリーや学びを伝える落ち着いた文体。3〜6文程度",
    "ブログ記事タイトル": "全角32字前後。検索されやすいキーワードを前半に入れ、読みたくなる具体性を持たせる",
    "YouTube 動画タイトル": "全角40字以内。興味を引く数字や具体的な効果を入れ、誇大表現は避ける",
    "キャッチコピー": "全角20字以内。短く印象に残るリズムのよい言葉にする",
}
TONES = ["親しみやすい", "丁寧", "カジュアル", "ユーモラス", "信頼感・専門的"]

SYSTEM = prompts.system_prompt(
    "あなたは SNS 運用とコピーライティングに強いコピーライターです。媒体の特性に合わせた、短くて響く文章を書きます。"
)


def build_prompt(source: str, media: str, tone: str, count: int, emoji: bool) -> str:
    task = (
        f"次の内容をもとに、{media}の案を{count}個作ってください。\n"
        f"- 媒体のルール: {MEDIA[media]}\n"
        f"- トーン: {tone}\n"
        f"- 絵文字: {'適度に使う' if emoji else '使わない'}\n"
        "- 各案は切り口（訴求ポイント）を変え、「### 案N」の見出しを付けて出力する"
    )
    return f"{task}\n\n--- 元ネタ・伝えたいこと ---\n{source.strip()}"


def render() -> None:
    st.title("SNS投稿・タイトル案")
    st.caption("SNS投稿文、記事・動画のタイトル、キャッチコピーを複数案まとめて作ります。")

    source = st.text_area(
        "元ネタ・伝えたいこと",
        height=180,
        placeholder="例: 新しく始めた朝活の習慣が、1か月で仕事の集中力アップにつながった話",
    )
    col1, col2, col3 = st.columns(3)
    media = col1.selectbox("媒体", list(MEDIA))
    tone = col2.selectbox("トーン", TONES)
    count = col3.slider("案の数", 3, 10, 5)
    emoji = st.checkbox("絵文字を使う", value=False)

    if st.button("案を作る", type="primary", key="sns_run"):
        if ui.require(source, "元ネタ"):
            ui.generate(TOOL_KEY, build_prompt(source, media, tone, count, emoji), SYSTEM)
    ui.show_result(TOOL_KEY, "sns")
