import streamlit as st
import random
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import extra_streamlit_components as stx  # 引入 Cookie 管理套件

# ==============================================================================
# 設定區：發信專用的 Gmail 資訊 (請替換成您的專屬資料)
# ==============================================================================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = "timbot000001@gmail.com"        # 填入發信用的 Gmail
SENDER_PASSWORD = "kooh dutv dggo ecfm"     # 填入 16 位元的「應用程式密碼」

# ==============================================================================
# 核心外掛：Cookie 記憶型 - 公司信箱動態驗證碼 (OTP) 24小時免驗證版 (英文信件版)
# ==============================================================================

# 1. 初始化 Cookie 管理器
cookie_manager = stx.CookieManager()

# 2. 嘗試從同仁的瀏覽器讀取 24 小時內的登入紀錄
auth_cookie = cookie_manager.get(cookie="sys_auth_verified")
saved_email = cookie_manager.get(cookie="sys_auth_email")

# 初始化 Session 狀態
if "authenticated" not in st.session_state:
    if auth_cookie == "true":
        st.session_state.authenticated = True
        st.session_state.user_email = saved_email if saved_email else "Authenticated User"
    else:
        st.session_state.authenticated = False

if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False
if "real_otp" not in st.session_state:
    st.session_state.real_otp = None
if "user_email" not in st.session_state:
    if auth_cookie == "true" and saved_email:
        st.session_state.user_email = saved_email
    else:
        st.session_state.user_email = ""

def send_otp_email(to_email, otp_code):
    """ 透過 Gmail SMTP 自動寄送英文驗證碼 """
    # 📝 郵件內文改為全英文
    mail_content = (
        f"Dear Colleague,\n\n"
        f"You are attempting to log in to the Carrier DG Restriction Query System.\n"
        f"Your security verification code is: 【 {otp_code} 】\n\n"
        f"Please enter this code on the webpage to complete your identity verification. "
        f"The verification code is valid until the browser tab is closed.\n\n"
        f"Security Notice: Please do not share this verification code with external personnel."
    )
    
    msg = MIMEText(mail_content, 'plain', 'utf-8')
    # 📝 寄件者名稱與主旨改為全英文
    msg['From'] = Header(f"DG System Auto-Mail <{SENDER_EMAIL}>", 'utf-8')
    msg['To'] = Header(to_email, 'utf-8')
    msg['Subject'] = Header("[Security Verification] Carrier DG Restriction Query System - OTP Code", 'utf-8')
    
    try:
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, [to_email], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Failed to send email. Please check SMTP settings. Error: {e}")
        return False

# --- UI 驗證介面呈現 ---
if not st.session_state.authenticated:
    st.title("🔒 同仁安全身份驗證")
    st.write("本系統含有內部敏感資料，請先使用公司電子郵件進行身份驗證。")
    
    # 步驟 1：輸入信箱並發送驗證碼
    email_input = st.text_input(
        "請輸入您的公司電子郵件信箱：", 
        value=st.session_state.user_email,
        placeholder="example@interasialine.com",
        disabled=st.session_state.otp_sent
    )
    
    if not st.session_state.otp_sent:
        if st.button("發送動態驗證碼", type="primary"):
            clean_email = email_input.strip().lower()
            
            # 🔒 僅限指定信箱網域才能通過
            ALLOWED_DOMAINS = ("@interasialine.com",)
            
            if not clean_email.endswith(ALLOWED_DOMAINS):
                st.error("❌ 存取拒絕：本系統僅限使用 @interasialine.com 結尾的公司信箱驗證登入。")
            else:
                generated_otp = str(random.randint(100000, 999999))
                with st.spinner("正在發送驗證碼至您的公司信箱..."):
                    if send_otp_email(clean_email, generated_otp):
                        st.session_state.otp_sent = True
                        st.session_state.real_otp = generated_otp
                        st.session_state.user_email = clean_email
                        st.success(f"✅ 驗證碼已成功寄送至 {clean_email}，請至信箱收信。")
                        st.rerun()
    
    # 步驟 2：輸入收到的驗證碼
    else:
        st.info(f"驗證碼已寄送至：{st.session_state.user_email}")
        otp_input = st.text_input("請輸入信箱收到的 6 位數驗證碼：", type="default", max_chars=6)
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("確認驗證", type="primary"):
                if otp_input.strip() == st.session_state.real_otp:
                    st.session_state.authenticated = True
                    
                    # 🍪 驗證成功，塞入 Cookie 記憶 24 小時 (86400秒)
                    cookie_manager.set("sys_auth_verified", "true", max_age=86400)
                    cookie_manager.set("sys_auth_email", st.session_state.user_email, max_age=86400)
                    
                    st.success("🔓 驗證成功！正在登入系統...")
                    st.rerun()
                else:
                    st.error("❌ 驗證碼錯誤，請重新確認。")
        with col2:
            if st.button("返回修改信箱"):
                st.session_state.otp_sent = False
                st.session_state.real_otp = None
                st.rerun()
                
        st.caption("💡 沒收到信？請檢查垃圾信箱，或點擊「返回修改信箱」重新發送。")
    st.stop()

# ==============================================================================
# 3. 這裡以下，完全接回您原本那一長串的「船東危險品禁裝清單查詢系統」程式碼
# ==============================================================================
# 側邊欄加上登入者提示
st.sidebar.info(f"👤 當前登入：{st.session_state.user_email}")
