import flet as ft
import time
import os
import sys
import io
import math
import tempfile
import pandas as pd
import concurrent.futures
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

# ==========================================
# ▼ 設定エリア ▼
# ==========================================

LOGIN_URL = 'https://app.squadbeyond.com/'
BASE_URL = 'https://app.squadbeyond.com/'

# 並列数
MAX_WORKERS = 3

# ChromeDriverパス（Docker内では /usr/bin/chromedriver）
CHROMEDRIVER_PATH = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")

# ヘッドレスChromeの共通オプション
def get_chrome_options():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    return options

# アカウント情報を環境変数 or accounts.csv から読み込み
def load_accounts():
    # 環境変数から読み込み（Cloud Run / Secret Manager）
    csv_data = os.environ.get("ACCOUNTS_CSV")
    if csv_data:
        df = pd.read_csv(io.StringIO(csv_data))
        accounts = {}
        for i, row in df.iterrows():
            key = str(i + 1)
            accounts[key] = {
                "name": str(row["name"]),
                "id": str(row["id"]),
                "pass": str(row["pass"]),
            }
        return accounts

    # フォールバック: ローカルファイル（開発用）
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    csv_path = os.path.join(base_dir, 'accounts.csv')

    if not os.path.exists(csv_path):
        print(f"エラー: accounts.csv が見つかりません: {csv_path}")
        return {}

    df = pd.read_csv(csv_path)
    accounts = {}
    for i, row in df.iterrows():
        key = str(i + 1)
        accounts[key] = {
            "name": str(row["name"]),
            "id": str(row["id"]),
            "pass": str(row["pass"]),
        }
    return accounts

ACCOUNTS = load_accounts()

# ==========================================
# ▼ ロジック関数群 ▼
# ==========================================

def get_session_cookies(account_info, log_func):
    log_func(">>> [準備] ログインセッションを取得します...")

    options = get_chrome_options()
    driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)
    wait = WebDriverWait(driver, 20)
    cookies = []

    try:
        driver.get(LOGIN_URL)
        time.sleep(2)

        email_xpath = "//input[@id=':r1:'] | //input[@name='email']"
        email_input = wait.until(EC.element_to_be_clickable((By.XPATH, email_xpath)))
        email_input.clear()
        email_input.send_keys(account_info['id'])

        pass_xpath = "//input[@id=':r2:'] | //input[@type='password']"
        pass_input = wait.until(EC.element_to_be_clickable((By.XPATH, pass_xpath)))
        pass_input.clear()
        pass_input.send_keys(account_info['pass'])

        btn1_xpath = "//button[@data-trackid='sign-in-form-login-button']"
        wait.until(EC.element_to_be_clickable((By.XPATH, btn1_xpath))).click()
        time.sleep(3)

        btn2_xpath = "//button[text()='ログイン' and contains(@class, 'MuiButton-sizeSmall')]"
        wait.until(EC.element_to_be_clickable((By.XPATH, btn2_xpath))).click()

        log_func(">>> [準備] ログイン処理完了。待機中...")
        time.sleep(5)

        cookies = driver.get_cookies()
        log_func(">>> [準備] セッション情報の取得に成功しました。")

    except Exception as e:
        log_func(f">>> [エラー] ログインに失敗しました: {e}")
    finally:
        driver.quit()

    return cookies

def run_automation_worker(worker_id, df_subset, cookies, log_func, reset_rates):
    log_func(f"[Worker-{worker_id}] ブラウザを起動します...")

    options = get_chrome_options()

    driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)
    wait = WebDriverWait(driver, 20)

    try:
        driver.get(BASE_URL)

        if not cookies:
            log_func(f"[Worker-{worker_id}] ★ エラー: Cookieがありません。")
            driver.quit()
            return

        for cookie in cookies:
            if 'expiry' in cookie:
                cookie['expiry'] = int(cookie['expiry'])
            driver.add_cookie(cookie)

        driver.refresh()
        time.sleep(3)

        log_func(f"[Worker-{worker_id}] セッション適用完了。処理を開始します。")

        for index, row in df_subset.iterrows():
            col1_url = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
            col2_ver = str(row.iloc[1]) if pd.notna(row.iloc[1]) else ""
            col3_chk = str(row.iloc[2]) if pd.notna(row.iloc[2]) else ""
            col4_key = str(row.iloc[3]) if pd.notna(row.iloc[3]) else ""
            col5_lbl = str(row.iloc[4]) if pd.notna(row.iloc[4]) else ""
            col7_url = str(row.iloc[6]) if pd.notna(row.iloc[6]) else ""

            if not col1_url or col1_url == 'nan' or col1_url == "":
                continue

            prefix = f"[Worker-{worker_id}] [{index+1}件目]"
            log_func(f"{prefix} 開始: {col1_url}")

            driver.get(col1_url)
            time.sleep(2)

            try:
                xpath_ver = f"//span[@data-test='ArticleList-Memo' and contains(text(), '{col2_ver}')]"
                wait.until(EC.element_to_be_clickable((By.XPATH, xpath_ver))).click()
            except Exception:
                log_func(f"{prefix} ★ Skip: 複製元Versionなし")
                continue

            try:
                menu_xpath = '//*[@id="root"]/div[2]/div/div[4]/div[2]/div/div[2]/div/div[2]/div/div[2]/button'
                wait.until(EC.element_to_be_clickable((By.XPATH, menu_xpath))).click()
                time.sleep(0.5)

                clone_menu_xpath = "//span[contains(text(), '別のbeyondページに複製')]"
                wait.until(EC.element_to_be_clickable((By.XPATH, clone_menu_xpath))).click()
            except:
                driver.execute_script("""
                var spans = document.querySelectorAll('span');
                for (var i = 0; i < spans.length; i++) {
                    if (spans[i].textContent.includes('別のbeyondページに複製')) {
                        spans[i].click();
                        break;
                    }
                }
                """)
            time.sleep(1)

            try:
                select_xpath = "//select[@data-test='DuplicateToOtherModal-DestinationAbTestUidSelect']"
                select_elem = wait.until(EC.presence_of_element_located((By.XPATH, select_xpath)))
                Select(select_elem).select_by_visible_text(col5_lbl)

                btn_xpath = "//div[contains(text(), '複製する')]"
                wait.until(EC.element_to_be_clickable((By.XPATH, btn_xpath))).click()
            except Exception as e:
                log_func(f"{prefix} ★ Error(複製): {e}")

            time.sleep(3)

            try:
                rate_xpath = f"//input[@value='{col4_key}']/following::div[@data-test='ArticleList-DeriveryUpRateForm'][1]"
                wait.until(EC.element_to_be_clickable((By.XPATH, rate_xpath))).click()
            except Exception as e:
                log_func(f"{prefix} ★ Error(割合): {e}")

            if reset_rates:
                js_rate_0 = """
                var others = document.querySelectorAll("div[data-test='ArticleList-Article'] input[data-test='ArticleList-DeriveryRateForm']");
                var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                others.forEach(function(i){
                    setter.call(i, "0");
                    i.dispatchEvent(new Event('input', { bubbles: true }));
                });
                """
                driver.execute_script(js_rate_0)
            else:
                log_func(f"{prefix} 配信割合0%化をスキップしました")

            try:
                link_replace_xpath = '//*[@id="root"]/div[2]/div/div[4]/div[7]/div/div[4]/div/div/div/div/div/img'
                time.sleep(1)
                replace_icon = wait.until(EC.element_to_be_clickable((By.XPATH, link_replace_xpath)))
                replace_icon.click()
                time.sleep(1)
            except Exception as e:
                log_func(f"{prefix} ★ Error(置換アイコン): {e}")

            try:
                chk_xpath = f"//div[contains(text(), '{col3_chk}')]"
                chk_elem = wait.until(EC.element_to_be_clickable((By.XPATH, chk_xpath)))
                chk_elem.click()
            except Exception as e:
                log_func(f"{prefix} ★ Error(置換元選択): {e}")

            try:
                input_xpath = "//input[@placeholder='新規のリンクを入力']"
                input_elem = wait.until(EC.presence_of_element_located((By.XPATH, input_xpath)))

                driver.execute_script("""
                    var element = arguments[0];
                    var value = arguments[1];
                    var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                    setter.call(element, value);
                    element.dispatchEvent(new Event('input', { bubbles: true }));
                """, input_elem, col7_url)
            except Exception as e:
                log_func(f"{prefix} ★ Error(URL入力): {e}")
            time.sleep(1)

            try:
                replace_btn_xpath = '//*[@id="root"]/div[2]/div/div[4]/div[7]/div/div[4]/div/div[2]/div/div/div[2]/div[5]/div/div[2]'
                wait.until(EC.element_to_be_clickable((By.XPATH, replace_btn_xpath))).click()
            except:
                driver.execute_script("var b=Array.from(document.querySelectorAll('div')).find(e=>e.textContent=='置換');if(b)b.click();")
            time.sleep(1)

            driver.refresh()
            time.sleep(2)

            try:
                update_btn_xpath = "//button[text()='更新']"
                wait.until(EC.element_to_be_clickable((By.XPATH, update_btn_xpath))).click()

                target_class_fragment = "css-1g290g6"
                success_condition_xpath = f"//button[text()='更新' and contains(@class, '{target_class_fragment}')]"
                wait.until(EC.presence_of_element_located((By.XPATH, success_condition_xpath)))
                time.sleep(0.5)
            except Exception as e:
                try:
                    driver.execute_script("""
                    var btns = document.querySelectorAll("button");
                    var target = Array.from(btns).find(b => b.textContent.trim() === "更新");
                    if(target){ target.click(); }
                    """)
                    time.sleep(2)
                except:
                    pass

            try:
                current_url = driver.current_url
                if "#" in current_url:
                    base_url = current_url.split("#")[0]
                else:
                    base_url = current_url.rstrip("/").rsplit("/", 1)[0]

                target_url = base_url + "/exit_popups"
                driver.get(target_url)
                time.sleep(2)
            except Exception as e:
                log_func(f"{prefix} ★ Error(画面遷移): {e}")

            try:
                target_xpath = f"//h6[contains(text(), '{col4_key}')]"
                wait.until(EC.element_to_be_clickable((By.XPATH, target_xpath))).click()
            except:
                log_func(f"{prefix} ★ Error(対象選択): {col4_key}")

            try:
                base_xpath = "//span[@aria-label='ONにすると選択中のVersionにポップアップ/バナーが紐づきます']"
                wait.until(EC.presence_of_element_located((By.XPATH, base_xpath)))

                driver.execute_script("""
                var parentSpan = document.querySelector("span[aria-label='ONにすると選択中のVersionにポップアップ/バナーが紐づきます']");
                var input = parentSpan.querySelector("input");
                if(input && !input.checked){
                    input.click();
                }
                """)

                on_state_xpath = base_xpath + "[contains(@class, 'Mui-checked')]"
                wait.until(EC.presence_of_element_located((By.XPATH, on_state_xpath)))
            except Exception as e:
                log_func(f"{prefix} ★ Error(スイッチ): {e}")

            try:
                url_xpath = "//input[@name='urlControl']"
                url_input = wait.until(EC.element_to_be_clickable((By.XPATH, url_xpath)))

                current_val = url_input.get_attribute("value")

                if current_val != col7_url:
                    driver.execute_script("""
                        var element = arguments[0];
                        var value = arguments[1];
                        var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                        setter.call(element, value);
                        element.dispatchEvent(new Event('input', { bubbles: true }));
                    """, url_input, col7_url)

                    time.sleep(1)
                    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='本番反映']"))).click()
                    log_func(f"{prefix} 完了")
                else:
                    log_func(f"{prefix} 変更なし完了")

            except Exception as e:
                log_func(f"{prefix} ★ Error(反映): {e}")

            time.sleep(1)

    except Exception as e:
        log_func(f"[Worker-{worker_id}] 重大なエラー: {e}")
    finally:
        log_func(f"[Worker-{worker_id}] 終了")
        driver.quit()


# ==========================================
# ▼ GUI構築エリア ▼
# ==========================================

def main(page: ft.Page):
    page.title = "SquadBeyond 自動化ツール"

    # アップロードされたCSVの保存先
    upload_dir = tempfile.mkdtemp()
    page.upload_dir = upload_dir

    # 選択されたCSVパスを表示するテキスト
    selected_csv_path = ft.Text("ファイル未選択", size=12, color="grey")

    header = ft.Text("SquadBeyond 自動化ツール", size=24, weight="bold")

    if not ACCOUNTS:
        page.add(
            header,
            ft.Text("エラー: アカウント情報が読み込めません。", size=16, color="red"),
            ft.Text("環境変数 ACCOUNTS_CSV または accounts.csv を確認してください。", size=12),
        )
        return

  # アカウント選択用ドロップダウン（accounts.csvから動的生成）
    account_options = [
        ft.dropdown.Option(key=key, text=f"{key}: {acc['name']}")
        for key, acc in ACCOUNTS.items()
    ]
    account_dd = ft.Dropdown(
        label="使用するアカウントを選択",
        options=account_options,
        width=400,
    )

    # -----------------------------------------------------------
    # ファイルアップロード（Web対応）
    # -----------------------------------------------------------
    def pick_files_result(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            upload_list = [
                ft.FilePickerUploadFile(
                    e.files[0].name,
                    upload_url=page.get_upload_url(e.files[0].name, 600),
                )
            ]
            file_picker.upload(upload_list)

    def on_upload_progress(e: ft.FilePickerUploadProgressEvent):
        if e.progress == 1.0:
            uploaded_path = os.path.join(upload_dir, e.file_name)
            selected_csv_path.value = f"アップロード完了: {e.file_name}"
            selected_csv_path.color = "black"
            selected_csv_path.data = uploaded_path
            selected_csv_path.update()

    file_picker = ft.FilePicker(
        on_result=pick_files_result,
        on_upload=on_upload_progress,
    )
    page.overlay.append(file_picker)

    def on_click_select_file(_):
        file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=["csv"],
        )

    # ファイル選択ボタン
    btn_select_file = ft.ElevatedButton(
        text="CSVファイルを選択",
        icon="upload_file",
        on_click=on_click_select_file
    )

    log_list = ft.ListView(expand=True, spacing=5, auto_scroll=True)

    def add_log(message):
        log_list.controls.append(ft.Text(message, size=12))
        page.update()

    # 共通の実行処理
    def start_process(reset_rates_mode):
        if not account_dd.value:
            add_log("【エラー】アカウントを選択してください！")
            return

        csv_path = getattr(selected_csv_path, 'data', None)
        if not csv_path:
            add_log("【エラー】CSVファイルをアップロードしてください！")
            return

        selected_account = ACCOUNTS[account_dd.value]

        btn_reset.disabled = True
        btn_skip.disabled = True
        btn_select_file.disabled = True

        if reset_rates_mode:
            add_log("【モード】他を0%にして実行します")
        else:
            add_log("【モード】割合変更なしで実行します")

        page.update()

        t = threading.Thread(target=run_process_thread, args=(selected_account, reset_rates_mode, csv_path))
        t.start()

    # 裏側で動くメイン処理
    def run_process_thread(selected_account, reset_rates, csv_path):
        try:
            add_log(f"CSVを読み込みます: {os.path.basename(csv_path)}")

            try:
                df = pd.read_csv(csv_path, header=None)
            except Exception as e:
                add_log(f"エラー: ファイル読み込み失敗 -> {e}")
                return

            add_log("ドライバ準備完了。")

            cookies = get_session_cookies(selected_account, add_log)
            if not cookies:
                add_log("ログインに失敗したため、処理を終了します。")
                return

            total_rows = len(df)
            if total_rows == 0:
                add_log("データがありません")
                return

            chunk_size = math.ceil(total_rows / MAX_WORKERS)
            chunks = []
            for i in range(0, total_rows, chunk_size):
                chunks.append(df.iloc[i:i + chunk_size])

            add_log(f"合計 {total_rows} 件のデータを {len(chunks)} 分割して並列処理します。")

            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = []
                for i, df_subset in enumerate(chunks):
                    worker_id = i + 1
                    if i > 0:
                        add_log(f"次のブラウザ起動まで 5秒 待機します...")
                        time.sleep(5)

                    futures.append(
                        executor.submit(run_automation_worker, worker_id, df_subset, cookies, add_log, reset_rates)
                    )

                concurrent.futures.wait(futures)

            add_log("全並列処理が完了しました。")

        except Exception as e:
            add_log(f"予期せぬエラーが発生しました: {e}")
        finally:
            btn_reset.disabled = False
            btn_skip.disabled = False
            btn_select_file.disabled = False
            page.update()

    # 実行ボタン
    btn_reset = ft.ElevatedButton(
        text="実行 (他を0%にする)",
        on_click=lambda e: start_process(True),
        height=50,
        bgcolor="red100",
        color="red900"
    )

    btn_skip = ft.ElevatedButton(
        text="実行 (割合変更なし)",
        on_click=lambda e: start_process(False),
        height=50
    )

    # 画面レイアウト
    page.add(
        header,
        account_dd,
        ft.Divider(),
        ft.Text("CSVファイル選択:"),
        ft.Row([btn_select_file, selected_csv_path], alignment="start", vertical_alignment="center"),
        ft.Divider(),
        ft.Row([btn_reset, btn_skip], alignment="center", spacing=20),
        ft.Text("実行ログ:"),
        ft.Container(
            content=log_list,
            border=ft.border.all(1, "grey"),
            border_radius=5,
            padding=10,
            height=300,
        )
    )

ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=int(os.environ.get("PORT", 8080)))
