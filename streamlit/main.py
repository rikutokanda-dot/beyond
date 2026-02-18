import streamlit as st
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ==========================================
# ▼ 設定エリア ▼
# ==========================================

LOGIN_URL = 'https://app.squadbeyond.com/' 
BASE_URL = 'https://app.squadbeyond.com/'

# Streamlitではセキュリティのため、コードに直接パスワードを書くのは非推奨です。
# ローカルでテストする場合や、Streamlit CloudのSecrets機能を使うことを想定しています。
# st.secrets からパスワードを読み込む形にする
ACCOUNTS = {
    "1": {
        "name": "kotone_takahashi",
        "id": "kotone_takahashi@organic-gr.com",
        "pass": st.secrets["passwords"]["p1"] # 金庫のp1を取り出す
    },
    "2": {
        "name": "hiroto_sato",
        "id": "hiroto_sato@organic-gr.com",
        "pass": st.secrets["passwords"]["p2"]
    },
    },
    "3": {
        "name": "rikuto_kanda",
        "id": "rikuto_kanda@organic-gr.com",
        "pass": st.secrets["passwords"]["p3"]
    },
    "4": {
        "name": "moeka_kosugi",
        "id": "moeka_kosugi@yomite.co.jp",
        "pass": st.secrets["passwords"]["p4"]
    },
    "5": {
        "name": "miku_ando",
        "id": "miku_ando@organic-gr.com",
        "pass": st.secrets["passwords"]["p5"]
    },
    "6": {
        "name": "jou_cobham",
        "id": "jou_cobham@organic-gr.com",
        "pass": st.secrets["passwords"]["p6"]
    }
    "7": {
        "name": "daisuke_watanabe",
        "id": "daisuke_watanabe@organic-gr.com",
        "pass": st.secrets["passwords"]["p7"]
    },
    "8": {
        "name": "minato_mitasaki",
        "id": "minato_mitasaki@organic-gr.com",
        "pass": st.secrets["passwords"]["p8"]
    },
    "9": {
        "name": "yuki_ogawa",
        "id": "yuki_ogawa@organic-gr.com",
        "pass": st.secrets["passwords"]["p9"]
    },
    "10": {
        "name": "ryunosuke_kageyama",
        "id": "ryunosuke_kageyama@organic-gr.com",
        "pass": st.secrets["passwords"]["p10"]
    },
    "11": {
        "name": "kotomi.addict",
        "id": "kotomi.addict@gmail.com",
        "pass": st.secrets["passwords"]["p11"]
    },
    "12": {
        "name": "natsuko_yamauchi",
        "id": "natsuko_yamauchi@organic-gr.com",
        "pass": st.secrets["passwords"]["p12"]
    },
    "13": {
        "name": "yuya_nakanishi",
        "id": "yuya_nakanishi@organic-gr.com",
        "pass": st.secrets["passwords"]["p13"]
    }
}


# ==========================================
# ▼ 関数定義 ▼
# ==========================================

def get_driver():
    """Webアプリ用に最適化されたChromeドライバを作成する関数"""
    options = Options()
    options.add_argument('--headless')  # 必須: 画面なしモード
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument("--window-size=1920,1080") # ヘッドレスでも解像度は指定推奨
    
    # Streamlit Cloud等でドライバが見つからないエラーを防ぐための記述
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        # ローカル等でうまくいかない場合の予備
        driver = webdriver.Chrome(options=options)
        
    return driver

def get_session_cookies(account_info):
    st.info(">>> [準備] ログインセッションを取得します...")
    
    driver = get_driver()
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
        
        st.write(">>> [準備] ログイン処理完了。待機中...")
        time.sleep(5)
        
        cookies = driver.get_cookies()
        st.success(">>> [準備] セッション情報の取得に成功しました。")

    except Exception as e:
        st.error(f">>> [エラー] ログインに失敗しました: {e}")
        return None
    finally:
        driver.quit()
    
    return cookies

def run_automation_single(index, row, cookies, reset_rates):
    """1行分の処理を行う関数"""
    driver = get_driver()
    wait = WebDriverWait(driver, 20)
    
    # ログ用のプレフィックス
    prefix = f"[{index+1}件目]"
    msg_container = st.empty() # ログを更新表示する枠
    
    def log(msg):
        msg_container.text(f"{prefix} {msg}")
        print(f"{prefix} {msg}")

    try:
        driver.get(BASE_URL)
        
        # Cookie適用
        for cookie in cookies:
            if 'expiry' in cookie:
                cookie['expiry'] = int(cookie['expiry'])
            driver.add_cookie(cookie)
        
        driver.refresh()
        time.sleep(3)
        
        col1_url = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
        col2_ver = str(row.iloc[1]) if pd.notna(row.iloc[1]) else ""
        col3_chk = str(row.iloc[2]) if pd.notna(row.iloc[2]) else ""
        col4_key = str(row.iloc[3]) if pd.notna(row.iloc[3]) else ""
        col5_lbl = str(row.iloc[4]) if pd.notna(row.iloc[4]) else ""
        col7_url = str(row.iloc[6]) if pd.notna(row.iloc[6]) else ""
        
        if not col1_url or col1_url == 'nan' or col1_url == "": 
            return "Skip (URLなし)"

        log(f"開始: {col1_url}")
        driver.get(col1_url)
        time.sleep(2)
        
        # --- ここから元のロジック ---
        
        # Version選択
        try:
            xpath_ver = f"//span[@data-test='ArticleList-Memo' and contains(text(), '{col2_ver}')]"
            wait.until(EC.element_to_be_clickable((By.XPATH, xpath_ver))).click()
        except Exception:
            log("★ Skip: 複製元Versionなし")
            return "Skip (Versionなし)"

        # メニュー操作
        try:
            menu_xpath = '//*[@id="root"]/div[2]/div/div[4]/div[2]/div/div[2]/div/div[2]/div/div[2]/button'
            wait.until(EC.element_to_be_clickable((By.XPATH, menu_xpath))).click()
            time.sleep(0.5) 
            
            clone_menu_xpath = "//span[contains(text(), '別のbeyondページに複製')]"
            wait.until(EC.element_to_be_clickable((By.XPATH, clone_menu_xpath))).click()
        except:
            driver.execute_script("var spans=document.querySelectorAll('span');for(var i=0;i<spans.length;i++){if(spans[i].textContent.includes('別のbeyondページに複製')){spans[i].click();break;}}")
        time.sleep(1)

        # 複製モーダル
        try:
            select_xpath = "//select[@data-test='DuplicateToOtherModal-DestinationAbTestUidSelect']"
            select_elem = wait.until(EC.presence_of_element_located((By.XPATH, select_xpath)))
            Select(select_elem).select_by_visible_text(col5_lbl)
            
            btn_xpath = "//div[contains(text(), '複製する')]"
            wait.until(EC.element_to_be_clickable((By.XPATH, btn_xpath))).click()
        except Exception as e:
            log(f"★ Error(複製): {e}")

        time.sleep(3)

        # 割合設定
        try:
            rate_xpath = f"//input[@value='{col4_key}']/following::div[@data-test='ArticleList-DeriveryUpRateForm'][1]"
            wait.until(EC.element_to_be_clickable((By.XPATH, rate_xpath))).click()
        except Exception as e:
            log(f"★ Error(割合): {e}")

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
        
        # 置換アイコンクリック
        try:
            link_replace_xpath = '//*[@id="root"]/div[2]/div/div[4]/div[7]/div/div[4]/div/div/div/div/div/img'
            time.sleep(1)
            replace_icon = wait.until(EC.element_to_be_clickable((By.XPATH, link_replace_xpath)))
            replace_icon.click()
            time.sleep(1) 
        except Exception as e:
            log(f"★ Error(置換アイコン): {e}")

        # 置換元選択
        try:
            chk_xpath = f"//div[contains(text(), '{col3_chk}')]"
            chk_elem = wait.until(EC.element_to_be_clickable((By.XPATH, chk_xpath)))
            chk_elem.click()
        except Exception as e:
            log(f"★ Error(置換元選択): {e}")

        # URL入力
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
            log(f"★ Error(URL入力): {e}")
        time.sleep(1) 

        # 置換実行ボタン
        try:
            replace_btn_xpath = '//*[@id="root"]/div[2]/div/div[4]/div[7]/div/div[4]/div/div[2]/div/div/div[2]/div[5]/div/div[2]'
            wait.until(EC.element_to_be_clickable((By.XPATH, replace_btn_xpath))).click()
        except:
            driver.execute_script("var b=Array.from(document.querySelectorAll('div')).find(e=>e.textContent=='置換');if(b)b.click();")
        time.sleep(1) 
        
        driver.refresh()
        time.sleep(2) 

        # 更新ボタン
        try:
            update_btn_xpath = "//button[text()='更新']"
            wait.until(EC.element_to_be_clickable((By.XPATH, update_btn_xpath))).click()
            target_class_fragment = "css-1g290g6"
            success_condition_xpath = f"//button[text()='更新' and contains(@class, '{target_class_fragment}')]"
            wait.until(EC.presence_of_element_located((By.XPATH, success_condition_xpath)))
            time.sleep(0.5)
        except Exception as e:
            try:
                driver.execute_script("var btns = document.querySelectorAll('button'); var target = Array.from(btns).find(b => b.textContent.trim() === '更新'); if(target){ target.click(); }")
                time.sleep(2) 
            except:
                pass

        # 画面遷移 (exit_popups)
        try:
            current_url = driver.current_url
            if "#" in current_url:
                base_url_current = current_url.split("#")[0]
            else:
                base_url_current = current_url.rstrip("/").rsplit("/", 1)[0]
            target_url_nav = base_url_current + "/exit_popups"
            driver.get(target_url_nav)
            time.sleep(2)
        except Exception as e:
            log(f"★ Error(画面遷移): {e}")

        # 対象選択
        try:
            target_xpath = f"//h6[contains(text(), '{col4_key}')]"
            wait.until(EC.element_to_be_clickable((By.XPATH, target_xpath))).click()
        except:
            log(f"★ Error(対象選択): {col4_key}")

        # スイッチON
        try:
            base_xpath = "//span[@aria-label='ONにすると選択中のVersionにポップアップ/バナーが紐づきます']"
            wait.until(EC.presence_of_element_located((By.XPATH, base_xpath)))
            driver.execute_script("""
            var parentSpan = document.querySelector("span[aria-label='ONにすると選択中のVersionにポップアップ/バナーが紐づきます']");
            var input = parentSpan.querySelector("input");
            if(input && !input.checked){ input.click(); }
            """)
            on_state_xpath = base_xpath + "[contains(@class, 'Mui-checked')]"
            wait.until(EC.presence_of_element_located((By.XPATH, on_state_xpath)))
        except Exception as e:
            log(f"★ Error(スイッチ): {e}")

        # 本番反映
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
                log("完了 (反映済み)")
                return "Success"
            else:
                log("完了 (変更なし)")
                return "No Change"

        except Exception as e:
            log(f"★ Error(反映): {e}")
            return f"Error: {e}"

    except Exception as e:
        log(f"重大なエラー: {e}")
        return f"Critical Error: {e}"
    finally:
        driver.quit()

# ==========================================
# ▼ GUI構築エリア (Streamlit) ▼
# ==========================================

def main():
    st.set_page_config(page_title="SquadBeyond 自動化ツール", layout="wide")
    st.title("SquadBeyond 自動化ツール (Web版)")

    # サイドバー：設定
    st.sidebar.header("設定")
    
    # アカウント選択
    account_keys = list(ACCOUNTS.keys())
    account_labels = [f"{k}: {ACCOUNTS[k]['name']}" for k in account_keys]
    selected_label = st.sidebar.selectbox("アカウント選択", account_labels)
    selected_key = selected_label.split(":")[0]
    
    # CSVアップロード
    uploaded_file = st.sidebar.file_uploader("CSVファイルをアップロード", type=["csv"])
    
    # モード選択
    reset_rates_mode = st.sidebar.checkbox("他を0%にして実行する", value=True)

    # 実行ボタン
    if st.sidebar.button("処理開始"):
        # バリデーション
        account_data = ACCOUNTS[selected_key]
        if not account_data["pass"]:
            st.error("【エラー】コード内のパスワードが空です。ACCOUNTS辞書を設定してください。")
            return
            
        if uploaded_file is None:
            st.error("CSVファイルをアップロードしてください。")
            return

        # CSV読み込み
        try:
            df = pd.read_csv(uploaded_file, header=None)
            st.write(f"データ件数: {len(df)}件")
            st.dataframe(df.head()) # プレビュー
        except Exception as e:
            st.error(f"CSV読み込みエラー: {e}")
            return

        # ログイン試行
        cookies = get_session_cookies(account_data)
        if not cookies:
            st.error("ログイン失敗のため中止します。")
            return

        # メイン処理ループ
        st.write("--- 処理を開始します ---")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        
        for i, row in df.iterrows():
            status_text.text(f"処理中... {i+1} / {len(df)}")
            result_status = run_automation_single(i, row, cookies, reset_rates_mode)
            results.append(result_status)
            progress_bar.progress((i + 1) / len(df))
            
        st.success("すべての処理が完了しました！")
        
        # 結果のダウンロード
        df["Result"] = results
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="結果CSVをダウンロード",
            data=csv,
            file_name='result_log.csv',
            mime='text/csv',
        )

if __name__ == "__main__":
    main()
