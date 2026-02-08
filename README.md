# SquadBeyond 自動化ツール (RPA)

SquadBeyond のページ複製・配信割合変更・URL置換・ポップアップ設定を自動化するツールです。

---

## 使い方（Windows）

### ステップ1: ダウンロード

1. このリポジトリの [Releases ページ](../../releases/latest) を開く
2. **beyond_RPA.zip** をダウンロード
3. ZIP を展開する

展開すると以下のファイルが入っています：
```
beyond_RPA.exe          ← 本体（ダブルクリックで起動）
accounts.csv.sample     ← アカウント設定のテンプレート
```

### ステップ2: アカウント設定（初回のみ）

1. `accounts.csv.sample` をコピーして **`accounts.csv`** にリネーム
2. `accounts.csv` を Excel で開く
3. **pass 列** に各アカウントの正しいパスワードを入力して保存

> accounts.csv は beyond_RPA.exe と **同じフォルダ** に置いてください。

### ステップ3: 起動

`beyond_RPA.exe` をダブルクリックして起動します。

> 初回起動時に Windows Defender の警告が出る場合があります。
> 「詳細情報」→「実行」をクリックしてください。

### ステップ4: 操作

1. ドロップダウンからアカウントを選択
2. 「CSVファイルを選択」で処理データの CSV を指定
3. 実行ボタンをクリック
   - **実行 (他を0%にする)**: 複製後、他バージョンの配信割合を 0% に設定
   - **実行 (割合変更なし)**: 配信割合を変更せずに実行

---

## CSVファイルの形式

ヘッダーなし、以下の列順：

| 列 | 内容 |
|----|------|
| 1  | 対象ページURL |
| 2  | 複製元バージョン名 |
| 3  | 置換元チェックボックス値 |
| 4  | キー値 |
| 5  | ラベル値（複製先） |
| 6  | （未使用） |
| 7  | 置換先URL |

## 必要環境

- Windows 10 以降
- Google Chrome（最新版推奨）

---

## 開発者向け（ソースから実行する場合）

```bash
git clone <リポジトリURL>
cd beyond
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
cp accounts.csv.sample accounts.csv
# accounts.csv の pass 列にパスワードを入力
python main.py
```
