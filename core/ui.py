from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from google.genai import errors as genai_errors

from core import gemini

load_dotenv()

HISTORY_LIMIT = 10


@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str
    temperature: float


def render_sidebar() -> None:
    with st.sidebar:
        st.header("設定")
        env_key = os.getenv("GEMINI_API_KEY", "").strip()
        if env_key:
            api_key = env_key
            st.caption(".env の GEMINI_API_KEY を使用中")
        else:
            api_key = st.text_input(
                "Gemini APIキー",
                type="password",
                key="api_key_input",
                help="この画面を閉じると消えます。恒久的に使う場合は .env に GEMINI_API_KEY を設定してください。",
            ).strip()
        model = st.selectbox("モデル", gemini.MODELS, key="model")
        temperature = st.slider(
            "創造性 (temperature)",
            0.0,
            2.0,
            0.7,
            0.1,
            key="temperature",
            help="低いほど安定・正確、高いほど多様で自由な表現になります。",
        )
    st.session_state["_settings"] = Settings(api_key, model, temperature)


def generate(tool_key: str, prompt: str, system: str) -> None:
    settings: Settings = st.session_state["_settings"]
    if not settings.api_key:
        st.error(
            "Gemini APIキーが未設定です。サイドバーで入力するか、.env に GEMINI_API_KEY を設定してください。"
        )
        return

    placeholder = st.empty()
    text = ""
    try:
        for chunk in gemini.stream_generate(
            prompt,
            system=system,
            api_key=settings.api_key,
            model=settings.model,
            temperature=settings.temperature,
        ):
            text += chunk
            placeholder.markdown(text + "▌")
    except genai_errors.APIError as e:
        placeholder.empty()
        st.error(f"Gemini API エラー ({e.code}): {e.message}")
        return
    except Exception as e:
        placeholder.empty()
        st.error(f"生成に失敗しました: {e}")
        return

    placeholder.empty()
    if not text.strip():
        st.warning(
            "結果が空でした。安全フィルタ等でブロックされた可能性があります。入力を変えて再度お試しください。"
        )
        return

    history = st.session_state.setdefault("history", {}).setdefault(tool_key, [])
    history.insert(0, {"time": datetime.now().strftime("%H:%M:%S"), "text": text})
    del history[HISTORY_LIMIT:]


def show_result(tool_key: str, filename: str) -> None:
    history = st.session_state.get("history", {}).get(tool_key)
    if not history:
        return

    latest = history[0]
    st.subheader("結果")
    preview_tab, copy_tab = st.tabs(["プレビュー", "コピー用テキスト"])
    with preview_tab:
        st.markdown(latest["text"])
    with copy_tab:
        st.code(latest["text"], language="markdown", wrap_lines=True)
    st.download_button(
        "Markdownで保存",
        latest["text"],
        file_name=f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown",
    )

    if len(history) > 1:
        with st.expander(f"このセッションの過去の結果 ({len(history) - 1}件)"):
            for item in history[1:]:
                st.caption(item["time"])
                st.code(item["text"], language="markdown", wrap_lines=True)


def require(value: str, label: str) -> bool:
    if value.strip():
        return True
    st.warning(f"{label}を入力してください。")
    return False
