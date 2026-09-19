# 【図解で理解】app.py は「玄関」だった — AIライティングツールの入口を読み解く

AIライティングツールの `app.py` は、たった十数行しかありません。それでも6つのツールが切り替わり、サイドバーの設定が全ページで共有されます。この記事では、その仕組みを Streamlit が初めての人にも分かるように解説します。

## 1. app.py はどんな役割？

一言でいうと **「アプリの玄関」** です。`app.py` 自身は文章生成をしません。次の3つだけを担当します。

1. 画面全体の設定（タイトルや幅）
2. サイドバー（API キー・モデル・温度）の表示
3. 6つのツールのページを登録して、切り替えられるようにする

実際の文章生成は、それぞれ `tools/` フォルダのファイルが行います。

```
app.py（玄関・案内係）
 ├─ core/ui.py       サイドバーや結果表示の共通部品
 └─ tools/
     ├─ blog.py           ブログ記事作成
     ├─ email_reply.py    メール返信・作成
     ├─ summarize.py      要約
     ├─ rewrite.py        校正・リライト
     ├─ translate.py      翻訳
     └─ sns_title.py      SNS投稿・タイトル案
```

## 2. コード全体

```python
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
```

## 3. 先に知っておきたい Streamlit のルール

コードを読む前に、Streamlit の大事な性質をひとつだけ押さえておきましょう。

> **ボタンを押す・文字を入力するなど、画面を操作するたびに、スクリプトが上から下まで最初から実行し直される。**

Excel のように「変更した部分だけ更新」ではなく、毎回 `app.py` を頭から実行し直して画面を作り直します。これを「再実行」と呼びます。この性質を頭に入れておくと、以降の説明がすっきり理解できます。

## 4. 1ブロックずつ読む

### (1) インポート

```python
import streamlit as st

from core import ui
from tools import blog, email_reply, rewrite, sns_title, summarize, translate
```

- `streamlit` は画面を作るライブラリ。慣例で `st` と略します。
- `ui` は共通部品（サイドバー、結果表示など）。
- `blog` などは、6つのツールそれぞれのファイルです。

### (2) ページ全体の設定

```python
st.set_page_config(page_title="AIライティングツール", page_icon=":material/edit_note:", layout="wide")
```

ブラウザのタブに出るタイトルとアイコン、画面の幅を決めています。`layout="wide"` は画面を横いっぱいに使う指定です。

**注意点:** `st.set_page_config` は、Streamlit の命令の中で **最初に** 呼ぶ決まりです。`st.` で始まる命令を先に書くとエラーになります。

### (3) サイドバーを表示する

```python
ui.render_sidebar()
```

左側の「設定」欄（API キー、モデル、創造性）を表示します。中身は `core/ui.py` にあります。

ここでのポイントは、**ページの切り替えより前に呼んでいる**ことです。おかげで、どのツールを開いても同じ設定欄が出ます。入力された設定は `st.session_state["_settings"]` にしまわれ、各ツールはそこから取り出して使います。

### (4) ページの一覧を作る

```python
pages = [
    st.Page(blog.render, title="ブログ記事作成", icon=":material/article:", url_path="blog", default=True),
    ...
]
```

`st.Page(...)` は「このページを画面に追加します」という登録です。引数の意味は次のとおりです。

| 引数 | 意味 |
|---|---|
| `blog.render` | そのページを開いたときに実行する関数（`()` を付けないのがコツ） |
| `title` | サイドバーの案内に出る名前 |
| `icon` | 名前の横のアイコン（`:material/...:` は Google の Material アイコン） |
| `url_path` | ブラウザの URL の末尾（例: `localhost:8501/email`） |
| `default=True` | 最初に開くページ。ブログ記事作成だけに付いている |

`blog.render` の後ろに `()` が付いていない点に注目してください。`blog.render()` と書くと、その場で実行されてしまいます。`blog.render` は「関数そのもの」を渡していて、ページを開いたときに Streamlit が実行してくれます。

### (5) ページを切り替えて実行する

```python
st.navigation(pages).run()
```

この1行で2つのことをしています。

- `st.navigation(pages)` … 登録したページ一覧から、サイドバーに切り替えメニューを作ります。
- `.run()` … 今選ばれているページの関数（`render`）を実行します。

## 5. 全体の流れ

ブログ記事作成で「生成する」を押したときの流れを追ってみます。

```
①「生成する」ボタンを押す
      ↓
② Streamlit が app.py を頭から再実行
      ↓
③ set_page_config        … 画面設定
      ↓
④ ui.render_sidebar()    … サイドバーを描画し、設定を session_state に保存
      ↓
⑤ pages を作る           … ページ一覧を用意
      ↓
⑥ st.navigation(...).run() … 選択中のページ（blog.render）を実行
      ↓
⑦ blog.render の中で入力欄を描画し、ボタンが押されていれば Gemini に生成を依頼
```

つまり `app.py` は毎回、「設定を表示して → 今のページを呼び出す」だけを行う司令塔です。

## 6. つまずきやすいポイント

### なぜ `url_path` が必要なの？

6つのツールの関数は、どれも `render` という同じ名前です。`url_path` を省略すると、Streamlit は関数名から URL を作るため、名前が重複してエラーになります。そこで `"blog"`、`"email"` のように、ページごとに別の名前を明示しています。

### 別のページに移ると、入力した文字が消える

Streamlit は、表示されていないページの入力欄の状態を捨てます。そのため、別のツールに移って戻ると入力欄は空になります。ただし、生成した結果は `st.session_state["history"]` に別途保存しているので、戻ってきても表示されます。

### `if __name__ == "__main__":` が無いのはなぜ？

普通の Python スクリプトと違い、Streamlit はファイルを直接、上から実行するためです。書く必要がありません。

## 7. 新しいツールを追加するには

たとえば「議事録作成」ツールを追加する場合、`app.py` の変更は2か所だけです。

```python
# ① 先頭で読み込む
from tools import blog, email_reply, minutes, rewrite, sns_title, summarize, translate

# ② pages に1行足す
st.Page(minutes.render, title="議事録作成", icon=":material/notes:", url_path="minutes"),
```

あとは `tools/minutes.py` に、他のツールと同じ形（`SYSTEM`・`build_prompt`・`render`）で中身を書けば完成です。`app.py` が薄いおかげで、機能を足すのが簡単な作りになっています。

## 8. まとめ

- `app.py` は文章生成をしない「玄関」で、設定の表示とページ切り替えだけを担当する。
- Streamlit は操作のたびに `app.py` を頭から再実行する。
- `st.set_page_config` は最初、`ui.render_sidebar()` はページ切り替えの前に呼ぶ。
- `st.Page` で各ツールを登録し、`st.navigation(pages).run()` で今のページを実行する。
- 同じ名前の関数を使うため、ページごとに `url_path` を分ける。

次は、実際に文章を作る `tools/blog.py` を読むと、`render` の中で何が起きているのかが分かります。
