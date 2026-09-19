# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

個人用の日本語ライティング支援ツール。Streamlit の UI と Gemini API（`google-genai` SDK）で構成。DB・認証なし、利用者は自分のみ。UI の文言とプロンプトはすべて日本語。

## コマンド

```bash
./start.command                              # 起動（.venv が無ければ作成・依存導入。http://localhost:8501 を自動で開く）
.venv/bin/streamlit run app.py --server.headless true   # 手動起動
.venv/bin/pip install -r requirements.txt    # 依存のインストール
```

- 起動は必ず `--server.headless true` 付き（または `start.command` 経由）で行う。付けないと、Streamlit 初回起動時の「Email:」入力待ちでポートが開かず、ブラウザでは `ERR_CONNECTION_REFUSED` に見える（Enter を押すまで進まない）。
- API キーは `.env` の `GEMINI_API_KEY`（`.env.example` 参照）か、サイドバーの入力欄から渡す。
- テストスイート・linter・git リポジトリは無い。変更の確認は `streamlit.testing.v1.AppTest` を使い、`core.gemini.stream_generate` をダミーのジェネレータに差し替えて行う。`ui.py` は `gemini.stream_generate` を呼び出し時に属性参照するため、この差し替えが効く。`AppTest.from_function` は関数のソースだけを取り出すので、変数はクロージャではなく `args=(...)` で渡す。各ツールの `render()` は、先に `ui.render_sidebar()` を呼ぶラッパー経由でテストする。

## アーキテクチャ

`app.py` は再実行のたびに `ui.render_sidebar()` を呼び、続けて `st.navigation([...]).run()` でツールごとの `st.Page` を表示する。`render_sidebar()` は `Settings`（api_key, model, temperature）を `st.session_state["_settings"]` に保存する。各ツールは引数なしでこの設定を参照できる。

各 `tools/<name>.py` は同じ形をしており、新しいツールもこの形に合わせる。
- `SYSTEM = prompts.system_prompt("<役割>")`: 役割と共通ルール `BASE_RULES`（前置き禁止・事実の捏造禁止・不明点は `[要確認: ○○]` と明記）を合成する。
- `build_prompt(...) -> str`: Streamlit を呼ばない純関数。プロンプトの文面を直すときはここを編集する。
- `render()`: 入力ウィジェットを並べ、`ui.require(...)` で入力チェックし、ボタン押下時に `ui.generate(TOOL_KEY, prompt, SYSTEM)` を呼び、最後に必ず `ui.show_result(TOOL_KEY, filename)` を呼ぶ。

生成から表示までの流れは `core/ui.py` が担う。`generate()` はチャンクを `st.empty()` に逐次表示し、完了後に最終テキストを `st.session_state["history"][tool_key]` の先頭へ積む（新しい順、上限 `HISTORY_LIMIT`）。`show_result()` はボタン押下ではなく、この履歴から描画する。これは意図的な設計で、ダウンロードボタンなど何かのウィジェットを操作するとスクリプトが再実行されるため、結果を再実行後も残す必要がある。表示中でないページのウィジェット状態は Streamlit が破棄するが、`history` は残る。

SDK に触れるのは `core/gemini.py` だけ（`stream_generate` がテキストのチャンクを yield する）。選択できるモデルの一覧は、同ファイルの `MODELS` 定数。

## 方針・スコープ

- 個人用のローカルツール。DB・認証・ユーザー管理・外部公開向けの対応（ログイン、レート制限など）は入れない。`localhost` でのみ使う。
- 履歴は `st.session_state` 内のみで、永続化しない。残したい結果は「Markdownで保存」ボタンでダウンロードする運用。永続化が必要になったら、まず相談する。
- 技術スタックは Python / Streamlit / Gemini API。SDK は `google-genai` を使い、旧 `google-generativeai` は使わない。依存を増やすときは先に確認する。

## 作業ルール

- ユーザーへの返答、コード中の UI 文言、コメント、ドキュメントは日本語で書く。返答は短く簡潔にする。
- ファイルの削除、依存ライブラリの追加・更新、`.venv` の作り直しをする前に確認する。
- `.env` と API キーは、コード・ログ・出力・コミットに含めない（`.gitignore` 済み）。
- UI を変更したら、`AppTest` だけで済ませず、実際にサーバーを起動してブラウザで表示を確認する。確認後は起動したサーバーを止める。
- 動作確認用のテストスクリプトは、プロジェクト直下ではなく scratchpad などプロジェクト外に置く（現状、リポジトリにテストは含めない方針）。
- コミットやプッシュは、頼まれたときだけ行う。

## プロンプト変更の指針

- 出力の質を直したいときは、まず該当ツールの `SYSTEM` と `build_prompt` を修正する。UI やモデル設定を触るのは、その後。
- 共通の振る舞い（前置きなし、事実の捏造禁止など）は `core/prompts.py` の `BASE_RULES` に集約している。ツール固有のルールだけを各ツールに書き、共通部分を重複させない。
- 翻訳ツールだけは訳文を日本語以外で出すため、`BASE_RULES` の「日本語で書く」と矛盾しないよう `SYSTEM` で明示している。同様の例外を作るときも `SYSTEM` で明示する。
- 媒体ごとの文字数制限（X は全角140字など）は `tools/sns_title.py` の `MEDIA` に集約している。仕様が変わったらここだけ直す。

## 注意点

- 実行環境はシステムの Python 3.9。全モジュールが `from __future__ import annotations` を使っているので、実行時に評価される `X | Y` 型や `match` は使わない。
- 全ツールのページが `render` という同名の関数なので、`app.py` の各 `st.Page` には重複しない `url_path` を明示する。省略すると Streamlit がページ重複のエラーを出す。
- アイコンは絵文字ではなく Material 形式（`":material/edit_note:"`）で指定する。
- ツールを追加するには、モジュールを作成し、`app.py` の `pages` リストに登録する。
