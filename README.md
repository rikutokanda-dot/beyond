# SquadBeyond 自動化ツール (RPA)

SquadBeyond のページ複製・配信割合変更・URL置換・ポップアップ設定を自動化する Web アプリです。
Google Cloud Run で動作し、URLにアクセスするだけで誰でも使えます。

---

## 使い方（社内メンバー向け）

1. 共有された URL をブラウザで開く
2. ログインパスワードを入力（管理者から共有されたもの）
3. ドロップダウンからアカウントを選択
3. 「CSVファイルを選択」で処理データの CSV をアップロード
4. 実行ボタンをクリック
   - **実行 (他を0%にする)**: 複製後、他バージョンの配信割合を 0% に設定
   - **実行 (割合変更なし)**: 配信割合を変更せずに実行

---

## デプロイ手順（管理者向け・初回のみ）

### 1. GCP API を有効化

```bash
gcloud services enable run.googleapis.com secretmanager.googleapis.com
```

### 2. アカウント情報を Secret Manager に登録

`accounts.csv` を用意（`accounts.csv.sample` を参考に、正しいパスワードを入力）してから：

```bash
gcloud secrets create accounts-csv --data-file=accounts.csv
```

### 3. Cloud Run にデプロイ

```bash
gcloud run deploy beyond-rpa \
  --source . \
  --region asia-northeast1 \
  --memory 2Gi --cpu 2 \
  --timeout 3600 \
  --max-instances 1 \
  --allow-unauthenticated \
  --set-secrets ACCOUNTS_CSV=accounts-csv:latest \
  --set-env-vars APP_PASSWORD=Rj7kXm3qWn
```

デプロイ完了後に表示される URL を社内メンバーに共有してください。

### パスワードの更新

```bash
gcloud secrets versions add accounts-csv --data-file=accounts.csv
gcloud run services update beyond-rpa --region asia-northeast1
```

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

---

## ローカル開発

```bash
docker build -t beyond-rpa .
docker run -p 8080:8080 -e ACCOUNTS_CSV="$(cat accounts.csv)" -e APP_PASSWORD=Rj7kXm3qWn beyond-rpa
# ブラウザで http://localhost:8080 を開く
```
