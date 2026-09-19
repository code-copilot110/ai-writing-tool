from __future__ import annotations

BASE_RULES = """\
共通ルール:
- 前置き・挨拶・「以下が〜です」のような説明は書かず、成果物だけを出力する。
- 入力に無い事実・数値・固有名詞を捏造しない。不明で必須の情報は [要確認: ○○] と明記する。
- 指定された形式（Markdown など）と文体を守る。日本語で書く（翻訳ツールを除く）。"""


def system_prompt(role: str) -> str:
    return f"{role}\n\n{BASE_RULES}"
