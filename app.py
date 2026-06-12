import streamlit as st
import datetime  
import random
import smtplib
import time  # 引入時間模組來處理時間差
from email.mime.text import MIMEText
from email.header import Header
import extra_streamlit_components as stx
import pandas as pd
import os
import re
import requests

# ==============================================================================
# 📊 MODULE: Real-Time Online Users Tracker
# ==============================================================================
class SystemAnalytics:
    def __init__(self):
        self.total_clicks = 0
        self.total_logins = 0
        self.active_users = {}  # Stores { user_identity: last_activity_timestamp }

    def update_activity(self, user_id):
        """Update the last active timestamp for a user"""
        self.active_users[user_id] = datetime.datetime.now()

    def get_active_users(self, minutes=10):
        """Filter and return the number of active users within the timeframe"""
        now = datetime.datetime.now()
        self.active_users = {
            u: t for u, t in self.active_users.items() 
            if (now - t).total_seconds() < minutes * 60
        }
        return len(self.active_users)

# Use st.cache_resource to share this tracker across all sessions/users globally
@st.cache_resource
def get_analytics_tracker():
    return SystemAnalytics()

tracker = get_analytics_tracker()

# Track the current user's activity on every rerun
current_user = st.session_state.get('user_email', '').strip()
if not current_user:
    current_user = 'Guest'
tracker.update_activity(current_user)

# ==============================================================================
# SETTINGS: Dedicated Gmail account for sending emails
# ==============================================================================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = "timbot000001@gmail.com"
SENDER_PASSWORD = "kooh dutv dggo ecfm"

# ==============================================================================
# CORE MODULE: Cookie Verification (F5 Proof)
# ==============================================================================
cookie_manager = stx.CookieManager(key="secure_auth_manager")

if "cookie_initialized" not in st.session_state:
    with st.spinner("🔒 Securing connection..."):
        time.sleep(0.5)  # 讓 JavaScript 與 Python 同步
        st.session_state.cookie_initialized = True
        st.rerun()

auth_cookie = cookie_manager.get(cookie="company_dg_auth")
saved_email = cookie_manager.get(cookie="company_dg_email")

if auth_cookie == "authenticated_success" and saved_email:
    st.session_state.authenticated = True
    st.session_state.user_email = saved_email
else:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False
if "real_otp" not in st.session_state:
    st.session_state.real_otp = None
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

def send_otp_email(to_email, otp_code):
    """ 發送安全驗證碼郵件 """
    mail_content = (
        f"Dear Colleague,\n\n"
        f"You are attempting to log in to the Carrier DG Restriction Query System.\n"
        f"Your security verification code is: 【 {otp_code} 】\n\n"
        f"Please enter this code on the webpage to complete your identity verification."
    )
    msg = MIMEText(mail_content, 'plain', 'utf-8')
    msg['From'] = Header(f"DG System Auto-Mail <{SENDER_EMAIL}>", 'utf-8')
    msg['To'] = Header(to_email, 'utf-8')
    msg['Subject'] = Header("[Security Verification] DG Query System - OTP Code", 'utf-8')
    
    try:
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, [to_email], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Failed to send email. Error: {e}")
        return False

# --- UI 身分驗證介面 ---
if not st.session_state.authenticated:
    st.title("🔒 Employee Security Verification")
    st.write("This system contains internal sensitive data. Please verify your identity first.")
    
    email_input = st.text_input(
        "Company Email Address:", 
        value=st.session_state.user_email,
        placeholder="example@interasialine.com",
        disabled=st.session_state.otp_sent
    )
    
    if not st.session_state.otp_sent:
        if st.button("Send Verification Code", type="primary"):
            clean_email = email_input.strip().lower()
            ALLOWED_DOMAINS = ("@interasialine.com",)
            
            if not clean_email.endswith(ALLOWED_DOMAINS):
                st.error("❌ Access Denied: This system is restricted to company emails.")
            else:
                generated_otp = str(random.randint(100000, 999999))
                with st.spinner("Sending verification code..."):
                    if send_otp_email(clean_email, generated_otp):
                        st.session_state.otp_sent = True
                        st.session_state.real_otp = generated_otp
                        st.session_state.user_email = clean_email
                        st.success(f"✅ Verification code sent to {clean_email}.")
                        st.rerun()
    else:
        st.info(f"Verification code sent to: {st.session_state.user_email}")
        otp_input = st.text_input("Enter the 6-digit verification code:", type="default", max_chars=6)
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Verify", type="primary"):
                if otp_input.strip() == st.session_state.real_otp:
                    st.session_state.authenticated = True
                    cookie_manager.set(
                        "company_dg_auth", 
                        "authenticated_success", 
                        key="write_auth_cookie", 
                        max_age=86400,
                        same_site="none",
                        secure=True
                    )
                    cookie_manager.set(
                        "company_dg_email", 
                        st.session_state.user_email, 
                        key="write_email_cookie", 
                        max_age=86400,
                        same_site="none",
                        secure=True
                    )
                    st.success("🔓 Verification successful! Logging in...")
                    st.rerun()
                else:
                    st.error("❌ Invalid verification code. Please try again.")
        with col2:
            if st.button("Back"):
                st.session_state.otp_sent = False
                st.session_state.real_otp = None
                st.rerun()
    st.stop()

# ==============================================================================
# MAIN APPLICATION INTERFACE
# ==============================================================================
st.set_page_config(page_title="Carrier DG Prohibited List Query System", layout="wide")

# Sidebar Configuration
st.sidebar.metric("📊 Active Users", f"{tracker.get_active_users(minutes=10)} online")
st.sidebar.info(f"👤 Logged in as: {st.session_state.user_email}")

if st.sidebar.button("Log Out 🔒"):
    cookie_manager.delete("company_dg_auth", key="delete_auth_cookie")
    cookie_manager.delete("company_dg_email", key="delete_email_cookie")
    st.session_state.authenticated = False
    st.session_state.cookie_initialized = False
    st.rerun()

# Data File Paths
excel_file = "dg_list.xlsx"
if not os.path.exists(excel_file):
    excel_file = os.path.join("DG_System", "dg_list.xlsx")

master_file = "imdg_master.xlsx"
if not os.path.exists(master_file):
    master_file = os.path.join("DG_System", "imdg_master.xlsx")

# Cache Functions
@st.cache_data
def load_carrier_excel(file_path, file_timestamp):
    if os.path.exists(file_path):
        return pd.read_excel(file_path, sheet_name=None)
    return None

@st.cache_data
def load_imdg_master(file_path, file_timestamp):
    if os.path.exists(file_path):
        df = pd.read_excel(file_path, dtype=str)
        df.columns = df.columns.astype(str).str.strip()
        return df
    return None

excel_time = os.path.getmtime(excel_file) if os.path.exists(excel_file) else 0
master_time = os.path.getmtime(master_file) if os.path.exists(master_file) else 0

excel_sheets = load_carrier_excel(excel_file, excel_time)
raw_master_df = load_imdg_master(master_file, master_time)

# Custom CSS
st.markdown("""
    <style>
    .psn-card {
        padding: 20px; border-radius: 10px; margin-bottom: 20px;
        background: linear-gradient(135deg, #1e3a8a, #3b82f6); color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .partner-card {
        padding: 20px; border-radius: 10px; margin-bottom: 15px;
        border-left: 8px solid #cbd5e1; background-color: #f8fafc;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .status-badge {
        font-size: 20px !important; font-weight: bold; padding: 4px 12px;
        border-radius: 5px; display: inline-block; margin-bottom: 0px;
    }
    .version-badge {
        font-size: 13px !important; background-color: #e2e8f0; color: #475569;
        padding: 2px 8px; border-radius: 4px; font-weight: bold; margin-left: 10px;
        display: inline-block;
    }
    .remark-box {
        background-color: #ffffff; padding: 15px; border-radius: 6px;
        border: 1px solid #e2e8f0; margin-top: 8px; margin-bottom: 8px;
    }
    .remark-line {
        font-size: 20px !important; line-height: 1.6; color: #1e293b;
        font-weight: 500; margin-bottom: 12px; white-space: pre-wrap;
    }
    .remark-header { font-size: 14px !important; color: #0284c7; font-weight: bold; margin-top: 6px; }
    .collapsed-header { font-size: 14px !important; color: #64748b; font-weight: bold; margin-top: 6px; }
    .partner-title { font-size: 26px !important; font-weight: bold; color: #0f172a; }
    .footer-box {
        text-align: center; padding: 30px 0px 10px 0px; font-size: 14px;
        color: #64748b; font-weight: 500; border-top: 1px solid #e2e8f0; margin-top: 50px;
    }
    .streamlit-expanderHeader { background-color: #f1f5f9 !important; border-radius: 6px !important; }
    .stExpander:nth-of-type(1) .streamlit-expanderHeader p { font-size: 19px !important; font-weight: 800 !important; color: #0f172a !important; }
    .stExpander:nth-of-type(2) .streamlit-expanderHeader p { font-size: 15px !important; font-weight: 600 !important; color: #64748b !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚢 Carrier DG Prohibited List Query System")

if "search_submitted" not in st.session_state:
    st.session_state.search_submitted = False
if "last_query" not in st.session_state:
    st.session_state.last_query = None
if "history_list" not in st.session_state:
    st.session_state.history_list = []

def handle_search():
    cls_val = st.session_state.input_class_widget.strip()
    un_val = st.session_state.input_un_widget.strip()
    carrier_val = st.session_state.input_carrier_widget
    
    if cls_val or un_val:
        query_payload = {"class": cls_val, "un": un_val, "carrier": carrier_val}
        st.session_state.last_query = query_payload
        st.session_state.search_submitted = True
        
        history_display = f"UN {un_val}" if un_val else f"Class {cls_val}"
        if history_display not in [h["display"] for h in st.session_state.history_list]:
            st.session_state.history_list.insert(0, {"display": history_display, "data": query_payload})
            if len(st.session_state.history_list) > 10:
                st.session_state.history_list.pop()
    else:
        st.session_state.search_submitted = False
        st.session_state.last_query = None

    st.session_state.input_class_widget = ""
    st.session_state.input_un_widget = ""

def load_history_query(query_payload):
    st.session_state.last_query = query_payload
    st.session_state.search_submitted = True

# Data Cleaning Helpers
def clean_class_string(class_val):
    if pd.isna(class_val): return ""
    val_str = str(class_val).strip()
    if val_str.upper() == 'ALL': return 'ALL'
    if val_str.endswith('.0'): val_str = val_str[:-2]
    match = re.search(r'[0-9]+(?:\.[0-9]+)?', val_str)
    return match.group(0) if match else val_str

def is_class_matching(input_cls, target_cls, exact_mode=False):
    if not input_cls or not target_cls: return False
    input_cls = clean_class_string(input_cls)
    target_cls = clean_class_string(target_cls)
    if target_cls == 'ALL': return True
    if exact_mode: return input_cls == target_cls
    if input_cls.startswith('1') and target_cls.startswith('1'): return True
    if input_cls == target_cls: return True
    if '.' in input_cls and '.' not in target_cls:
        if input_cls.split('.')[0] == target_cls: return True
    if '.' not in input_cls and '.' in target_cls:
        if target_cls.split('.')[0] == input_cls: return True
    return False

def extract_subrisks_for_matching(subrisk_val):
    if pd.isna(subrisk_val): return []
    val_str = str(subrisk_val).strip()
    tokens = val_str.replace('/', ' ').replace(',', ' ').replace('、', ' ').split()
    cleaned_tokens = []
    for t in tokens:
        cleaned = clean_class_string(t)
        if cleaned: cleaned_tokens.append(cleaned)
        elif t.strip() == "P": cleaned_tokens.append("P")
    return cleaned_tokens

def format_subrisk_display(subrisk_val):
    if pd.isna(subrisk_val): return ""
    val_str = str(subrisk_val).strip()
    if val_str.lower() == 'nan' or val_str == "": return ""
    return re.sub(r'\bP\b', 'Marine Pollutant (MP)', val_str)

def format_un_number(un_val):
    if pd.isna(un_val): return ""
    if isinstance(un_val, float) and un_val.is_integer(): un_val = int(un_val)
    val_str = str(un_val).strip()
    if val_str.endswith('.0'): val_str = val_str[:-2]
    if val_str.upper() == 'ALL' or val_str == '': return 'ALL'
    if val_str.isdigit(): return val_str.zfill(4)
    digit_match = re.search(r'\d+', val_str)
    return digit_match.group(0).zfill(4) if digit_match else val_str

def parse_sheet_version(sheet_name):
    if '_' in sheet_name:
        parts = sheet_name.split('_', 1)
        return parts[0].upper(), f"Ver: {parts[1]}"
    return sheet_name.upper(), "Ver: 最新版"

# Main Logic UI Rendering
if excel_sheets is None:
    st.error("❌ CRITICAL ERROR: dg_list.xlsx not found!")
else:
    try:
        raw_sheets = [sheet for sheet in excel_sheets.keys() if not (sheet.startswith("Sheet") and excel_sheets[sheet].empty)]
        partner_display_map = {} 
        options_list = ["ALL CARRIERS"]
        
        for sheet in raw_sheets:
            carrier_name, ver_str = parse_sheet_version(sheet)
            display_label = f"{carrier_name}"
            partner_display_map[display_label] = sheet
            options_list.append(display_label)
        
        has_master = False
        if raw_master_df is not None:
            try:
                master_df = raw_master_df.copy()
                if 'UN Number' in master_df.columns or 'UN' in master_df.columns:
                    un_col = [c for c in master_df.columns if c.lower() in ['un number', 'un', 'un號碼']][0]
                    cls_col = [c for c in master_df.columns if any(k in c.lower() for k in ['class', 'division', '類別'])][0]
                    
                    master_df['UN Number'] = master_df[un_col].apply(format_un_number)
                    master_df['Class'] = master_df[cls_col].apply(clean_class_string)
                    
                    sub_risk_col_name = None
                    for col in master_df.columns:
                        if col.lower() in ['sub risk', 'subrisk', '次要風險', 'subsidiary risk']:
                            sub_risk_col_name = col
                            break
                    master_df['Detected_SubRisk'] = master_df[sub_risk_col_name] if sub_risk_col_name else ""
                    has_master = True
            except Exception as e:
                st.warning(f"⚠️ Warning: imdg_master.xlsx database failed to load. Error: {e}")

        with st.sidebar:
            st.markdown("### 🔍 Search Intelligence")
            st.markdown("#### 🕒 Quick Recall (Last 10)")
            if not st.session_state.history_list:
                st.caption("No recent searches.")
            else:
                for idx, item in enumerate(st.session_state.history_list):
                    st.button(label=f"{idx+1}. {item['display']}", key=f"recall_{idx}", on_click=load_history_query, args=(item['data'],), use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🧹 Clear History", use_container_width=True, type="secondary"):
                    st.session_state.history_list = []
                    st.rerun()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### 1. Enter Class / Division")
            user_input_class = st.text_input("Class Input", placeholder="e.g., 1, 2.3, 3", key="input_class_widget", label_visibility="collapsed")
        with col2:
            st.markdown("### 2. Enter UN Number")
            raw_input_un = st.text_input("UN Number Input", placeholder="e.g., 0005, 1950, 2430", key="input_un_widget", label_visibility="collapsed")
        with col3:
            st.markdown("### 3. Filter by Carrier")
            selected_display = st.selectbox("Partner Filter", options_list, key="input_carrier_widget", label_visibility="collapsed")

        st.button("Search Database", type="primary", use_container_width=True, on_click=handle_search)

        if st.session_state.search_submitted and st.session_state.last_query is not None:
            query_data = st.session_state.last_query
            final_class = clean_class_string(query_data["class"]) if query_data["class"] else ""
            input_un = format_un_number(query_data["un"]) if query_data["un"] else ""
            if input_un == 'ALL': input_un = ""
            selected_display = query_data["carrier"]
            
            is_valid_input = True
            matched_master_records = []
            
            MULTI_CLASS_UNS = ["1950", "2037"]
            if input_un in MULTI_CLASS_UNS and not final_class:
                st.error(f"❌ INTERCEPT WARNING: UN {input_un} contains multiple regulatory classifications. You MUST enter 'Class' field!")
                is_valid_input = False
                
            if is_valid_input and not input_un and not final_class:
                st.warning("⚠️ Action Required: Please enter at least a UN Number or a Class/Division.")
                is_valid_input = False
                
            if is_valid_input and final_class and final_class != 'ALL':
                try:
                    class_num = float(clean_class_string(final_class))
                    if class_num < 1.0 or class_num >= 10.0:
                        st.error("❌ Input Error: Classes only range from 1 to 9.")
                        is_valid_input = False
                except ValueError:
                    st.error("⚠️ Invalid Format: Class parameters must be numeric numbers.")
                    is_valid_input = False

            if is_valid_input and input_un and has_master:
                un_exists = master_df[master_df['UN Number'] == input_un]
                if un_exists.empty:
                    st.error(f"❌ Regulatory Alert: UN {input_un} is NOT found in IMDG Code Master Database!")
                    
                    # 🌟 核心功能：帶有網頁前端狀態回報與 Chrome 標頭偽裝的表單發送區塊
                    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSc1caW7PBAtU3wtsQ_J6UoPOuJeFAKbyUfa3shMqCOSV7vLMQ/formResponse"
                    form_data = {
                        "entry.1445284603": st.session_state.get('user_email', 'Unknown_User'),  
                        "entry.520419811": input_un                                              
                    }
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    }
                    try:
                        res = requests.post(form_url, data=form_data, headers=headers, timeout=5)
                        if res.status_code == 200:
                            st.toast("ℹ️ 系統提示：缺失 UN 已成功同步至後台試算表！")
                        else:
                            st.error(f"⚠️ Google 表單傳送失敗，狀態碼：{res.status_code}（通常為表單權限阻擋）")
                    except Exception as e:
                        st.error(f"⚠️ 傳送過程發生網路異常：{e}")
                        
                    is_valid_input = False
                else:
                    unique_un_exists = un_exists.drop_duplicates(subset=['Class', 'Detected_SubRisk', 'PSN'])
                    for _, master_row in unique_un_exists.iterrows():
                        db_class = clean_class_string(master_row['Class'])
                        db_subrisk = str(master_row['Detected_SubRisk']).strip() if pd.notna(master_row['Detected_SubRisk']) else ""
                        db_psn = str(master_row['PSN']).strip() if 'PSN' in master_row else ""
                        if not final_class or final_class == 'ALL' or is_class_matching(final_class, db_class):
                            matched_master_records.append({"class": db_class, "sub_risk": db_subrisk, "psn": db_psn})

            if is_valid_input and not input_un and final_class:
                matched_master_records.append({"class": final_class, "sub_risk": "", "psn": "Generic Category Search"})

            if is_valid_input and matched_master_records:
                st.markdown("---")
                for record in matched_master_records:
                    current_class = clean_class_string(record["class"])
                    raw_subrisk = record["sub_risk"]
                    current_psn = record["psn"]
                    
                    master_subrisk_list = extract_subrisks_for_matching(raw_subrisk)
                    display_subrisk_text = format_subrisk_display(raw_subrisk)
                    subrisk_display = f" (Sub Risk: {display_subrisk_text})" if display_subrisk_text else ""
                    
                    if input_un and current_psn:
                        st.markdown(f"""
                            <div class="psn-card">
                                <div style="font-size: 16px; opacity: 0.8; font-weight: bold; margin-bottom: 5px;">🌍 IMDG Code Regulatory Identification:</div>
                                <div style="font-size: 28px; font-weight: bold; line-height: 1.3;">UN {input_un} - {current_psn}</div>
                                <div style="font-size: 14px; opacity: 0.9; margin-top: 5px;">Official Classification: Class {current_class}{subrisk_display}</div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    search_targets = [(sheet, sheet) for sheet in raw_sheets] if selected_display == "ALL CARRIERS" else [(partner_display_map[selected_display], selected_display)]
                    
                    green_bucket, yellow_bucket, red_bucket = [], [], []
                    
                    for sheet_name, display_label in search_targets:
                        carrier_clean_name, version_tag = parse_sheet_version(sheet_name)
                        df = excel_sheets[sheet_name].copy()
                        df.columns = df.columns.astype(str).str.strip()
                        
                        col_mapping = {}
                        for c in df.columns:
                            c_lower = c.lower().replace(" ", "").replace("/", "").replace("_", "")
                            if 'un' in c_lower: col_mapping['UN'] = c
                            if 'class' in c_lower or 'division' in c_lower or '類別' in c_lower: col_mapping['Class'] = c
                            if 'prohibit' in c_lower or '狀態' in c_lower or 'status' in c_lower: col_mapping['Prohibited'] = c
                            if 'remark' in c_lower and ('has' in c_lower or '狀態' in c_lower): col_mapping['HasRemark'] = c
                            if 'subrisk' in c_lower or '次要' in c_lower or 'subsidiary' in c_lower: col_mapping['SubRisk'] = c
                        
                        if 'UN' not in col_mapping or 'Class' not in col_mapping or 'Prohibited' not in col_mapping:
                            continue
                        
                        remark_cols = [c for c in df.columns if any(k in c.lower() for k in ['remark', '備註', '限制', '條件', '敘述'])]
                        df['Clean_UN'] = df[col_mapping['UN']].fillna('ALL').apply(format_un_number)
                        df['Clean_Class'] = df[col_mapping['Class']].apply(clean_class_string)
                        df['Clean_Prohibited'] = df[col_mapping['Prohibited']].fillna('').astype(str).str.strip().str.upper()
                        df['Clean_HasRemark'] = df[col_mapping['HasRemark']].fillna('').astype(str).str.strip().str.upper() if 'HasRemark' in col_mapping else ""
                        df['Clean_SubRisk'] = df[col_mapping['SubRisk']].fillna('').astype(str).str.strip().apply(clean_class_string) if 'SubRisk' in col_mapping else ""

                        carrier_matched_rows = []
                        specific_dg_list = []  
                        collapsed_list = []    

                        if input_un:
                            exact_matches = df[df['Clean_UN'] == input_un]
                            for _, row in exact_matches.iterrows():
                                carrier_cls = row['Clean_Class']
                                carrier_subrisk = row['Clean_SubRisk']
                                if carrier_cls and not is_class_matching(current_class, carrier_cls): continue
                                if carrier_subrisk and master_subrisk_list and carrier_subrisk not in master_subrisk_list: continue
                                carrier_matched_rows.append(row)
                                
                                if 'HasRemark' in col_mapping and str(row[col_mapping['HasRemark']]).strip():
                                    hr_val = str(row[col_mapping['HasRemark']]).strip()
                                    if hr_val and hr_val.lower() != 'nan' and hr_val.upper() not in ["YES", "TRUE"] and hr_val not in [c["text"] for c in specific_dg_list]:
                                        specific_dg_list.append({"col_name": "Has Remark", "text": hr_val})
                                
                                for r_col in remark_cols:
                                    if 'HasRemark' in col_mapping and r_col == col_mapping['HasRemark']: continue
                                    r_val = str(row[r_col]).strip()
                                    if r_val and r_val.lower() != 'nan' and r_val != '' and r_val not in [c["text"] for c in specific_dg_list]:
                                        specific_dg_list.append({"col_name": r_col, "text": r_val})

                        global_lines = df[(df['Clean_UN'] == '') | (df['Clean_UN'].str.upper() == 'ALL')]
                        universal_counter = 1
                        
                        for _, g_row in global_lines.iterrows():
                            carrier_restricted_cls = g_row['Clean_Class']
                            is_exact = True if (carrier_restricted_cls and carrier_restricted_cls != 'ALL') else False
                            main_class_hit = is_class_matching(current_class, carrier_restricted_cls, exact_mode=is_exact)
                            
                            sub_risk_hit = False
                            hit_subrisk_val = ""
                            if master_subrisk_list and carrier_restricted_cls:
                                for sr in master_subrisk_list:
                                    if sr != "P" and is_class_matching(sr, carrier_restricted_cls, exact_mode=is_exact):
                                        sub_risk_hit = True
                                        hit_subrisk_val = sr
                                        break
                            
                            if main_class_hit or sub_risk_hit:
                                carrier_matched_rows.append(g_row)
                                for r_col in remark_cols:
                                    r_val = str(g_row[r_col]).strip()
                                    if r_val and r_val.lower() != 'nan' and r_val != '':
                                        if carrier_restricted_cls == 'ALL':
                                            if r_val not in [c["text"] for c in collapsed_list]:
                                                collapsed_list.append({"col_name": "Universal DG Policy", "text": r_val, "num": universal_counter})
                                                universal_counter += 1
                                        else:
                                            label = f"Main Class {carrier_restricted_cls} Policy" if main_class_hit else f"Sub Risk '{hit_subrisk_val}' Restriction"
                                            if r_val not in [c["text"] for c in specific_dg_list]:
                                                specific_dg_list.append({"col_name": label, "text": r_val})

                        is_any_row_prohibited = False
                        is_any_row_remarked = False
                        if carrier_matched_rows:
                            for row in carrier_matched_rows:
                                p_text = str(row['Clean_Prohibited']).strip().upper()
                                r_text = str(row['Clean_HasRemark']).strip().upper()
                                if any(k in p_text for k in ["🔴", "禁收", "YES", "PROHIBITED"]): is_any_row_prohibited = True
                                if any(k in r_text for k in ["🟡", "YES", "TRUE"]): is_any_row_remarked = True

                        un_display = f"UN {input_un} (Class {current_class})" if input_un else f"Class {current_class} Universal Policy"
                        carrier_payload = {
                            "carrier_name": carrier_clean_name, "version_tag": version_tag, "un_display": un_display,
                            "specific_dg_list": specific_dg_list, "collapsed_list": collapsed_list, "carrier_matched_rows": carrier_matched_rows
                        }

                        if is_any_row_prohibited:
                            carrier_payload.update({"border_color": "#ef4444", "bg_badge": "#fee2e2", "text_badge": "#991b1b", "display_status": "🔴 Strictly Prohibited"})
                            red_bucket.append(carrier_payload)
                        elif is_any_row_remarked or specific_dg_list:
                            carrier_payload.update({"border_color": "#f59e0b", "bg_badge": "#fef3c7", "text_badge": "#92400e", "display_status": "🟡 Conditional Acceptance"})
                            yellow_bucket.append(carrier_payload)
                        else:
                            carrier_payload.update({"border_color": "#10b981", "bg_badge": "#d1fae5", "text_badge": "#065f46", "display_status": "🟢 Standard Acceptance"})
                            green_bucket.append(carrier_payload)

                    for target_bucket in [green_bucket, yellow_bucket, red_bucket]:
                        for item in target_bucket:
                            st.markdown(f"""
                                <div class="partner-card" style="border-left-color: {item['border_color']}; margin-bottom: 5px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span class="partner-title">
                                            🏢 Carrier: {item['carrier_name']} 
                                            <span class="version-badge">{item['version_tag']}</span>
                                            <div style="font-size: 13px; color: #64748b; font-weight: normal; margin-top: 4px;">Ref: {item['un_display']}</div>
                                        </span>
                                        <span class="status-badge" style="background-color: {item['bg_badge']}; color: {item['text_badge']};">{item['display_status']}</span>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)

                            if not item['carrier_matched_rows'] and not item['specific_dg_list']:
                                st.markdown('<div class="remark-box"><div class="remark-line">No specific booking restrictions found.</div></div>', unsafe_allow_html=True)
                            else:
                                if item['specific_dg_list']:
                                    with st.expander(f"📋 View Specific DG Remarks ({len(item['specific_dg_list'])} Items)", expanded=False):
                                        specific_html = "".join([f'<div class="remark-header">📌 [{rem["col_name"]}]</div><div class="remark-line">{rem["text"]}</div>' for rem in item['specific_dg_list']])
                                        st.markdown(f'<div class="remark-box" style="border-left: 4px solid #0284c7;">{specific_html}</div>', unsafe_allow_html=True)
                                if item['collapsed_list']:
                                    with st.expander(f"📄 View Global / Universal DG Policies ({len(item['collapsed_list'])} Items)", expanded=False):
                                        collapsed_html = "".join([f'<div class="collapsed-header">📌 {f"Universal DG Policy {rem['num']}. " if idx == 0 else f"{rem['num']}. "}</div><div class="remark-line">{rem["text"]}</div>' for idx, rem in enumerate(item['collapsed_list'])])
                                        st.markdown(f'<div class="remark-box">{collapsed_html}</div>', unsafe_allow_html=True)
                            st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("<br><br>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"❌ File reading failed. Error message: {e}")

# Footer
st.markdown("""
    <div class="footer-box">
        <div style="color: #e11d48; font-weight: bold; margin-bottom: 8px;">⚠️ INTERNAL USE ONLY – DO NOT DISTRIBUTE EXTERNALLY</div>
        <div>Copyright © 2026 IAL DG TEAM. All Rights Reserved.</div>
        <div style="font-size: 13px; color: #94a3b8;">Any issue contact <a href="mailto:tim.lee@interasialine.com" style="color: #38bdf8; text-decoration: none; font-weight: bold;">tim.lee@interasialine.com</a></div>
    </div>
    """, unsafe_allow_html=True)
