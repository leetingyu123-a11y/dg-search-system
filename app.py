import streamlit as st
import pandas as pd
import os
import re
import unicodedata

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
# ⚡ STREAMLIT CACHE DATA FUNCTIONS
# -------------------------------------------------------------
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

# -------------------------------------------------------------
# 🎨 CSS STYLING
# -------------------------------------------------------------
st.markdown("""
    <style>
    .psn-card {
        padding: 15px; border-radius: 8px; margin-bottom: 15px;
        background: linear-gradient(135deg, #1e3a8a, #3b82f6); color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .partner-card {
        padding: 15px; border-radius: 8px; margin-bottom: 10px;
        border-left: 8px solid #cbd5e1; background-color: #f8fafc;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .status-badge {
        font-size: 16px !important; font-weight: bold; padding: 3px 10px;
        border-radius: 5px; display: inline-block;
    }
    .remark-box {
        background-color: #ffffff; padding: 15px; border-radius: 6px;
        border: 1px solid #e2e8f0; margin-top: 5px; margin-bottom: 5px;
    }
    .remark-line {
        font-size: 18px !important; line-height: 1.5; color: #1e293b;
        font-weight: 500; margin-bottom: 10px; white-space: pre-wrap; 
    }
    .remark-header {
        font-size: 13px !important; color: #0284c7; font-weight: bold; margin-top: 4px;
    }
    .collapsed-header {
        font-size: 13px !important; color: #64748b; font-weight: bold; margin-top: 4px;
    }
    .partner-title {
        font-size: 22px !important; font-weight: bold; color: #0f172a;
    }
    .footer-box {
        text-align: center; padding: 20px 0px 10px 0px; font-size: 13px;
        color: #64748b; border-top: 1px solid #e2e8f0; margin-top: 40px;
    }
    
    .stExpander .streamlit-expanderHeader p { margin-bottom: 0px !important; }
    .stExpander:nth-of-type(1) .streamlit-expanderHeader p { font-size: 16px !important; font-weight: 800 !important; color: #0f172a !important; }
    .stExpander:nth-of-type(2) .streamlit-expanderHeader p { font-size: 14px !important; font-weight: 600 !important; color: #64748b !important; }

    .search-label {
        font-size: 13px !important;
        font-weight: 600;
        color: #94a3b8;
        margin-bottom: 4px !important;
        margin-top: 5px !important;
    }
    
    div[data-testid="stTextInput"] input {
        padding: 4px 10px !important;
        height: 36px !important;
        font-size: 14px !important;
    }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] {
        padding: 0px !important;
        height: 36px !important;
        font-size: 14px !important;
    }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        min-height: 36px !important;
        height: 36px !important;
    }
    
    div.stButton > button {
        padding: 4px 15px !important;
        height: 36px !important;
        font-size: 14px !important;
        margin-top: 28px !important;
    }

    [data-testid="stSidebar"] .stButton button {
        padding: 2px 8px !important;
        min-height: 24px !important;
        height: 24px !important;
        font-size: 12px !important;
        margin-bottom: 2px !important;
        border-radius: 4px !important;
        background-color: #f1f5f9 !important;
        color: #475569 !important;
        border: 1px solid #e2e8f0 !important;
        line-height: 1.2 !important;
        margin-top: 0px !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🚢 Carrier DG Prohibited List Query System")

# -------------------------------------------------------------
# ⏳ SESSION STATE & HISTORY LOGIC
# -------------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []
if "search_trigger" not in st.session_state:
    st.session_state.search_trigger = False

# 儲存當前正在展示的搜尋結果
if "current_search" not in st.session_state:
    st.session_state.current_search = None

# 綁定輸入框的 State
if "widget_class" not in st.session_state:
    st.session_state.widget_class = ""
if "widget_un" not in st.session_state:
    st.session_state.widget_un = ""

def click_history(hist_un, hist_class):
    st.session_state.widget_class = hist_class
    st.session_state.widget_un = hist_un
    st.session_state.search_trigger = True

with st.sidebar:
    st.subheader("⚙️ Settings")
    with st.expander("⏳ Recent Search History", expanded=False):
        if not st.session_state.history:
            st.caption("No history.")
        else:
            for idx, item in enumerate(st.session_state.history):
                lbl = f"UN{item['un']} [C{item['class']}]" if item['un'] else f"C{item['class']} (Glob)"
                st.button(lbl, key=f"h_{idx}", on_click=click_history, args=(item['un'], item['class']), use_container_width=True)
            if st.button("🗑️ Clear All History", use_container_width=True):
                st.session_state.history = []
                st.rerun()

# -------------------------------------------------------------
# 🧼 CLEANING & MATCHING FUNCTIONS
# -------------------------------------------------------------
def clean_class_string(class_val):
    if pd.isna(class_val): return ""
    val_str = unicodedata.normalize('NFKC', str(class_val)).strip().upper()
    if 'ALL' in val_str: return 'ALL'
    if val_str.endswith('.0'): val_str = val_str[:-2]
    match = re.search(r'[0-9]+(?:\.[0-9]+)?', val_str)
    return match.group(0) if match else val_str

def is_class_matching(input_cls, target_cls, exact_mode=False):
    if not input_cls or not target_cls: return False
    i_cls = clean_class_string(input_cls)
    t_cls = clean_class_string(target_cls)
    if t_cls == 'ALL': return True
    if i_cls.startswith('1') or t_cls.startswith('1'): return i_cls == t_cls
    if exact_mode: return i_cls == t_cls
    if i_cls == t_cls: return True
    if '.' in i_cls and '.' not in t_cls:
        if i_cls.split('.')[0] == t_cls: return True
    if '.' not in i_cls and '.' in t_cls:
        if t_cls.split('.')[0] == i_cls: return True
    return False

def extract_subrisks_for_matching(subrisk_val):
    if pd.isna(subrisk_val): return []
    val_str = str(subrisk_val).strip()
    tokens = val_str.replace('/', ' ').replace(',', ' ').replace('、', ' ').split()
    return [clean_class_string(t) for t in tokens if clean_class_string(t) or t.strip()=="P"]

def format_subrisk_display(subrisk_val):
    if pd.isna(subrisk_val): return ""
    val_str = str(subrisk_val).strip()
    return re.sub(r'\bP\b', 'Marine Pollutant (MP)', val_str) if val_str.lower()!='nan' else ""

def format_un_number(un_val):
    if pd.isna(un_val): return ""
    val_str = unicodedata.normalize('NFKC', str(un_val)).strip()
    if val_str.upper() == 'ALL' or val_str == '': return 'ALL'
    pure_digits = re.sub(r'[^0-9]', '', val_str)
    return pure_digits.zfill(4) if pure_digits else val_str

# -------------------------------------------------------------
# 🖥️ SEARCH INTERFACE
# -------------------------------------------------------------
if excel_sheets is None:
    st.error("❌ dg_list.xlsx not found!")
else:
    try:
        all_partners = [s for s in excel_sheets.keys() if not (s.startswith("Sheet") and excel_sheets[s].empty)]
        has_master = False
        if raw_master_df is not None:
            master_df = raw_master_df.copy()
            un_cols = [c for c in master_df.columns if c.lower() in ['un number', 'un', 'un號碼']]
            cls_cols = [c for c in master_df.columns if any(k in c.lower() for k in ['class', 'division', '類別'])]
            psn_cols = [c for c in master_df.columns if c.lower() in ['psn', 'proper shipping name', '品名']]
            
            if un_cols and cls_cols:
                un_col = un_cols[0]
                cls_col = cls_cols[0]
                psn_col = psn_cols[0] if psn_cols else None
                master_df['UN Number'] = master_df[un_col].apply(format_un_number)
                master_df['Class'] = master_df[cls_col].apply(clean_class_string)
                master_df['PSN_Clean'] = master_df[psn_col].fillna('') if psn_col else "Generic Category Search"
                sub_risk_col = [c for c in master_df.columns if 'sub' in c.lower() or '次要' in c.lower()]
                master_df['Detected_SubRisk'] = master_df[sub_risk_col[0]] if sub_risk_col else ""
                has_master = True

        # 版面重組：拿掉手動 Clear 鈕，讓搜尋按鈕放大填滿
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1.5])
        with col1:
            st.markdown('<p class="search-label">1. Class / Division</p>', unsafe_allow_html=True)
            user_input_class = st.text_input("Class", key="widget_class", placeholder="e.g., 3, 5.1", label_visibility="collapsed").strip()
        with col2:
            st.markdown('<p class="search-label">2. UN Number</p>', unsafe_allow_html=True)
            raw_input_un = st.text_input("UN", key="widget_un", placeholder="e.g., 1950, 2067", label_visibility="collapsed").strip()
        with col3:
            st.markdown('<p class="search-label">3. Carrier Filter</p>', unsafe_allow_html=True)
            selected_partner = st.selectbox("Carrier", ["ALL CARRIERS"] + all_partners, label_visibility="collapsed")
        with col4:
            search_pressed = st.button("Search Database", type="primary", use_container_width=True)

        # 🚀 核心邏輯：按下搜尋或觸發歷史紀錄時，立刻抽取數值並把輸入框洗空！
        if search_pressed or st.session_state.search_trigger:
            st.session_state.search_trigger = False
            
            # 抽取出要搜尋的參數
            search_class = user_input_class
            search_un = format_un_number(raw_input_un) if raw_input_un else ""
            
            # 💡 重點：立刻清空 Widget State，這樣在下一次渲染時輸入框就是乾淨空白的！
            st.session_state.widget_class = ""
            st.session_state.widget_un = ""
            
            # 將本次搜尋參數存進結果快取中，供下方渲染使用
            st.session_state.current_search = {
                "class": search_class,
                "un": search_un,
                "carrier": selected_partner
            }
            st.rerun() # 強制刷新，讓輸入框立刻清空，同時保留搜尋狀態

        # -------------------------------------------------------------
        # 📊 渲染展示邏輯 (從快取讀取當前搜尋結果)
        # -------------------------------------------------------------
        if st.session_state.current_search is not None:
            c_search = st.session_state.current_search
            final_class = clean_class_string(c_search["class"]) if c_search["class"] else ""
            input_un = c_search["un"]
            selected_partner = c_search["carrier"]
            
            is_valid_input = True
            matched_master_records = []
            
            if input_un in ["1950", "2037"] and not final_class:
                st.error("❌ INTERCEPT WARNING: UN 1950/2037 contains multiple classes. You MUST enter 'Class / Division'!")
                is_valid_input = False
            elif not input_un and not final_class:
                is_valid_input = False

            if is_valid_input and input_un and has_master:
                un_exists = master_df[master_df['UN Number'] == input_un]
                if un_exists.empty:
                    st.error(f"❌ Regulatory Alert: UN {input_un} is NOT found in IMDG master database.")
                    is_valid_input = False
                else:
                    unique_un = un_exists.drop_duplicates(subset=['Class', 'Detected_SubRisk'])
                    for _, m_row in unique_un.iterrows():
                        if not final_class or is_class_matching(final_class, m_row['Class']):
                            matched_master_records.append({
                                "class": m_row['Class'], 
                                "sub_risk": m_row['Detected_SubRisk'], 
                                "psn": m_row['PSN_Clean']
                            })
                    if not matched_master_records:
                        st.error(f"❌ Mismatch Warning: Official IMDG lists UN {input_un} under different Class.")
                        is_valid_input = False

            if is_valid_input and not input_un:
                matched_master_records.append({"class": final_class, "sub_risk": "", "psn": "Generic Category Search"})

            if is_valid_input and matched_master_records:
                # 寫入側邊欄歷史紀錄
                log = {"un": input_un, "class": final_class}
                if log not in st.session_state.history:
                    st.session_state.history.insert(0, log)
                    st.session_state.history = st.session_state.history[:5]
                
                st.markdown("---")
                for rec in matched_master_records:
                    curr_cls = clean_class_string(rec["class"])
                    curr_psn = rec["psn"]
                    m_subrisk_list = extract_subrisks_for_matching(rec["sub_risk"])
                    display_subrisk_text = format_subrisk_display(rec["sub_risk"])
                    subrisk_display = f" (Sub Risk: {display_subrisk_text})" if display_subrisk_text else ""
                    
                    if input_un and curr_psn:
                        st.markdown(f"""
                            <div class="psn-card">
                                <div style="font-size: 24px; font-weight: bold;">UN {input_un} - {curr_psn}</div>
                                <div style="font-size: 14px; opacity: 0.9;">Official Class: {curr_cls}{subrisk_display}</div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    search_targets = all_partners if selected_partner == "ALL CARRIERS" else [selected_partner]
                    
                    standard_bucket = []
                    remarked_bucket = []
                    prohibited_bucket = []

                    for sheet in search_targets:
                        df = excel_sheets[sheet].copy()
                        df.columns = df.columns.astype(str).str.strip()
                        
                        cols = {}
                        for c in df.columns:
                            c_lower = c.lower().replace(" ", "").replace("/", "").replace("_", "")
                            if 'un' in c_lower: cols['UN'] = c
                            if 'class' in c_lower or 'division' in c_lower or '類別' in c_lower: cols['Class'] = c
                            if 'prohibit' in c_lower or '狀態' in c_lower or 'status' in c_lower: cols['Prohibited'] = c
                            if 'remark' in c_lower and ('has' in c_lower or '狀態' in c_lower): cols['HasRemark'] = c
                            if 'subrisk' in c_lower or '次要' in c_lower or 'subsidiary' in c_lower: cols['SubRisk'] = c
                        
                        if 'UN' not in cols or 'Class' not in cols or 'Prohibited' not in cols:
                            continue
                        
                        remark_cols = [c for c in df.columns if any(k in c.lower() for k in ['remark', '備註', '限制', '條件'])]
                        
                        df['Clean_UN'] = df[cols['UN']].fillna('ALL').apply(format_un_number)
                        df['Clean_Class'] = df[cols['Class']].apply(clean_class_string)
                        df['Clean_Prohibited'] = df[cols['Prohibited']].fillna('').astype(str).str.strip().str.upper()
                        df['Clean_HasRemark'] = df[cols['HasRemark']].fillna('').astype(str).str.strip().str.upper() if 'HasRemark' in cols else ""
                        df['Clean_SubRisk'] = df[cols['SubRisk']].fillna('').astype(str).str.strip().apply(clean_class_string) if 'SubRisk' in cols else ""

                        carrier_matched_rows = []
                        specific_dg_list = []  
                        collapsed_list = []    

                        # 1. 精確 UN 規則
                        if input_un:
                            for _, row in df[df['Clean_UN'] == input_un].iterrows():
                                if row['Clean_Class'] and not is_class_matching(curr_cls, row['Clean_Class']): continue
                                if row['Clean_SubRisk'] and m_subrisk_list and row['Clean_SubRisk'] not in m_subrisk_list: continue
                                carrier_matched_rows.append(row)
                                
                                for r_col in remark_cols:
                                    r_val = str(row[r_col]).strip()
                                    if r_val and r_val.lower() != 'nan' and r_val != '' and r_val.upper() not in ["YES","TRUE"]:
                                        if r_val not in [s["text"] for s in specific_dg_list]:
                                            specific_dg_list.append({"col_name": str(r_col), "text": r_val})

                        # 2. 全域通則
                        global_lines = df[(df['Clean_UN'] == '') | (df['Clean_UN'] == 'ALL')]
                        universal_counter = 1
                        
                        for _, g_row in global_lines.iterrows():
                            c_res_cls = g_row['Clean_Class']
                            is_exact = True if (c_res_cls and c_res_cls != 'ALL') else False
                            
                            main_hit = is_class_matching(curr_cls, c_res_cls, exact_mode=is_exact)
                            sub_hit = False
                            if m_subrisk_list and c_res_cls:
                                for sr in m_subrisk_list:
                                    if sr != "P" and is_class_matching(sr, c_res_cls, exact_mode=is_exact):
                                        sub_hit = True; break
                            
                            if main_hit or sub_hit:
                                carrier_matched_rows.append(g_row)
                                for r_col in remark_cols:
                                    r_val = str(g_row[r_col]).strip()
                                    if r_val and r_val.lower() != 'nan' and r_val != '':
                                        if c_res_cls == 'ALL':
                                            if r_val not in [c["text"] for c in collapsed_list]:
                                                collapsed_list.append({"col_name": "Universal DG Policy", "text": r_val, "num": universal_counter})
                                                universal_counter += 1
                                        else:
                                            lbl = f"Class {c_res_cls} Policy" if main_hit else "Sub Risk Restriction"
                                            if r_val not in [s["text"] for s in specific_dg_list]:
                                                specific_dg_list.append({"col_name": lbl, "text": r_val})

                        is_any_row_prohibited = False
                        is_any_row_remarked = False
                        if carrier_matched_rows:
                            for r in carrier_matched_rows:
                                p_txt = str(r['Clean_Prohibited']).upper()
                                r_txt = str(r['Clean_HasRemark']).upper()
                                if any(k in p_txt for k in ["🔴", "禁收", "YES", "PROHIBITED"]): is_any_row_prohibited = True
                                if any(k in r_txt for k in ["🟡", "YES", "TRUE"]): is_any_row_remarked = True

                        partner_data = {
                            "sheet_name": sheet,
                            "carrier_matched_rows": carrier_matched_rows,
                            "specific_dg_list": specific_dg_list,
                            "collapsed_list": collapsed_list
                        }

                        if is_any_row_prohibited:
                            prohibited_bucket.append(partner_data)
                        elif is_any_row_remarked or specific_dg_list:
                            remarked_bucket.append(partner_data)
                        else:
                            standard_bucket.append(partner_data)

                    final_render_flow = [
                        ("standard", standard_bucket, "#10b981", "#d1fae5", "#065f46", "🟢 Standard Acceptance"),
                        ("remarked", remarked_bucket, "#f59e0b", "#fef3c7", "#92400e", "🟡 Conditional Acceptance / Review Remarks"),
                        ("prohibited", prohibited_bucket, "#ef4444", "#fee2e2", "#991b1b", "🔴 Strictly Prohibited")
                    ]

                    un_display = f"UN {input_un} (Class {curr_cls})" if input_un else f"Class {curr_cls} Universal Policy"
                    
                    for status_type, bucket, bcolor, bgcolor, tcolor, label_text in final_render_flow:
                        for item in bucket:
                            s_name = item["sheet_name"]
                            s_list = item["specific_dg_list"]
                            c_list = item["collapsed_list"]
                            m_rows = item["carrier_matched_rows"]

                            st.markdown(f"""
                                <div class="partner-card" style="border-left-color: {bcolor}; margin-bottom: 5px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span class="partner-title">🏢 Carrier: {s_name} (Ref: {un_display})</span>
                                        <span class="status-badge" style="background-color: {bgcolor}; color: {tcolor};">{label_text}</span>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)

                            if not m_rows and not s_list:
                                st.markdown('<div class="remark-box"><div class="remark-line">No specific booking restrictions found for this category from this carrier.</div></div>', unsafe_allow_html=True)
                            else:
                                if s_list:
                                    with st.expander(f"📋 View Specific DG Remarks ({len(s_list)} Items)", expanded=False):
                                        html = "".join([f'<div class="remark-header">📌 [{str(s["col_name"])}]</div><div class="remark-line">{str(s["text"])}</div>' for s in s_list])
                                        st.markdown(f'<div class="remark-box" style="border-left: 4px solid #0284c7;">{html}</div>', unsafe_allow_html=True)
                                if c_list:
                                    with st.expander(f"📄 View Global / Universal DG Policies ({len(c_list)} Items)", expanded=False):
                                        html = ""
                                        for idx, g in enumerate(c_list):
                                            hdr = f"Universal DG Policy {g['num']}." if idx == 0 else f"{g['num']}."
                                            html += f'<div class="collapsed-header">📌 {hdr}</div><div class="remark-line">{str(g["text"]).strip()}</div>'
                                        st.markdown(f'<div class="remark-box">{html}</div>', unsafe_allow_html=True)
                                        
                    st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("<br><br>", unsafe_allow_html=True)
                            
    except Exception as e:
        st.error(f"❌ Execution Bug Found. Error details: {e}")

# Footer (包含高亮信箱)
st.markdown('<div class="footer-box">⚠️ INTERNAL USE ONLY – DO NOT DISTRIBUTE EXTERNALLY<br>Copyright © 2026 IAL DG TEAM. All Rights Reserved <br>Any issue and user feedback plz contact <span style="background-color: #fef08a; color: #1e293b; padding: 2px 6px; border-radius: 4px; font-weight: bold;">tim.lee@interasialine.com</span> via teams.</div>', unsafe_allow_html=True)
