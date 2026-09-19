from __future__ import annotations

import streamlit as st

from core import prompts, ui

TOOL_KEY = "blog"
TONES = ["親しみやすい", "丁寧・フォーマル", "専門的・信頼感", "カジュアル・口語", "エッセイ調"]
SCOPE_OUTLINE = "構成案のみ"
SCOPE_FULL = "本文まで"

SYSTEM = prompts.system_prompt(
    "あなたはプロのブログライターです。読者の悩みや検索意図に応え、最後まで読みたくなる記事を書きます。"
)


SEO_OUTPUT_FULL = (
    "記事本文のあとに区切り線（---）を置き、「## SEO情報」として次を出力してください。\n"
    "- 想定した検索意図（1〜2文）\n"
    "- メタディスクリプション（全角120字前後。主キーワードを含め、クリックしたくなる内容）\n"
    "- URL スラッグ案（英小文字とハイフン）"
)
SEO_OUTPUT_OUTLINE = (
    "構成案には、次も含めてください。\n"
    "- 想定した検索意図（1〜2文）\n"
    "- 各 H2 見出しで意識するキーワードと要点\n"
    "- 「よくある質問」に入れる Q&A の案（2〜4個）\n"
    "- メタディスクリプション案（全角120字前後）と URL スラッグ案（英小文字とハイフン）"
)


def split_keywords(keywords: str) -> list[str]:
    normalized = keywords.replace("、", ",").replace("，", ",")
    return [k.strip() for k in normalized.split(",") if k.strip()]


def seo_rules(main_keyword: str) -> str:
    return (
        "SEO の要件（検索で上位表示され、かつ読者の役に立つ記事にするため、必ず守ってください）:\n"
        "- まず、このテーマで検索する人の検索意図（知りたいこと・解決したい悩み）を想定し、記事全体でそれに過不足なく答える。\n"
        f"- 主キーワード「{main_keyword}」を、タイトルの前半、導入文の最初の100字以内、"
        "少なくとも1つの H2 見出し、まとめに自然に含める。同じ語の連呼や不自然な詰め込みはしない。\n"
        "- その他のキーワードと、関連語・共起語（一緒に検索されやすい言葉）は、意味が通る範囲で見出しや本文に自然に散らす。\n"
        "- タイトルは全角32字前後。主キーワードを前半に置き、読者のメリットや具体性が伝わるものにする。\n"
        "- 見出しだけを読んでも内容が分かるようにし、各 H2 の冒頭で結論や要点を先に述べる。\n"
        "- 手順・比較・チェックリストなど、箇条書きや表にしたほうが分かりやすい部分は構造化する。\n"
        "- 具体例・数字・手順を入れ、読者がすぐ行動できる内容にする。"
        "ただし統計や出典が必要な事実は捏造せず、[要確認: 出典] と明記する。\n"
        "- 記事の最後に「よくある質問」を2〜4個、Q&A 形式で入れる。"
    )


def build_prompt(
    topic: str,
    keywords: str,
    audience: str,
    tone: str,
    length: int,
    scope: str,
    seo: bool,
    notes: str,
) -> str:
    lines = [f"テーマ: {topic.strip()}"]
    if keywords.strip():
        lines.append(f"キーワード（先頭が主キーワード）: {keywords.strip()}")
    lines.append(f"想定読者: {audience.strip() or '指定なし（一般の読者）'}")
    lines.append(f"文体・トーン: {tone}")
    if notes.strip():
        lines.append(f"盛り込みたい内容・参考情報:\n{notes.strip()}")

    if scope == SCOPE_OUTLINE:
        task = (
            "ブログ記事の構成案を Markdown で作成してください。"
            "タイトル案（3つ）、リード文の方針、H2/H3 の見出し構成と各見出しで書く要点、まとめの方針を含めてください。"
        )
    else:
        task = (
            f"ブログ記事を本文まで書いてください。目安の長さは約{length}字です。"
            "Markdown で、# タイトル、導入文、## 見出し（必要に応じて ###）、まとめの順に構成してください。"
        )
    if seo:
        main = split_keywords(keywords)[:1] or [topic.strip()]
        task += "\n\n" + seo_rules(main[0]) + "\n\n" + (
            SEO_OUTPUT_OUTLINE if scope == SCOPE_OUTLINE else SEO_OUTPUT_FULL
        )
    return "\n".join(lines) + "\n\n" + task


def render() -> None:
    st.title("ブログ記事作成")
    st.caption("テーマとキーワードから、構成案または記事本文を作ります。")

    topic = st.text_input("テーマ・タイトルの案", placeholder="例: 在宅ワークで集中力を保つ方法")
    col1, col2 = st.columns(2)
    keywords = col1.text_input(
        "キーワード（カンマ区切り。先頭が主キーワード）",
        placeholder="例: 在宅ワーク 集中力, 習慣, 環境づくり",
    )
    audience = col2.text_input("想定読者", placeholder="例: 在宅勤務を始めたばかりの会社員")
    col3, col4, col5 = st.columns(3)
    tone = col3.selectbox("トーン", TONES)
    scope = col4.radio("出力範囲", [SCOPE_FULL, SCOPE_OUTLINE], horizontal=True)
    length = col5.slider("目安の文字数", 800, 6000, 2000, 200, disabled=scope == SCOPE_OUTLINE)
    seo = st.checkbox("SEOを意識する（メタディスクリプション付き）", value=True)
    notes = st.text_area("盛り込みたい内容・参考情報（任意）", height=120)

    if st.button("生成する", type="primary", key="blog_run"):
        if ui.require(topic, "テーマ"):
            ui.generate(
                TOOL_KEY,
                build_prompt(topic, keywords, audience, tone, length, scope, seo, notes),
                SYSTEM,
            )
    ui.show_result(TOOL_KEY, "blog")
