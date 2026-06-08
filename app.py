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
    .footer-box {
        text-align: center;
        padding: 30px 0px 10px 0px;
        font-size: 14px;
        color: #64748b;
        font-weight: 500;
        border-top: 1px solid #e2e8f0;
        margin-top: 50px;
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

def clean_class_string(class_val):
    if pd.isna(class_val):
        return ""
    val_str = str(class_val).strip()
    if val_str.endswith('.0'):
        val_str = val_str[:-2]
    match = re.search(r'[0-9]+(?:\.[0-9]+)?', val_str)
    return match.group(0) if match else val_str

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
    formatted = re.sub(r'\bP\b', '海汙 (Marine Pollutant)', val_str)
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
        return val_str
    if val_str.isdigit():
        return val_str.zfill(4)
    digit_match = re.search(r'\d+', val_str)
    if digit_match:
        return digit_match.group(0).zfill(4)
    return val_str

if not os.path.exists(excel_file):
    st.error("❌ CRITICAL ERROR: dg_list.xlsx not found!")
else:
    try:
        excel_sheets = pd.read_excel(excel_file, sheet_name=None)
        all_partners = [sheet for sheet in excel_sheets.keys() if not (sheet.startswith("Sheet") and excel_sheets[sheet].empty)]
        
        has_master = False
        if os.path.exists(master_file):
            try:
                master_df = pd.read_excel(master_file, dtype=str)
                master_df.columns = master_df.columns.astype(str).str.strip()
                if 'UN Number' in master_df.columns or 'UN' in master_df.columns:
                    un_col = [c for c in master_df.columns if c.lower() in ['un number', 'un', 'un號碼']][0]
                    cls_col = [c for c in master_df.columns if any(k in c.lower() for k in ['class', 'division', '類別'])][0]
                    
                    master_df['UN Number'] = master_df[un_col].apply(format_un_number)
                    master_df['Class'] = master_df[cls_col]
                    
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

        # Search Query Interface Layout
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### 1. Enter Class / Division")
            user_input_class = st.text_input("Class Input", placeholder="e.g., 1, 2.3, 3", label_visibility="collapsed").strip()
        with col2:
            st.markdown("### 2. Enter UN Number")
            raw_input_un = st.text_input("UN Number Input", placeholder="e.g., 0005, 1950, 2430", label_visibility="collapsed").strip()
            input_un = format_un_number(raw_input_un) if raw_input_un else ""
        with col3:
            st.markdown("### 3. Filter by Carrier ")
            partner_options = ["ALL CARRIERS"] + all_partners
            selected_partner = st.selectbox("Partner Filter", partner_options, label_visibility="collapsed")

        if st.button("Search Database", type="primary", use_container_width=True):
            final_class = user_input_class
            is_valid_input = True
            matched_master_records = []
            
            if not input_un and not final_class:
                st.warning("⚠️ Action Required: Please enter at least a UN Number or a Class/Division to perform search.")
                is_valid_input = False
                
            if is_valid_input and final_class:
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
                    for _, master_row in un_exists.iterrows():
                        db_class = str(master_row['Class']).strip()
                        db_subrisk = str(master_row['Detected_SubRisk']).strip() if pd.notna(master_row['Detected_SubRisk']) else ""
                        db_psn = str(master_row['PSN']).strip() if 'PSN' in master_row else ""
                        
                        if not final_class:
                            matched_master_records.append({"class": db_class, "sub_risk": db_subrisk, "psn": db_psn})
                        else:
                            clean_user_cls = clean_class_string(final_class)
                            if is_class_matching(clean_user_cls, clean_class_string(db_class)):
                                matched_master_records.append({"class": db_class, "sub_risk": db_subrisk, "psn": db_psn})
                    
                    if not matched_master_records and final_class:
                        st.error(f"❌ Mismatch Warning: Official IMDG lists UN {input_un} under Class `{un_exists['Class'].tolist()}`.")
                        is_valid_input = False
                    elif not final_class and len(matched_master_records) > 1:
                        st.info(f"💡 Multi-Category Alert: UN {input_un} contains {len(matched_master_records)} distinct regulatory classifications.")

            if is_valid_input and not input_un and final_class:
                matched_master_records.append({"class": final_class, "sub_risk": "", "psn": "Generic Category Search"})

            if is_valid_input and matched_master_records:
                st.markdown("---")
                
                for record in matched_master_records:
                    current_class = record["class"]
                    raw_subrisk = record["sub_risk"]
                    current_psn = record["psn"]
                    
                    master_subrisk_list = extract_subrisks_for_matching(raw_subrisk)
                    display_subrisk_text = format_subrisk_display(raw_subrisk)
                    
                    clean_current_class = clean_class_string(current_class)
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
                    
                    for sheet_name in search_targets:
                        df = excel_sheets[sheet_name]
                        df.columns = df.columns.astype(str).str.strip()
                        
                        col_mapping = {}
                        for c in df.columns:
                            c_lower = c.lower()
                            if any(k in c_lower for k in ['un號碼', 'un number', 'un_number']): col_mapping['UN'] = c
                            if any(k in c_lower for k in ['class/division', 'class', 'division', '類別']): col_mapping['Class'] = c
                            if any(k in c_lower for k in ['狀態', 'prohibited']): col_mapping['Prohibited'] = c
                            if any(k in c_lower for k in ['has remark', 'hasremark', '備註狀態']): col_mapping['HasRemark'] = c
                            if any(k in c_lower for k in ['次要風險', 'sub risk', 'subsidiary risk', 'subrisk']): col_mapping['SubRisk'] = c
                        
                        # Fallback for old status columns if new structure isn't fully defined yet
                        if 'Prohibited' not in col_mapping:
                            for c in df.columns:
                                if 'status' in c.lower(): col_mapping['Prohibited'] = c
                        
                        if 'UN' not in col_mapping or 'Class' not in col_mapping:
                            st.error(f"⚠️ Sheet `{sheet_name}` format error. Missing columns. Found: {list(df.columns)}")
                            continue
                        
                        remark_cols = [c for c in df.columns if any(k in c.lower() for k in ['remark', '備註', '限制', '條件', '敘述'])]
                        
                        df['Clean_UN'] = df[col_mapping['UN']].fillna('').apply(format_un_number)
                        df['Clean_Class'] = df[col_mapping['Class']].apply(clean_class_string)
                        
                        df['Clean_Prohibited'] = df[col_mapping['Prohibited']].fillna('').astype(str).str.strip().str.upper() if 'Prohibited' in col_mapping else ""
                        df['Clean_HasRemark'] = df[col_mapping['HasRemark']].fillna('').astype(str).str.strip().str.upper() if 'HasRemark' in col_mapping else ""
                        df['Clean_SubRisk'] = df[col_mapping['SubRisk']].fillna('').astype(str).str.strip() if 'SubRisk' in col_mapping else ""

                        matched_rows = []
                        global_class_remarks = []
                        has_global_prohibited = False
                        global_prohibited_row = None

                        # 1. Global Class Rules Scanning
                        if clean_current_class:
                            global_lines = df[(df['Clean_UN'] == '') | (df['Clean_UN'].str.upper() == 'ALL')]
                            
                            for _, g_row in global_lines.iterrows():
                                carrier_restricted_cls = g_row['Clean_Class']
                                
                                raw_p_val = g_row['Clean_Prohibited']
                                is_prohibited_status = any(k in raw_p_val for k in ["🔴", "禁收", "YES", "PROHIBITED"]) and (raw_p_val != 'NAN' and raw_p_val != '')
                                
                                main_class_hit = is_class_matching(clean_current_class, carrier_restricted_cls)
                                
                                sub_risk_hit = False
                                if master_subrisk_list and carrier_restricted_cls:
                                    if any(is_class_matching(sr, carrier_restricted_cls) for sr in master_subrisk_list if sr != "P"):
                                        sub_risk_hit = True
                                
                                if main_class_hit or sub_risk_hit:
                                    if is_prohibited_status:
                                        has_global_prohibited = True
                                        global_prohibited_row = g_row
                                    else:
                                        matched_rows.append(g_row)
                                    
                                    for r_col in remark_cols:
                                        r_val = str(g_row[r_col]).strip()
                                        if r_val and r_val.lower() != 'nan' and r_val != '':
                                            trigger_source = "Main Class" if main_class_hit else f"Sub Risk '{carrier_restricted_cls}'"
                                            global_class_remarks.append({
                                                "col_name": f"General Policy via {trigger_source}", 
                                                "text": r_val
                                            })

                        # 2. Precision Row Match Routing
                        if not input_un:
                            if has_global_prohibited and not matched_rows: 
                                matched_rows = [global_prohibited_row]
                        else:
                            exact_match = df[df['Clean_UN'] == input_un]
                            if not exact_match.empty:
                                exact_matched_rows = []
                                for _, row in exact_match.iterrows():
                                    carrier_cls = row['Clean_Class']
                                    carrier_subrisk = clean_class_string(row['Clean_SubRisk'])
                                    
                                    if carrier_cls and not is_class_matching(clean_current_class, carrier_cls):
                                        continue
                                    if carrier_subrisk and master_subrisk_list:
                                        if carrier_subrisk not in master_subrisk_list:
                                            continue
                                    exact_matched_rows.append(row)
                                
                                if exact_matched_rows:
                                    matched_rows = exact_matched_rows
                                elif has_global_prohibited and not matched_rows:
                                    matched_rows = [global_prohibited_row]
                            elif has_global_prohibited and not matched_rows:
                                matched_rows = [global_prohibited_row]

                        # --- Card Rendering ---
                        if not matched_rows:
                            st.markdown(f"""
                                <div class="partner-card" style="border-left-color: #10b981;">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span class="partner-title">🏢 Carrier: {sheet_name} (UN Ref: {input_un if input_un else "Class " + current_class})</span>
                                        <span class="status-badge" style="background-color: #d1fae5; color: #065f46;">🟢 Standard Acceptance</span>
                                    </div>
                                    <div style="margin-top: 10px;">
                                        <div class="remark-box"><div class="remark-line">No specific booking restrictions found for this category from this carrier.</div></div>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            for row in matched_rows:
                                p_text = str(row['Clean_Prohibited']).strip().upper()
                                r_text = str(row['Clean_HasRemark']).strip().upper()
                                
                                carrier_record_cls = row[col_mapping['Class']] if pd.notna(row[col_mapping['Class']]) else ""
                                un_display = row['Clean_UN'] if row['Clean_UN'] != '' else f"Class {current_class} Universal Policy"
                                if carrier_record_cls and row['Clean_UN'] != '':
                                    un_display = f"UN {row['Clean_UN']} (Class {carrier_record_cls})"
                                
                                # 💡 NEW THREE-TIER COLOR LOGIC
                                is_prohibited = any(k in p_text for k in ["🔴", "禁收", "YES", "PROHIBITED"]) and (p_text != 'NAN' and p_text != '')
                                is_has_remark = any(k in r_text for k in ["🟡", "YES", "TRUE"]) and (r_text != 'NAN' and r_text != '')
                                
                                if is_prohibited or has_global_prohibited:
                                    border_color = "#ef4444"; bg_badge = "#fee2e2"; text_badge = "#991b1b"
                                    display_status = "🔴 Strictly Prohibited"
                                elif is_has_remark:
                                    border_color = "#f59e0b"; bg_badge = "#fef3c7"; text_badge = "#92400e"
                                    display_status = "🟡 Conditional Acceptance / Review Remarks"
                                else:
                                    # 💡 GREEN LIGHT WITH REMARK: Both blank but item exists in table!
                                    border_color = "#10b981"; bg_badge = "#d1fae5"; text_badge = "#065f46"
                                    display_status = "🟢 Standard Acceptance (See Notice)"

                                collected_remarks = []
                                for r_col in remark_cols:
                                    r_val = str(row[r_col]).strip()
                                    if r_val and r_val.lower() != 'nan' and r_val != '':
                                        collected_remarks.append({"col_name": r_col, "text": r_val})

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
                                                {"".join([f'<div class="remark-header">📌 [{rem["col_name"]}]</div><div class="remark-line">{rem["text"]}</div>' for rem in combined_remarks]) if combined_remarks else '<div class="remark-line">Standard conditions apply.</div>'}
                                            </div>
                                        </div>
                                    </div>
                                """, unsafe_allow_html=True)
                st.markdown("<br><br>", unsafe_allow_html=True)
                            
    except Exception as e:
        st.error(f"❌ File reading failed. Error message: {e}")

# ==============================================================================
# FOOTER SECTION: Copyright & Confidentiality Declaration
# ==============================================================================
st.markdown("""
    <div class="footer-box">
        <div style="color: #e11d48; font-weight: bold; margin-bottom: 5px;">
            ⚠️ INTERNAL USE ONLY – DO NOT DISTRIBUTE EXTERNALLY
        </div>
        <div>
            Copyright © 2026 IAL DG TEAM. All Rights Reserved.
        </div>
    </div>
    """, unsafe_allow_html=True)
