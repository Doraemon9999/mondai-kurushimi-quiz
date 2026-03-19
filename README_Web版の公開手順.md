# 問題と苦しみの理解度テスト - Web版の公開手順

URLを知っている方だけがアクセスできる形で、Web版を公開するときの手順です。  
ひとつずつ進めていけば大丈夫です。

**この先の流れ**  
ステップ1でお手元で動かしたあと、URLで共有したくなったら、ステップ2〜4のとおりに進めてください。GitHub にリポジトリを作り、Streamlit Cloud でデプロイすると、専用のURLが発行されます。そのURLを、共有したい人だけに渡せば、「URLを知っている人だけがアクセスできる」状態になります。無理せず、必要なところから試してみてください。

---

## ステップ1: まずはお手元で動かしてみる

1. ターミナル（PowerShellなど）で、この `web_app` フォルダに移動してください。
   ```
   cd "c:\Users\hurri\OneDrive\デスクトップ\問題と苦しみ関連\web_app"
   ```
   ※ `デスクトップ` の直後に `\` を入れるのを忘れずに。

2. 必要なパッケージを入れます。
   ```
   pip install -r requirements.txt
   ```

3. **problem_answers_vol3.xlsx** を、この `web_app` フォルダに置いてください。  
   元のExcelは「問題と苦しみ関連」フォルダにあります。

4. アプリを起動してみてください。
   ```
   streamlit run app.py
   ```
   ブラウザが開いたら、「テスト」タブで問題が進むか、「お問い合わせ」タブでフォームが表示されるか確認してみてください。ここまでできていればOKです。

---

## ステップ2: GitHub にリポジトリを作る（URLで共有したいとき）

1. [GitHub](https://github.com) にログインして、**New repository** から新しいリポジトリを作成します。  
   名前は例えば `mondai-kurushimi-quiz` で大丈夫です。Public で問題ありません。  
   （URLを検索やSNSに出さなければ、知っている人だけがアクセスできる形になります。）

2. 次のファイルを、そのリポジトリに含めます。
   - `app.py`
   - `requirements.txt`
   - `problem_answers_vol3.xlsx`（`web_app` フォルダに置いたもの）

   コマンドの例は以下です（リポジトリのURLはご自身のものに置き換えてください）。
   ```powershell
   cd "c:\Users\hurri\OneDrive\デスクトップ\問題と苦しみ関連\web_app"
   git init
  git add app.py requirements.txt problem_answers_vol3.xlsx .gitignore .streamlit/config.toml
   git commit -m "Initial: Web版クイズ"
   git branch -M main
   git remote add origin https://github.com/あなたのユーザー名/mondai-kurushimi-quiz.git
   git push -u origin main
   ```
   ※ Git をまだ使ったことがない場合は、先に `git config --global user.name` と `user.email` を設定しておくとスムーズです。

---

## ステップ3: Streamlit Cloud でURLを発行する

1. [Streamlit Community Cloud](https://share.streamlit.io/) を開き、**Sign up with GitHub** でGitHubと連携してログインします。

2. **New app** をクリックします。

3. 次のように設定します。
   - **Repository**: ステップ2で作ったリポジトリ（例: `あなたのユーザー名/mondai-kurushimi-quiz`）
   - **Branch**: `main`
   - **Main file path**: `app.py`

4. **Deploy** をクリックして、完了するまで少し待ちます。

5. 数分ほどで **Your app is live!** と表示され、専用のURLが発行されます。  
   例: `https://mondai-kurushimi-quiz-xxxxx.streamlit.app`  
   このURLを開くと、同じテスト・お問い合わせがブラウザで使えます。

---

## ステップ4: URLを「知っている人だけ」に共有する

- 発行されたURLは、**検索エンジンに登録したり、SNSで広く公開したりしなければ**、基本的には知っている人だけがアクセスできます。
- メールやLINEなどで、**利用してほしい方だけ** にURLを送ってください。  
  これで「実際にURLを知っている人だけがアクセスできる」形になります。

---

## ちょっとした注意

- **problem_answers_vol3.xlsx** は、`web_app` フォルダに置いたうえで、Git に含めておくと安心です。含めていないと、デプロイ先では問題が表示されない場合があります。
- お問い合わせは、いまは「メールソフトで送信」するリンクが表示される形です。自動で送信したい場合は、Formspree などのサービスと連携する必要があります。
