## Yahoo!ニュースから検索したいワードについて情報を収集するためのプログラム

### 使い方
- mkdir json
- python -m venv venv
- source ./venv/bin/activate
- pip install --upgrade pip setuptools
- pip install -r requirements.txt
- python main.py SEARCH_WORD \[CLICK_TIMES\]

### 引数要素
- SEARCH_WORD: 検索対象のワード
- CLICK_TIMES: 記事一覧にて表示数を増やすボタンを何回押すか．多いほど大量の記事情報を集めることが可能．
