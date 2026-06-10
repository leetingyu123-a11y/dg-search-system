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
# ⚡ STREAMLIT CACHE DATA FUNCTIONS (快取加速)
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
# 🎨 CSS STYLING (視覺樣式優化)
# -------------------------------------------------------------
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
        border-radius: 5px; display: inline-block;
    }
    .remark-box {
        background-color: #ffffff; padding: 15px; border-radius: 6px;
        border: 1px solid #e2e8f0; margin-top: 8px; margin-bottom: 8px;
    }
    .remark-line {
        font-size: 20px !important; line-height: 1.6; color: #1e293b;
        font-weight: 500; margin-bottom: 12px; white-space: pre-wrap; 
    }
    .remark-header {
        font-size: 14px !important; color: #0284c7; font-weight: bold; margin-top: 6px;
    }
    .collapsed-header {
        font-size: 14px !important; color: #64748b; font-weight: bold; margin-top: 6px;
    }
    .partner-title {
        font-size: 26px !important; font-weight: bold; color: #0f172a;
    }
    .footer-box {
        text-align: center; padding: 30px 0px 10px 0px; font-size: 14px;
        color: #64748b; border-top: 1px solid #e2e8f0; margin-top: 50px;
    }
    
    /* 摺疊面板標題優化 */
    .stExpander .streamlit-expanderHeader p {
        margin-bottom: 0px !important;
    }
    .stExpander:nth-of-type(1) .streamlit-expanderHeader p {
        font-size: 19px !important; font-weight: 800 !important; color: #0f172a !important;
    }
    .stExpander:nth-of-type(2) .streamlit-expanderHeader p {
        font-size: 15px !important; font-weight: 600 !important; color: #64748b !important;
    }

    /* 🌟 歷史紀錄側邊欄：按鈕極小化 CSS */
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
if "input_un_value" not in st.session_state:
    st.session_state.input_un_value = ""
if "input_class_value" not in st.session_state:
    st.session_state.input_class_value = ""

def click_history(hist_un, hist_class):
    st.session_state.input_un_value = hist_un
    st.session_state.input_class_value = hist_class
    st.session_state.search_trigger = True

# 側邊欄改版：使用摺疊區收納歷史紀錄，使其不顯眼
with st.sidebar:
    st.subheader("⚙️ Settings")
    with st.expander("⏳ Recent Search History", expanded=False): # 預設關閉，更隱蔽
        if not st.session_state.history:
            st.caption("No history.")
        else:
            for idx, item in enumerate(st.session_state.history):
                lbl = f"UN{item['un']} [C{item['class']}]" if item['un'] else f"C{item['class']} (Glob)"
                st.button(lbl, key=f"h_{idx}", on_click=click_history, args=(item['un'], item['class']), use_container_width=True)
            if st.button("🗑️ Clear All", use_container_width=True):
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
    if exact_mode: return i_cls == t_cls
    if i_cls.startswith('1') and t_cls.startswith('1'): return True
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
            if any(k in master_df.columns for k in ['UN', 'Class']):
                un_col = [c for c in master_df.columns if c.lower() in ['un number', 'un']][0]
                cls_col = [c for c in master_df.columns if 'class' in c.lower() or '類別' in c.lower()][0]
                master_df['UN Number'] = master_df[un_col].apply(format_un_number)
                master_df['Class'] = master_df[cls_col].apply(clean_class_string)
                master_df['Detected_SubRisk'] = master_df[[c for c in master_df.columns if 'sub' in c.lower()][0]] if any('sub' in c.lower() for c in master_df.columns) else ""
                has_master = True

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### 1. Class")
            user_input_class = st.text_input("Class", value=st.session_state.input_class_value, placeholder="1, 3, etc", label_visibility="collapsed").strip()
        with col2:
            st.markdown("### 2. UN Number")
            raw_input_un = st.text_input("UN", value=st.session_state.input_un_value, placeholder="0066, 1950", label_visibility="collapsed").strip()
            input_un = format_un_number(raw_input_un) if raw_input_un else ""
        with col3:
            st.markdown("### 3. Carrier")
            selected_partner = st.selectbox("Carrier", ["ALL CARRIERS"] + all_partners, label_visibility="collapsed")

        if st.button("Search Database", type="primary", use_container_width=True) or st.session_state.search_trigger:
            st.session_state.search_trigger = False
            st.session_state.input_class_value = user_input_class
            st.session_state.input_un_value = raw_input_un
            
            final_class = clean_class_string(user_input_class) if user_input_class else ""
            is_valid_input = True
            matched_master_records = []
            
            # 驗證邏輯
            if input_un in ["1950", "2037"] and not final_class:
                st.error("❌ UN 1950/2037 requires Class Input.")
                is_valid_input = False
            elif not input_un and not final_class:
                st.warning("⚠️ Enter UN or Class.")
                is_valid_input = False

            if is_valid_input and input_un and has_master:
                un_exists = master_df[master_df['UN Number'] == input_un]
                if un_exists.empty:
                    st.error(f"❌ UN {input_un} not in Master DB.")
                    is_valid_input = False
                else:
                    unique_un = un_exists.drop_duplicates(subset=['Class', 'Detected_SubRisk'])
                    for _, m_row in unique_un.iterrows():
                        if not final_class or is_class_matching(final_class, m_row['Class']):
                            matched_master_records.append({"class": m_row['Class'], "sub_risk": m_row['Detected_SubRisk'], "psn": m_row.get('PSN','')})
                    if not matched_master_records:
                        st.error("❌ Mismatch Class/UN.")
                        is_valid_input = False

            if is_valid_input and not input_un:
                matched_master_records.append({"class": final_class, "sub_risk": "", "psn": "Generic Search"})

            if is_valid_input and matched_master_records:
                # 紀錄歷史
                log = {"un": input_un, "class": final_class}
                if log not in st.session_state.history:
                    st.session_state.history.insert(0, log)
                    st.session_state.history = st.session_state.history[:5]
                
                st.markdown("---")
                for rec in matched_master_records:
                    curr_cls = clean_class_string(rec["class"])
                    curr_psn = rec["psn"]
                    m_subrisk_list = extract_subrisks_for_matching(rec["sub_risk"])
                    
                    if input_un and curr_psn:
                        st.markdown(f'<div class="psn-card"><div style="font-size: 28px; font-weight: bold;">UN {input_un} - {curr_psn}</div><div>Class {curr_cls}</div></div>', unsafe_allow_html=True)
                    
                    search_targets = all_partners if selected_partner == "ALL CARRIERS" else [selected_partner]
                    
                    # 排序桶子
                    prohibited_bucket, remarked_bucket, standard_bucket = [], [], []

                    for sheet in search_targets:
                        df = excel_sheets[sheet].copy()
                        df.columns = df.columns.astype(str).str.strip()
                        cols = {('UN' if 'un' in c.lower() else 'Class' if 'class' in c.lower() else 'Prohibited' if 'prohibit' in c.lower() or 'status' in c.lower() else 'HasRemark' if 'has' in c.lower() else 'SubRisk' if 'sub' in c.lower() else ''): c for c in df.columns}
                        cols = {k: v for k, v in cols.items() if k}
                        
                        df['Clean_UN'] = df[cols['UN']].fillna('ALL').apply(format_un_number)
                        df['Clean_Class'] = df[cols['Class']].apply(clean_class_string)
                        df['Clean_Prohibited'] = df[cols['Prohibited']].fillna('').astype(str).str.upper()
                        
                        matched_rows = []
                        spec_rem, glob_rem = [], []

                        # 1. Exact UN
                        if input_un:
                            for _, r in df[df['Clean_UN'] == input_un].iterrows():
                                if is_class_matching(curr_cls, r['Clean_Class']): matched_rows.append(r)
                        
                        # 2. Global Policy
                        u_count = 1
                        for _, gr in df[(df['Clean_UN'] == '') | (df['Clean_UN'] == 'ALL')].iterrows():
                            is_ex = (gr['Clean_Class'] and gr['Clean_Class'] != 'ALL')
                            if is_class_matching(curr_cls, gr['Clean_Class'], exact_mode=is_ex):
                                matched_rows.append(gr)
                                for cname in [c for c in df.columns if any(k in c.lower() for k in ['remark', '備註', '限制'])]:
                                    val = str(gr[cname]).strip()
                                    if val and val.lower()!='nan' and val!='':
                                        if gr['Clean_Class'] == 'ALL':
                                            glob_rem.append({"num": u_count, "text": val}); u_count += 1
                                        else:
                                            spec_rem.append({"col_name": f"Class {gr['Clean_Class']} Policy", "text": val})

                        # 重新掃描特定備註 (針對 Exact UN)
                        if input_un:
                            for _, r in df[df['Clean_UN'] == input_un].iterrows():
                                if is_class_matching(curr_cls, r['Clean_Class']):
                                    for cname in [c for c in df.columns if any(k in c.lower() for k in ['remark', '備註', '限制'])]:
                                        val = str(r[cname]).strip()
                                        if val and val.lower()!='nan' and val.upper() not in ["YES","TRUE"]:
                                            spec_rem.append({"col_name": cname, "text": val})

                        # 燈號判定
                        is_pro = any(any(k in str(r['Clean_Prohibited']) for k in ["🔴", "禁收", "YES", "PROHIBITED"]) for r in matched_rows)
                        p_data = {"name": sheet, "spec": spec_rem, "glob": glob_rem, "has_match": len(matched_rows)>0}
                        
                        if is_pro: prohibited_bucket.append(p_data)
                        elif spec_rem: remarked_bucket.append(p_data)
                        else: standard_bucket.append(p_data)

                    # 🌟 渲染順序：綠 -> 黃 -> 紅
                    final_render = [("🟢 Standard", standard_bucket, "#10b981", "#d1fae5", "#065f46"), 
                                    ("🟡 Conditional", remarked_bucket, "#f59e0b", "#fef3c7", "#92400e"), 
                                    ("🔴 Prohibited", prohibited_bucket, "#ef4444", "#fee2e2", "#991b1b")]
                    
                    for label, bucket, bcolor, bgcolor, tcolor in final_render:
                        for item in bucket:
                            st.markdown(f'<div class="partner-card" style="border-left-color: {bcolor};"><div style="display: flex; justify-content: space-between; align-items: center;"><span class="partner-title">🏢 {item["name"]}</span><span class="status-badge" style="background-color: {bgcolor}; color: {tcolor};">{label}</span></div></div>', unsafe_allow_html=True)
                            if item["spec"]:
                                with st.expander(f"📋 Specific Remarks ({len(item['spec'])})"):
                                    st.markdown(f'<div class="remark-box" style="border-left: 4px solid #0284c7;">' + "".join([f'<div class="remark-header">📌 [{s["col_name"]}]</div><div class="remark-line">{s["text"]}</div>' for s in item["spec"]]) + '</div>', unsafe_allow_html=True)
                            if item["glob"]:
                                with st.expander(f"📄 Global Policies ({len(item['glob'])})"):
                                    html = ""
                                    for idx, g in enumerate(item["glob"]):
                                        header = f"Universal DG Policy {g['num']}." if idx==0 else f"{g['num']}."
                                        html += f'<div class="collapsed-header">📌 {header}</div><div class="remark-line">{g["text"]}</div>'
                                    st.markdown(f'<div class="remark-box">{html}</div>', unsafe_allow_html=True)
                            if not item["has_match"]:
                                st.caption("No specific matching rules found.")
                    st.markdown("<br>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error: {e}")

st.markdown('<div class="footer-box">⚠️ INTERNAL USE ONLY | Copyright © 2026 IAL DG TEAM</div>', unsafe_allow_html=True)
