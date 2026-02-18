import time
import os
import math
import pandas as pd
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ==========================================
# ▼ 設定エリア ▼
# ==========================================

LOGIN_URL = 'https://app.squadbeyond.com/' 
BASE_URL = 'https://app.squadbeyond.com/' # Cookie設定用のベースURL
CSV_FILENAME = 'beyond複製シート - 出力用.csv'

# 並列数
MAX_WORKERS = 3

ACCOUNTS = {
    "1": {
        "id": "kotone_takahashi@organic-gr.com",
        "pass": "Va+5bsM+eGB*"
    },
    "2": {
        "id": "hiroto_sato@organic-gr.com",
        "pass": "Hyhm3101610!"
    }
}

# ==========================================

def get_session_cookies(account_info, driver_path):
    """
    最初に1回だけログインを行い、セッションCookieを取得する関数
    """
    print(">>> [準備] ログインセッションを取得します...")
    
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless") 
    driver = webdriver.Chrome(service=Service(driver_path), options=options)
    wait = WebDriverWait(driver, 20)
    cookies = []

    try:
        driver.get(LOGIN_URL)
        time.sleep(2)

        # ユーザーID
        email_xpath = "//input[@id=':r1:'] | //input[@name='email']"
        email_input = wait.until(EC.element_to_be_clickable((By.XPATH, email_xpath)))
        email_input.clear()
        email_input.send_keys(account_info['id'])

        # パスワード
        pass_xpath = "//input[@id=':r2:'] | //input[@type='password']"
        pass_input = wait.until(EC.element_to_be_clickable((By.XPATH, pass_xpath)))
        pass_input.clear()
        pass_input.send_keys(account_info['pass'])

        # 1つ目のボタン
        btn1_xpath = "//button[@data-trackid='sign-in-form-login-button']"
        wait.until(EC.element_to_be_clickable((By.XPATH, btn1_xpath))).click()
        time.sleep(3) 

        # 2つ目のボタン
        btn2_xpath = "//button[text()='ログイン' and contains(@class, 'MuiButton-sizeSmall')]"
        wait.until(EC.element_to_be_clickable((By.XPATH, btn2_xpath))).click()
        
        # ログイン完了待ち（確実にCookieが入るまで待つ）
        print(">>> [準備] ログイン処理完了。待機中...")
        time.sleep(5)
        
        # Cookieを取得
        cookies = driver.get_cookies()
        print(">>> [準備] セッション情報の取得に成功しました。")

    except Exception as e:
        print(f">>> [エラー] ログインに失敗しました: {e}")
    finally:
        driver.quit()
    
    return cookies

def run_automation_worker(worker_id, df_subset, cookies, driver_path):
    """
    Cookieを使ってログイン済みの状態で作業するワーカースレッド
    """
    print(f"[Worker-{worker_id}] ブラウザを起動します...")
    
    options = webdriver.ChromeOptions()
    # ウィンドウ位置をずらす
    options.add_argument(f"--window-position={50 + (worker_id-1)*400},{50 + (worker_id-1)*50}")
    options.add_argument("--window-size=1000,900")
    
    driver = webdriver.Chrome(service=Service(driver_path), options=options)
    wait = WebDriverWait(driver, 20)

    try:
        # ---------------------------------------------------------
        # Cookie適用処理（ログインスキップ）
        # ---------------------------------------------------------
        
        # まずドメインにアクセス（Cookieはドメインが一致しないとセットできないため）
        driver.get(BASE_URL)
        
        # 取得しておいたCookieを適用
        if not cookies:
            print(f"[Worker-{worker_id}] ★ エラー: Cookieがありません。処理を中断します。")
            driver.quit()
            return

        for cookie in cookies:
            # expiryがfloatだとエラーになる場合があるのでint変換（念のため）
            if 'expiry' in cookie:
                cookie['expiry'] = int(cookie['expiry'])
            driver.add_cookie(cookie)
        
        # Cookie適用後にリロードしてログイン状態にする
        driver.refresh()
        time.sleep(3) # ログイン反映待ち
        
        print(f"[Worker-{worker_id}] セッション適用完了。処理を開始します。")

        # ---------------------------------------------------------
        # ループ実行
        # ---------------------------------------------------------
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
            print(f"{prefix} 開始: {col1_url}")

            # 1. Open
            driver.get(col1_url)
            time.sleep(2)
            
            # 2. 複製元version
            try:
                xpath_ver = f"//span[@data-test='ArticleList-Memo' and contains(text(), '{col2_ver}')]"
                wait.until(EC.element_to_be_clickable((By.XPATH, xpath_ver))).click()
            except Exception:
                print(f"{prefix} ★ Skip: 複製元Versionなし")
                continue

            # 3. メニューボタン
            try:
                menu_xpath = '//*[@id="root"]/div[2]/div/div[4]/div[2]/div/div[2]/div/div[2]/div/div[2]/button'
                wait.until(EC.element_to_be_clickable((By.XPATH, menu_xpath))).click()
                time.sleep(0.5) 
                
                # 4. 「別のbeyondページに複製」
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

            # 5. 複製先
            try:
                select_xpath = "//select[@data-test='DuplicateToOtherModal-DestinationAbTestUidSelect']"
                select_elem = wait.until(EC.presence_of_element_located((By.XPATH, select_xpath)))
                Select(select_elem).select_by_visible_text(col5_lbl)
                
                # 6. 「複製する」
                btn_xpath = "//div[contains(text(), '複製する')]"
                wait.until(EC.element_to_be_clickable((By.XPATH, btn_xpath))).click()
            except Exception as e:
                print(f"{prefix} ★ Error(複製): {e}")

            time.sleep(3)

            # 7. 配信割合100%
            try:
                rate_xpath = f"//input[@value='{col4_key}']/following::div[@data-test='ArticleList-DeriveryUpRateForm'][1]"
                wait.until(EC.element_to_be_clickable((By.XPATH, rate_xpath))).click()
            except Exception as e:
                print(f"{prefix} ★ Error(割合): {e}")

            
            # 9. リンク置換
            try:
                link_replace_xpath = '//*[@id="root"]/div[2]/div/div[4]/div[7]/div/div[4]/div/div/div/div/div/img'
                time.sleep(1)
                replace_icon = wait.until(EC.element_to_be_clickable((By.XPATH, link_replace_xpath)))
                replace_icon.click()
                time.sleep(1) 
            except Exception as e:
                print(f"{prefix} ★ Error(置換アイコン): {e}")

            # 10. 置換元選択
            try:
                chk_xpath = f"//div[contains(text(), '{col3_chk}')]"
                chk_elem = wait.until(EC.element_to_be_clickable((By.XPATH, chk_xpath)))
                chk_elem.click()
            except Exception as e:
                print(f"{prefix} ★ Error(置換元選択): {e}")

            # 11. URL入力
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
                print(f"{prefix} ★ Error(URL入力): {e}")
            time.sleep(1) 

            # 12. 置換実行
            try:
                replace_btn_xpath = '//*[@id="root"]/div[2]/div/div[4]/div[7]/div/div[4]/div/div[2]/div/div/div[2]/div[5]/div/div[2]'
                wait.until(EC.element_to_be_clickable((By.XPATH, replace_btn_xpath))).click()
            except:
                driver.execute_script("var b=Array.from(document.querySelectorAll('div')).find(e=>e.textContent=='置換');if(b)b.click();")
            time.sleep(1) 
            
            # 13. 更新
            driver.refresh()
            time.sleep(2) 

            # 14. 更新ボタン
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

            # 15. ページ遷移
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
                print(f"{prefix} ★ Error(画面遷移): {e}")

            # 16. 対象選択
            try:
                target_xpath = f"//h6[contains(text(), '{col4_key}')]"
                wait.until(EC.element_to_be_clickable((By.XPATH, target_xpath))).click()
            except:
                print(f"{prefix} ★ Error(対象選択): {col4_key}")

            # 17. スイッチON
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
                print(f"{prefix} ★ Error(スイッチ): {e}")

            # 18. 反映
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
                    print(f"{prefix} 完了")
                else:
                    print(f"{prefix} 変更なし完了")

            except Exception as e:
                print(f"{prefix} ★ Error(反映): {e}")

            time.sleep(1)

    except Exception as e:
        print(f"[Worker-{worker_id}] 重大なエラー: {e}")
    finally:
        print(f"[Worker-{worker_id}] 終了")
        driver.quit()

def main():
    print("--------------------------------------------------")
    print("使用するアカウントを選択してください (3並列で実行します):")
    print("  [1] kotone_takahashi")
    print("  [2] hiroto_sato")
    print("--------------------------------------------------")
    choice = input("番号を入力してください: ").strip()
    selected_account = ACCOUNTS.get(choice)

    # --- CSV読み込み ---
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, CSV_FILENAME)
    print(f"CSVを読み込みます: {csv_path}")
    
    try:
        df = pd.read_csv(csv_path, header=None)
    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません -> {csv_path}")
        return

    # --- ★重要: ここで一度だけドライバの準備を行う (競合回避) ---
    print("ドライバを確認中...")
    driver_path = ChromeDriverManager().install()
    print("ドライバ準備完了。")

    # --- ★追加: 代表して1回だけログインし、Cookieを取得 ---
    cookies = get_session_cookies(selected_account, driver_path)
    if not cookies:
        print("ログインに失敗したため、処理を終了します。")
        return

    # --- データを3分割する ---
    total_rows = len(df)
    if total_rows == 0:
        print("データがありません")
        return

    chunk_size = math.ceil(total_rows / MAX_WORKERS)
    chunks = []
    for i in range(0, total_rows, chunk_size):
        chunks.append(df.iloc[i:i + chunk_size])

    print(f"\n合計 {total_rows} 件のデータを {len(chunks)} 分割して並列処理します。")
    print("="*60)

    # --- 並列実行開始 ---
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for i, df_subset in enumerate(chunks):
            worker_id = i + 1
            
            if i > 0:
                print(f"次のブラウザ起動まで 5秒 待機します...")
                time.sleep(5)

            # Cookieを渡してスレッド起動
            futures.append(
                executor.submit(run_automation_worker, worker_id, df_subset, cookies, driver_path)
            )
        
        concurrent.futures.wait(futures)

    print("\n" + "="*60)
    print("全並列処理が完了しました。")
    print("終了するにはEnterを押してください...")
    input()

if __name__ == "__main__":
    main()