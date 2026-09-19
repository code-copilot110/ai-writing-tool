import streamlit as st

from core import ui
from tools import blog, email_reply, rewrite, sns_title, summarize, translate

st.set_page_config(page_title="AIライティングツール", page_icon=":material/edit_note:", layout="wide")

ui.render_sidebar()

pages = [
    st.Page(blog.render, title="ブログ記事作成", icon=":material/article:", url_path="blog", default=True),
    st.Page(email_reply.render, title="メール返信・作成", icon=":material/mail:", url_path="email"),
    st.Page(summarize.render, title="要約", icon=":material/summarize:", url_path="summarize"),
    st.Page(rewrite.render, title="校正・リライト", icon=":material/spellcheck:", url_path="rewrite"),
    st.Page(translate.render, title="翻訳", icon=":material/translate:", url_path="translate"),
    st.Page(sns_title.render, title="SNS投稿・タイトル案", icon=":material/tag:", url_path="sns"),
]
st.navigation(pages).run()
