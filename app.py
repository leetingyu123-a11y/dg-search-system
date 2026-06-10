import streamlit as st
import pandas as pd
import os
import re

# Set page title and wide layout
st.set_page_config(page_title="Carrier DG Prohibited List Query System", layout="wide")

# Define file paths
excel_file = "dg_list.xlsx"
if not os.path.exists(excel_file):
    excel_file = os.path.join("DG_System", "dg_list.xlsx")

master_file = "imdg_master.xlsx"
if not os.path.exists(master_file):
    master_file = os.path.join("DG_System", "imdg_master.xlsx")

# -------------------------------------------------------------
# ⚡ STREAMLIT CACHE DATA FUNCTIONS (雲端環境優化版快取)
# -------------------------------------------------------------
@st.cache_data
def load_carrier_excel(file_path, file_timestamp):
    """讀取並載入船東 DG 限制清單 (dg_list.xlsx)"""
    if os.path.exists(file_path):
        return pd.read_excel(file_path, sheet_name=None)
    return None

@st.cache_data
def load_imdg_master(file_path, file_timestamp):
    """讀取並載入官方 IMDG Master 數據庫 (imdg_master.xlsx)"""
    if os.path.exists(file_path):
        df = pd.read_excel(file_path, dtype=str)
        df.columns = df.columns.astype(str).str.strip()
        return df
    return None

excel_time = os.path.getmtime(excel_file) if os.path.exists(excel_file) else 0
master_time = os.path.getmtime(master_file) if os.path.exists(master_file) else 0

excel_sheets = load_carrier_excel(excel_file, excel_time)
raw_master_df = load_imdg_master(master_file, master_time)
# -------------------------------------------------------------

st.markdown("""
    <style>
    .psn-card {
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        background: linear-gradient(135deg, #1e3a8a, #3b82f6);
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .partner-card {
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 15px;
        border-left: 8px solid #cbd5e1;
        background-color: #f8fafc;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .status-badge {
        font-size: 20px !important;
        font-weight: bold;
        padding: 4px 12px;
        border-radius: 5px;
        display: inline-block;
        margin-bottom: 0px;
    }
    .remark-box {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 6px;
        border: 1px solid #e2e8f0;
        margin-top: 8px;
        margin-bottom: 8px;
    }
    .remark-line {
        font-size: 20px !important; 
        line-height: 1.6;
        color: #1e293b;
        font-weight: 500;
        margin-bottom: 12px;
        white-space: pre-wrap; 
    }
    .remark-header {
        font-size: 14px !important;
        color: #0284c7;
        font-weight: bold;
        margin-top: 6px;
    }
    .collapsed-header {
        font-size: 14px !important;
        color: #64748b;
        font-weight: bold;
        margin-top: 6px;
    }
    .partner-title {
        font-size: 26px !important;
        font-weight: bold;
        color: #0f172a;
    }
    .footer-box {
        text-align: center;
        padding: 30px 0px 10px 0px;
        font-size: 14px;
        color: #64748b;
        font-weight: 500;
        border-top: 1px solid #e2e8f0;
        margin-top: 50px;
    }
    
    .streamlit-expanderHeader {
        background-color: #f1f5f9 !important;
        border-radius: 6px !important;
    }

    .stExpander:nth-of-type(1) .streamlit-expanderHeader p {
        font-size: 19px !important;       
        font-weight: 800 !important;       
        color: #0f172a !important;         
    }

    .stExpander:nth-of-type(2) .streamlit-expanderHeader p {
        font-size: 15px !important;       
        font-weight: 600 !important;       
        color: #64748b !important;         
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🚢 Carrier DG Prohibited List Query System")

# -------------------------------------------------------------
# 🔄 處理「搜尋後輸入框自動清空」的核心機制
# -------------------------------------------------------------
if "search_submitted" not in st.session_state:
    st.session_state.search_submitted = False
if "last_query" not in st.session_state:
    st.session_state.last_query = None

# 當按下搜尋按鈕時触发的 CallBack
def handle_search():
    # 先把當前輸入框的值撈出來存入暫存區
    cls_val = st.session_state.input_class_widget.strip()
    un_val = st.session_state.input_un_widget.strip()
    carrier_val = st.session_state.input_carrier_widget
    
    if cls_val or un_val:
        st.session_state.last_query = {
            "class": cls_val,
            "un": un_val,
            "carrier": carrier_val
        }
        st.session_state.search_submitted = True
    else:
        st.session_state.search_submitted = False
        st.session_state.last_query = None

    # 清空輸入框的 Widget State
    st.session_state.input_class_widget = ""
    st.session_state.input_un_widget = ""

# -------------------------------------------------------------

def clean_class_string(class_val):
    if pd.isna(class_val):
        return ""
    val_str = str(class_val).strip()
    if val_str.upper() == 'ALL':
        return 'ALL'
    if val_str.endswith('.0'):
        val_str = val_str[:-2]
    match = re.search(r'[0-9]+(?:\.[0-9]+)?', val_str)
    return match.group(0) if match else val_str

def is_class_matching(input_cls, target_cls, exact_mode=False):
    if not input_cls or not target_cls:
        return False
    input_cls = clean_class_string(input_cls)
    target_cls = clean_class_string(target_cls)
    
    if target_cls == 'ALL':
        return True
        
    if exact_mode:
        return input_cls == target_cls

    if input_cls.startswith('1') and target_cls.startswith('1'):
        return True
    if input_cls == target_cls:
        return True
    if '.' in input_cls and '.' not in target_cls:
        if input_cls.split('.')[0] == target_cls:
            return True
    if '.' not in input_cls and '.' in target_cls:
        if target_cls.split('.')[0] == input_cls:
            return True
    return False

def extract_subrisks_for_matching(subrisk_val):
    if pd.isna(subrisk_val):
        return []
    val_str = str(subrisk_val).strip()
    tokens = val_str.replace('/', ' ').replace(',', ' ').replace('、', ' ').split()
    cleaned_tokens = []
    for t in tokens:
        cleaned = clean_class_string(t)
        if cleaned:
            cleaned_tokens.append(cleaned)
        elif t.strip() == "P":
            cleaned_tokens.append("P")
    return cleaned_tokens

def format_subrisk_display(subrisk_val):
    if pd.isna(subrisk_val):
        return ""
    val_str = str(subrisk_val).strip()
    if val_str.lower() == 'nan' or val_str == "":
        return ""
    formatted = re.sub(r'\bP\b', 'Marine Pollutant (MP)', val_str)
    return formatted

def format_un_number(un_val):
    if pd.isna(un_val):
        return ""
    if isinstance(un_val, float):
        if un_val.is_integer():
            un_val = int(un_val)
    val_str = str(un_val).strip()
    if val_str.endswith('.0'):
        val_str = val_str[:-2]
    if val_str.upper() == 'ALL' or val_str == '':
        return 'ALL'
    if val_str.isdigit():
        return val_str.zfill(4)
    digit_match = re.search(r'\d+', val_str)
    if digit_match:
        return digit_match.group(0).zfill(4)
    return val_str

if excel_sheets is None:
    st.error("❌ CRITICAL ERROR: dg_list.xlsx not found!")
else:
    try:
        all_partners = [sheet for sheet in excel_sheets.keys() if not (sheet.startswith("Sheet") and excel_sheets[sheet].empty)]
        
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
                    
                    if sub_risk_col_name:
                        master_df['Detected_SubRisk'] = master_df[sub_risk_col_name]
                    else:
                        master_df['Detected_SubRisk'] = ""
                        
                    has_master = True
            except Exception as e:
                st.warning(f"⚠️ Warning: imdg_master.xlsx database failed to load. Error: {e}")

        # Interface Layout (輸入框預設永遠是空白)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### 1. Enter Class / Division")
            user_input_class = st.text_input("Class Input", placeholder="e.g., 1, 2.3, 3", key="input_class_widget", label_visibility="collapsed")
        with col2:
            st.markdown("### 2. Enter UN Number")
            raw_input_un = st.text_input("UN Number Input", placeholder="e.g., 0005, 1950, 2430", key="input_un_widget", label_visibility="collapsed")
        with col3:
            st.markdown("### 3. Filter by Carrier")
            partner_options = ["ALL CARRIERS"] + all_partners
            selected_partner = st.selectbox("Partner Filter", partner_options, key="input_carrier_widget", label_visibility="collapsed")

        # 點擊按鈕直接觸發 handle_search 清空輸入框
        st.button("Search Database", type="primary", use_container_width=True, on_click=handle_search)

        # -------------------------------------------------------------
        # 📊 執行搜尋與渲染邏輯 (從暫存區讀取上一次提交的資料)
        # -------------------------------------------------------------
        if st.session_state.search_submitted and st.session_state.last_query is not None:
            query_data = st.session_state.last_query
            
            final_class = clean_class_string(query_data["class"]) if query_data["class"] else ""
            input_un = format_un_number(query_data["un"]) if query_data["un"] else ""
            if input_un == 'ALL': 
                input_un = ""
            selected_partner = query_data["carrier"]
            
            is_valid_input = True
            matched_master_records = []
            
            MULTI_CLASS_UNS = ["1950", "2037"]
            
            if input_un in MULTI_CLASS_UNS and not final_class:
                st.error(f"❌ INTERCEPT WARNING: UN {input_un} contains multiple regulatory classifications (e.g., 2.1/2.2/2.3). You MUST enter the 'Class / Division' field to perform this search!")
                is_valid_input = False
                
            if is_valid_input and not input_un and not final_class:
                st.warning("⚠️ Action Required: Please enter at least a UN Number or a Class/Division to perform search.")
                is_valid_input = False
                
            if is_valid_input and final_class and final_class != 'ALL':
                cleaned_num_str = clean_class_string(final_class)
                try:
                    class_num = float(cleaned_num_str)
                    if class_num < 1.0 or class_num >= 10.0:
                        st.error("❌ Input Error: IMDG Code Dangerous Goods Classes only range from 1 to 9.")
                        is_valid_input = False
                except ValueError:
                    st.error("⚠️ Invalid Format: Class parameters must be numeric numbers.")
                    is_valid_input = False

            if is_valid_input and input_un and has_master:
                un_exists = master_df[master_df['UN Number'] == input_un]
                if un_exists.empty:
                    st.error(f"❌ Regulatory Alert: UN {input_un} is NOT found in the official IMDG Code Master Database!")
                    is_valid_input = False
                else:
                    unique_un_exists = un_exists.drop_duplicates(subset=['Class', 'Detected_SubRisk', 'PSN'])
                    
                    for _, master_row in unique_un_exists.iterrows():
                        db_class = clean_class_string(master_row['Class'])
                        db_subrisk = str(master_row['Detected_SubRisk']).strip() if pd.notna(master_row['Detected_SubRisk']) else ""
                        db_psn = str(master_row['PSN']).strip() if 'PSN' in master_row else ""
                        
                        if not final_class or final_class == 'ALL':
                            matched_master_records.append({"class": db_class, "sub_risk": db_subrisk, "psn": db_psn})
                        else:
                            if is_class_matching(final_class, db_class):
                                matched_master_records.append({"class": db_class, "sub_risk": db_subrisk, "psn": db_psn})
                    
                    if not matched_master_records and final_class and final_class != 'ALL':
                        clean_listed_classes = [clean_class_string(c) for c in un_exists['Class'].tolist()]
                        st.error(f"❌ Mismatch Warning: Official IMDG lists UN {input_un} under Class `{clean_listed_classes}`.")
                        is_valid_input = False
                    elif not final_class and len(matched_master_records) > 1:
                        st.info(f"💡 Multi-Category Alert: UN {input_un} contains {len(matched_master_records)} distinct regulatory classifications.")

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
                    
                    search_targets = all_partners if selected_partner == "ALL CARRIERS" else [selected_partner]
                    
                    # 建立三個獨立的桶子用來裝不同燈號的結果
                    green_bucket = []
                    yellow_bucket = []
                    red_bucket = []
                    
                    for sheet_name in search_targets:
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
                            st.error(f"⚠️ Sheet `{sheet_name}` structure error. Column resolution failed.")
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

                        # 1. Check Exact UN Matches First
                        if input_un:
                            exact_matches = df[df['Clean_UN'] == input_un]
                            for _, row in exact_matches.iterrows():
                                carrier_cls = row['Clean_Class']
                                carrier_subrisk = row['Clean_SubRisk']
                                
                                if carrier_cls and not is_class_matching(current_class, carrier_cls):
                                    continue
                                if carrier_subrisk and master_subrisk_list:
                                    if carrier_subrisk not in master_subrisk_list:
                                        continue
                                carrier_matched_rows.append(row)
                                
                                if 'HasRemark' in col_mapping and str(row[col_mapping['HasRemark']]).strip():
                                    hr_val = str(row[col_mapping['HasRemark']]).strip()
                                    if hr_val and hr_val.lower() != 'nan' and hr_val.upper() not in ["YES", "TRUE"] and hr_val not in [c["text"] for c in specific_dg_list]:
                                        specific_dg_list.append({"col_name": "Has Remark", "text": hr_val})
                                
                                for r_col in remark_cols:
                                    if 'HasRemark' in col_mapping and r_col == col_mapping['HasRemark']:
                                        continue
                                    r_val = str(row[r_col]).strip()
                                    if r_val and r_val.lower() != 'nan' and r_val != '':
                                        if r_val not in [c["text"] for c in specific_dg_list]:
                                            specific_dg_list.append({"col_name": r_col, "text": r_val})

                        # 2. Check Global Policy Rules
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
                                                collapsed_list.append({
                                                    "col_name": "Universal DG Policy",
                                                    "text": r_val,
                                                    "num": universal_counter
                                                })
                                                universal_counter += 1
                                        else:
                                            label = f"Main Class {carrier_restricted_cls} Policy" if main_class_hit else f"Sub Risk '{hit_subrisk_val}' Restriction"
                                            if r_val not in [c["text"] for c in specific_dg_list]:
                                                specific_dg_list.append({"col_name": label, "text": r_val})

                        # 3. 統計狀態（只看真正匹配成功的那些行）
                        is_any_row_prohibited = False
                        is_any_row_remarked = False
                        
                        if carrier_matched_rows:
                            for row in carrier_matched_rows:
                                p_text = str(row['Clean_Prohibited']).strip().upper()
                                r_text = str(row['Clean_HasRemark']).strip().upper()
                                if any(k in p_text for k in ["🔴", "禁收", "YES", "PROHIBITED"]):
                                    is_any_row_prohibited = True
                                if any(k in r_text for k in ["🟡", "YES", "TRUE"]):
                                    is_any_row_remarked = True

                        # 打包該船東的渲染資料
                        un_display = f"UN {input_un} (Class {current_class})" if input_un else f"Class {current_class} Universal Policy"
                        carrier_payload = {
                            "sheet_name": sheet_name,
                            "un_display": un_display,
                            "specific_dg_list": specific_dg_list,
                            "collapsed_list": collapsed_list,
                            "carrier_matched_rows": carrier_matched_rows
                        }

                        # 根據核心規則，將資料分流到各自的燈號桶子裡
                        if is_any_row_prohibited:
                            carrier_payload.update({"border_color": "#ef4444", "bg_badge": "#fee2e2", "text_badge": "#991b1b", "display_status": "🔴 Strictly Prohibited"})
                            red_bucket.append(carrier_payload)
                        elif is_any_row_remarked or specific_dg_list:
                            carrier_payload.update({"border_color": "#f59e0b", "bg_badge": "#fef3c7", "text_badge": "#92400e", "display_status": "🟡 Conditional Acceptance / Review Remarks"})
                            yellow_bucket.append(carrier_payload)
                        else:
                            carrier_payload.update({"border_color": "#10b981", "bg_badge": "#d1fae5", "text_badge": "#065f46", "display_status": "🟢 Standard Acceptance"})
                            green_bucket.append(carrier_payload)

                    # 🌟 核心修改：依序從 綠燈 -> 黃燈 -> 紅燈 進行畫面渲染
                    for target_bucket in [green_bucket, yellow_bucket, red_bucket]:
                        for item in target_bucket:
                            st.markdown(f"""
                                <div class="partner-card" style="border-left-color: {item['border_color']}; margin-bottom: 5px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span class="partner-title">🏢 Carrier: {item['sheet_name']} (Ref: {item['un_display']})</span>
                                        <span class="status-badge" style="background-color: {item['bg_badge']}; color: {item['text_badge']};">{item['display_status']}</span>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)

                            if not item['carrier_matched_rows'] and not item['specific_dg_list']:
                                st.markdown('<div class="remark-box"><div class="remark-line">No specific booking restrictions found for this category from this carrier.</div></div>', unsafe_allow_html=True)
                            else:
                                # 📂 摺疊 1：專屬特定 DG 項目
                                if item['specific_dg_list']:
                                    specific_label = f"📋 View Specific DG Remarks ({len(item['specific_dg_list'])} Items)"
                                    with st.expander(specific_label, expanded=False):
                                        specific_html = "".join([f'<div class="remark-header">📌 [{rem["col_name"]}]</div><div class="remark-line">{rem["text"]}</div>' for rem in item['specific_dg_list']])
                                        st.markdown(f'<div class="remark-box" style="border-left: 4px solid #0284c7;">{specific_html}</div>', unsafe_allow_html=True)
                                
                                # 📂 摺疊 2：通用通則
                                if item['collapsed_list']:
                                    expander_label = f"📄 View Global / Universal DG Policies ({len(item['collapsed_list'])} Items)"
                                    with st.expander(expander_label, expanded=False):
                                        collapsed_html = ""
                                        for idx, rem in enumerate(item['collapsed_list']):
                                            header_label = f"Universal DG Policy {rem['num']}." if idx == 0 else f"{rem['num']}."
                                            collapsed_html += f'<div class="collapsed-header">📌 {header_label}</div><div class="remark-line">{rem["text"]}</div>'
                                        st.markdown(f'<div class="remark-box">{collapsed_html}</div>', unsafe_allow_html=True)
                                        
                                if not item['specific_dg_list'] and not item['collapsed_list']:
                                    st.markdown('<div class="remark-box"><div class="remark-line">Standard conditions apply.</div></div>', unsafe_allow_html=True)
                                        
                            st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("<br><br>", unsafe_allow_html=True)
                            
    except Exception as e:
        st.error(f"❌ File reading failed. Error message: {e}")

# ==============================================================================
# FOOTER SECTION: Copyright & Confidentiality Declaration
# ==============================================================================
st.markdown("""
    <div class="footer-box">
        <div style="color: #e11d48; font-weight: bold; margin-bottom: 8px;">
            ⚠️ INTERNAL USE ONLY – DO NOT DISTRIBUTE EXTERNALLY
        </div>
        <div style="margin-bottom: 5px;">
            Copyright © 2026 IAL DG TEAM. All Rights Reserved.
        </div>
        <div style="font-size: 13px; color: #94a3b8;">
            Any issue and user feedback plz contact <a href="mailto:tim.lee@interasialine.com" style="color: #38bdf8; text-decoration: none; font-weight: bold;">tim.lee@interasialine.com</a> via Teams
        </div>
    </div>
    """, unsafe_allow_html=True)
