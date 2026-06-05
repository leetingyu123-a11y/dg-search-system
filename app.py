import streamlit as st
import pandas as pd
import os
import re

# Set page title and wide layout
st.set_page_config(page_title="Carrier DG Prohibited List Query System", layout="wide")

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
        margin-bottom: 10px;
    }
    .remark-box {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 6px;
        border: 1px solid #e2e8f0;
        margin-top: 8px;
    }
    .remark-line {
        font-size: 20px !important; 
        line-height: 1.6;
        color: #1e293b;
        font-weight: 500;
        margin-bottom: 8px;
        white-space: pre-wrap; 
    }
    .remark-header {
        font-size: 14px !important;
        color: #e11d48;
        font-weight: bold;
        margin-top: 4px;
    }
    .partner-title {
        font-size: 26px !important;
        font-weight: bold;
        color: #0f172a;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🚢 Carrier DG Prohibited List Query System")

# Define file paths
excel_file = "dg_list.xlsx"
if not os.path.exists(excel_file):
    excel_file = os.path.join("DG_System", "dg_list.xlsx")

master_file = "imdg_master.xlsx"
if not os.path.exists(master_file):
    master_file = os.path.join("DG_System", "imdg_master.xlsx")

# Clean Class strings (e.g., "Division 1.4" -> "1.4", "Class 3" -> "3")
def clean_class_string(class_val):
    if pd.isna(class_val):
        return ""
    val_str = str(class_val).strip()
    match = re.search(r'[0-9]+(?:\.[0-9]+)?', val_str)
    return match.group(0) if match else val_str

# Bi-directional Class family penetration algorithm
def is_class_matching(input_cls, target_cls):
    if not input_cls or not target_cls:
        return False
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

# High-efficiency zero-padding for UN Number
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
        return val_str
    if val_str.isdigit():
        return val_str.zfill(4)
    digit_match = re.search(r'\d+', val_str)
    if digit_match:
        return digit_match.group(0).zfill(4)
    return val_str

if not os.path.exists(excel_file):
    st.error("❌ CRITICAL ERROR: dg_list.xlsx not found! Please ensure the Excel file is correctly uploaded to GitHub.")
else:
    try:
        excel_sheets = pd.read_excel(excel_file, sheet_name=None)
        all_partners = [sheet for sheet in excel_sheets.keys() if not (sheet.startswith("Sheet") and excel_sheets[sheet].empty)]
        
        has_master = False
        if os.path.exists(master_file):
            try:
                master_df = pd.read_excel(master_file, dtype=str)
                master_df.columns = master_df.columns.astype(str).str.strip()
                if 'UN Number' in master_df.columns and 'Class' in master_df.columns:
                    master_df['UN Number'] = master_df['UN Number'].apply(format_un_number)
                    has_master = True
            except Exception as e:
                st.warning(f"⚠️ Warning: imdg_master.xlsx master database failed to load. Error: {e}")

        # Search Query Interface Layout
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### 1. Enter Class / Division (Optional)")
            user_input_class = st.text_input("Class Input", placeholder="e.g., 1, 2.3, 3", label_visibility="collapsed").strip()
        with col2:
            st.markdown("### 2. Enter UN Number (Optional)")
            raw_input_un = st.text_input("UN Number Input", placeholder="e.g., 0005, 3481", label_visibility="collapsed").strip()
            input_un = format_un_number(raw_input_un) if raw_input_un else ""
        with col3:
            st.markdown("### 3. Filter by Carrier (Optional)")
            partner_options = ["ALL CARRIERS"] + all_partners
            selected_partner = st.selectbox("Partner Filter", partner_options, label_visibility="collapsed")

        if st.button("Search Database", type="primary", use_container_width=True):
            final_class = user_input_class
            official_psn_en = ""
            is_valid_input = True
            
            if not input_un and not final_class:
                st.warning("⚠️ Action Required: Please enter at least a UN Number or a Class/Division to perform search.")
                is_valid_input = False
                
            if is_valid_input and input_un and has_master:
                un_exists = master_df[master_df['UN Number'] == input_un]
                if un_exists.empty:
                    st.error(f"❌ Regulatory Alert: UN {input_un} is NOT found in the official IMDG Code Master Database!")
                    is_valid_input = False
                else:
                    official_class_from_db = str(un_exists.iloc[0]['Class']).strip()
                    if 'PSN' in un_exists.columns:
                        official_psn_en = str(un_exists.iloc[0]['PSN']).strip()
                    if not final_class:
                        final_class = official_class_from_db
                        st.info(f"💡 System auto-identified Regulatory Category: Class `{final_class}`")
                    else:
                        clean_user_cls = clean_class_string(final_class)
                        official_classes_clean = [clean_class_string(c) for c in un_exists['Class'].tolist()]
                        class_match = any(is_class_matching(clean_user_cls, c) for c in official_classes_clean if c)
                        if not class_match:
                            st.error(f"❌ Mismatch Warning: Official IMDG lists UN {input_un} under Class `{un_exists['Class'].tolist()}`.")
                            st.error(f"🚨 Your input Class was `{user_input_class}`. Please double check regulatory data.")
                            is_valid_input = False

            clean_final_class = clean_class_string(final_class)

            if is_valid_input:
                st.markdown("---")
                if input_un and official_psn_en:
                    st.markdown(f"""
                        <div class="psn-card">
                            <div style="font-size: 16px; opacity: 0.8; font-weight: bold; margin-bottom: 5px;">🌍 IMDG Code Regulatory Identification:</div>
                            <div style="font-size: 28px; font-weight: bold; line-height: 1.3;">UN {input_un} - {official_psn_en}</div>
                            <div style="font-size: 14px; opacity: 0.9; margin-top: 5px;">Official Classification: Class {final_class}</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                search_targets = all_partners if selected_partner == "ALL CARRIERS" else [selected_partner]
                
                for sheet_name in search_targets:
                    df = excel_sheets[sheet_name]
                    df.columns = df.columns.astype(str).str.strip()
                    
                    col_mapping = {}
                    for c in df.columns:
                        if c in ['UN號碼', 'UN Number', 'UN Number ']: col_mapping['UN'] = c
                        if c in ['Class', 'Class ']: col_mapping['Class'] = c
                        if c in ['狀態', 'Prohibited', 'Prohibited ']: col_mapping['Status'] = c
                    
                    if 'UN' not in col_mapping or 'Class' not in col_mapping or 'Status' not in col_mapping:
                        st.error(f"⚠️ Sheet `{sheet_name}` format error. Must contain headers: [UN Number], [Class], and [Prohibited]")
                        continue
                    
                    remark_cols = [c for c in df.columns if any(k in c.lower() for k in ['remark', '備註', '限制', '條件', '敘述'])]
                    
                    df['Clean_UN'] = df[col_mapping['UN']].fillna('').apply(format_un_number)
                    df['Clean_Class'] = df[col_mapping['Class']].apply(clean_class_string)
                    df['Clean_Status'] = df[col_mapping['Status']].fillna('').astype(str).str.strip()

                    matched_rows = []
                    global_class_remarks = []
                    has_global_prohibited = False
                    global_prohibited_row = None

                    # 🧠 1. Scan for Global Class Rules (where UN Number is blank or 'ALL')
                    if clean_final_class:
                        global_rules = df[
                            ((df['Clean_UN'] == '') | (df['Clean_UN'].str.upper() == 'ALL')) & 
                            (df['Clean_Class'].apply(lambda x: is_class_matching(clean_final_class, x)))
                        ]
                        for _, g_row in global_rules.iterrows():
                            # If it's a wholesale ban (e.g., Prohibited = YES for the whole class)
                            if any(k in g_row['Clean_Status'].upper() for k in ["🔴", "禁收", "YES", "PROHIBITED"]):
                                has_global_prohibited = True
                                global_prohibited_row = g_row
                            
                            for r_col in remark_cols:
                                r_val = str(g_row[r_col]).strip()
                                if r_val and r_val.lower() != 'nan' and r_val != '':
                                    global_class_remarks.append({"col_name": f"General Policy ({g_row[col_mapping['Class']]})", "text": r_val})

                    # 🧠 2. Routing Logic based on User Input Type
                    if not input_un:
                        # 🚨 USER ONLY SEARCHED BY CLASS:
                        if has_global_prohibited:
                            # If the whole class is banned (like Class 2.3), just show that ONE global rule row!
                            matched_rows = [global_prohibited_row]
                        else:
                            # If there's no global ban row, but there are global remarks (like Class 3 flashpoint),
                            # keep matched_rows empty so it triggers the yellow conditional light, avoiding UN list explosion.
                            matched_rows = []
                    else:
                        # 🎯 USER SEARCHED BY SPECIFIC UN NUMBER:
                        # Show precise UN match if it exists, otherwise fall back to global ban if applicable
                        exact_match = df[df['Clean_UN'] == input_un]
                        if not exact_match.empty:
                            for _, row in exact_match.iterrows():
                                matched_rows.append(row)
                        elif has_global_prohibited:
                            matched_rows = [global_prohibited_row]

                    # --- 🎨 Render Card Output ---
                    if not matched_rows:
                        if global_class_remarks:
                            # Yellow light warning (Show only general class remarks, hide individual UNs)
                            st.markdown(f"""
                                <div class="partner-card" style="border-left-color: #f59e0b;">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span class="partner-title">🏢 Carrier: {sheet_name} (Class Ref: {user_input_class})</span>
                                        <span class="status-badge" style="background-color: #fef3c7; color: #92400e;">🟡 Conditional Acceptance</span>
                                    </div>
                                    <div style="margin-top: 10px;">
                                        <div style="font-weight: bold; color: #64748b; margin-bottom: 5px; font-size: 14px;">📝 General Class Rules Notice:</div>
                                        <div class="remark-box">
                                            {"".join([f'<div class="remark-header" style="color:#b45309;">⚠️ [{rem["col_name"]}]</div><div class="remark-line">{rem["text"]}</div>' for rem in global_class_remarks])}
                                        </div>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            # Safe Green Light
                            st.markdown(f"""
                                <div class="partner-card" style="border-left-color: #10b981;">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span class="partner-title">🏢 Carrier: {sheet_name} (UN Ref: {input_un if input_un else "Class " + user_input_class})</span>
                                        <span class="status-badge" style="background-color: #d1fae5; color: #065f46;">🟢 Standard Acceptance</span>
                                    </div>
                                    <div style="margin-top: 10px;">
                                        <div class="remark-box"><div class="remark-line">No specific booking restrictions found for this category from this carrier.</div></div>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        # Red light hit (Either specific UN hit, or optimized single-row Global Class Ban)
                        for row in matched_rows:
                            status_text = row['Clean_Status']
                            un_display = row['Clean_UN'] if row['Clean_UN'] != '' else f"Class {user_input_class} Universal Policy"
                            
                            if any(k in status_text.upper() for k in ["🔴", "禁收", "YES", "PROHIBITED"]):
                                border_color = "#ef4444"; bg_badge = "#fee2e2"; text_badge = "#991b1b"
                                display_status = "🔴 Strictly Prohibited"
                            else:
                                border_color = "#f59e0b"; bg_badge = "#fef3c7"; text_badge = "#92400e"
                                display_status = "🟡 Conditional Acceptance / Review Remarks"

                            collected_remarks = []
                            for r_col in remark_cols:
                                r_val = str(row[r_col]).strip()
                                if r_val and r_val.lower() != 'nan' and r_val != '':
                                    collected_remarks.append({"col_name": r_col, "text": r_val})

                            # Merge general class rules
                            combined_remarks = []
                            combined_remarks.extend(collected_remarks)
                            for g_rem in global_class_remarks:
                                if g_rem["text"] not in [c["text"] for c in combined_remarks]:
                                    combined_remarks.append(g_rem)

                            st.markdown(f"""
                                <div class="partner-card" style="border-left-color: {border_color};">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span class="partner-title">🏢 Carrier: {sheet_name} (Ref: {un_display})</span>
                                        <span class="status-badge" style="background-color: {bg_badge}; color: {text_badge};">{display_status}</span>
                                    </div>
                                    <div style="margin-top: 10px;">
                                        <div style="font-weight: bold; color: #64748b; margin-bottom: 5px; font-size: 14px;">📝 Comprehensive Carrier Remarks:</div>
                                        <div class="remark-box">
                                            {"".join([f'<div class="remark-header">📌 [{rem["col_name"]}]</div><div class="remark-line">{rem["text"]}</div>' for rem in combined_remarks]) if combined_remarks else '<div class="remark-line">Prohibited without additional conditions.</div>'}
                                        </div>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                            
    except Exception as e:
        st.error(f"❌ File reading failed. Error message: {e}")
