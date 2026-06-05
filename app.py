import streamlit as st
import pandas as pd
import os
import re

# 設定網頁標題與寬度版面
st.set_page_config(page_title="各航商 DG 禁收清單查詢系統", layout="wide")

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

st.title("🚢 各航商 DG 禁收清單查詢系統")
st.caption("🔥 終極法規繼承版：自動穿透 UN 空白大類限制、自動套用 Class 3 閃點等大類通用 Remark！")

# 定義檔案路徑
excel_file = "dg_list.xlsx"
if not os.path.exists(excel_file):
    excel_file = os.path.join("DG_System", "dg_list.xlsx")

master_file = "imdg_master.xlsx"
if not os.path.exists(master_file):
    master_file = os.path.join("DG_System", "imdg_master.xlsx")

# 清洗 Class 欄位，只留下數字與小數點
def clean_class_string(class_val):
    if pd.isna(class_val):
        return ""
    val_str = str(class_val).strip()
    match = re.search(r'[0-9]+(?:\.[0-9]+)?', val_str)
    return match.group(0) if match else val_str

# 全 Class 家族雙向穿透演算法
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

# 超強效極致清洗：還原前導零
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
    st.error("❌ 找不到 dg_list.xlsx 檔案！請確認 Excel 檔案是否已經上傳至 GitHub。")
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
                st.warning(f"⚠️ 官方總表 imdg_master.xlsx 讀取失敗。錯誤: {e}")

        # 建立篩選介面
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### 1. 請輸入 Class 類別 (選填)")
            user_input_class = st.text_input("Class Input", placeholder="例如: 1, 2.3, 3", label_visibility="collapsed").strip()
        with col2:
            st.markdown("### 2. 請輸入 UN 號碼 (選填)")
            raw_input_un = st.text_input("UN Number Input", placeholder="例如: 0005, 1088", label_visibility="collapsed").strip()
            input_un = format_un_number(raw_input_un) if raw_input_un else ""
        with col3:
            st.markdown("### 3. 選擇特定航商 (選填)")
            partner_options = ["全部航商"] + all_partners
            selected_partner = st.selectbox("Partner Filter", partner_options, label_visibility="collapsed")

        if st.button("開始查詢", type="primary", use_container_width=True):
            final_class = user_input_class
            official_psn_en = ""
            official_psn_ch = ""
            is_valid_input = True
            
            if not input_un and not final_class:
                st.warning("⚠️ 請至少輸入「UN 號碼」或「Class 類別」其中一項再進行查詢！")
                is_valid_input = False
                
            if is_valid_input and input_un and has_master:
                un_exists = master_df[master_df['UN Number'] == input_un]
                if un_exists.empty:
                    st.error(f"❌ 嚴重警告：在最新 IMDG Code 官方總表中，根本【查無此 UN 號碼：{input_un}】！")
                    is_valid_input = False
                else:
                    official_class_from_db = str(un_exists.iloc[0]['Class']).strip()
                    if 'PSN' in un_exists.columns:
                        official_psn_en = str(un_exists.iloc[0]['PSN']).strip()
                    if 'PSN_CH' in un_exists.columns:
                        official_psn_ch = str(un_exists.iloc[0]['PSN_CH']).strip()
                    if not final_class:
                        final_class = official_class_from_db
                        st.info(f"💡 系統自動識別法規類別：Class `{final_class}`")
                    else:
                        clean_user_cls = clean_class_string(final_class)
                        official_classes_clean = [clean_class_string(c) for c in un_exists['Class'].tolist()]
                        class_match = any(is_class_matching(clean_user_cls, c) for c in official_classes_clean if c)
                        if not class_match:
                            st.error(f"❌ 警告：官方總表中 UN {input_un} 對應的合法 Class 為 `{un_exists['Class'].tolist()}`。")
                            st.error(f"🚨 但您手動輸入的 Class 是 `{user_input_class}`，兩者完全對不上！")
                            is_valid_input = False

            clean_final_class = clean_class_string(final_class)

            if is_valid_input:
                st.markdown("---")
                if input_un and official_psn_en:
                    ch_display = f" / {official_psn_ch}" if official_psn_ch and official_psn_ch != "nan" else ""
                    st.markdown(f"""
                        <div class="psn-card">
                            <div style="font-size: 16px; opacity: 0.8; font-weight: bold; margin-bottom: 5px;">🌍 IMDG Code 官方標準法規識別：</div>
                            <div style="font-size: 28px; font-weight: bold; line-height: 1.3;">UN {input_un} - {official_psn_en}{ch_display}</div>
                            <div style="font-size: 14px; opacity: 0.9; margin-top: 5px;">官方法定分類：Class {final_class}</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                search_targets = all_partners if selected_partner == "全部航商" else [selected_partner]
                
                for sheet_name in search_targets:
                    df = excel_sheets[sheet_name]
                    df.columns = df.columns.astype(str).str.strip()
                    
                    col_mapping = {}
                    for c in df.columns:
                        if c in ['UN號碼', 'UN Number']: col_mapping['UN'] = c
                        if c == 'Class': col_mapping['Class'] = c
                        if c in ['狀態', 'Prohibited']: col_mapping['Status'] = c
                    
                    if 'UN' not in col_mapping or 'Class' not in col_mapping or 'Status' not in col_mapping:
                        st.error(f"⚠️ 航商分頁 `{sheet_name}` 格式不符，請確認是否包含基本欄位")
                        continue
                    
                    remark_cols = [c for c in df.columns if any(k in c.lower() for k in ['remark', '備註', '限制', '條件', '敘述'])]
                    
                    # 💡 容錯清洗：將空白格轉為空字串，方便比對
                    df['Clean_UN'] = df[col_mapping['UN']].fillna('').apply(format_un_number)
                    df['Clean_Class'] = df[col_mapping['Class']].apply(clean_class_string)
                    df['Clean_Status'] = df[col_mapping['Status']].fillna('').astype(str).str.strip()

                    matched_rows = []
                    global_class_remarks = [] # 用於收集「UN 留白」的大類通用備註

                    # 🧠 【特殊法規智慧過濾機制】
                    # 先找出該航商 Excel 裡，有沒有「UN 是空的」但「Class 符合這次查詢」的大類通用條款
                    if clean_final_class:
                        global_rules = df[
                            ((df['Clean_UN'] == '') | (df['Clean_UN'].str.upper() == 'ALL')) & 
                            (df['Clean_Class'].apply(lambda x: is_class_matching(clean_final_class, x)))
                        ]
                        for _, g_row in global_rules.iterrows():
                            # 收集通用備註文字
                            for r_col in remark_cols:
                                r_val = str(g_row[r_col]).strip()
                                if r_val and r_val.lower() != 'nan' and r_val != '':
                                    global_class_remarks.append({"col_name": f"大類通用限制 ({g_row[col_mapping['Class']]})", "text": r_val})
                            
                            # 如果這個通用條款的狀態是 YES（例如 2.3 條款），且目前是有輸入特定 UN 的情況，則把它直接升格為撞線紀錄！
                            if input_un and any(k in g_row['Clean_Status'].upper() for k in ["🔴", "禁收", "YES", "PROHIBITED"]):
                                matched_rows.append(g_row)

                    # 正常的號碼與 Class 分流查詢
                    if not input_un:
                        match_df = df[df['Clean_Class'].apply(lambda x: is_class_matching(clean_final_class, x)) & (df['Clean_UN'] != '')]
                        for _, row in match_df.iterrows():
                            matched_rows.append(row)
                    else:
                        exact_match = df[df['Clean_UN'] == input_un]
                        if not exact_match.empty:
                            for _, row in exact_match.iterrows():
                                matched_rows.append(row)

                    # --- 🎨 渲染卡片結果 ---
                    if not matched_rows:
                        # 雖然號碼沒中，但如果有一條「Class 3 閃點通用備註」，我們也要以黃燈警告方式秀出來！
                        if global_class_remarks:
                            st.markdown(f"""
                                <div class="partner-card" style="border-left-color: #f59e0b;">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span class="partner-title">🏢 航商：{sheet_name} (對應UN: {input_un})</span>
                                        <span class="status-badge" style="background-color: #fef3c7; color: #92400e;">🟡 特定收載 / 須注意大類規範</span>
                                    </div>
                                    <div style="margin-top: 10px;">
                                        <div style="font-weight: bold; color: #64748b; margin-bottom: 5px; font-size: 14px;">📝 航商大類通用規範提醒：</div>
                                        <div class="remark-box">
                                            {"".join([f'<div class="remark-header" style="color:#b45309;">⚠️ [{rem["col_name"]}]</div><div class="remark-line">{rem["text"]}</div>' for rem in global_class_remarks])}
                                        </div>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            # 真正安全的綠燈
                            st.markdown(f"""
                                <div class="partner-card" style="border-left-color: #10b981;">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span class="partner-title">🏢 航商：{sheet_name} (對應UN: {input_un if input_un else "該 Class"})</span>
                                        <span class="status-badge" style="background-color: #d1fae5; color: #065f46;">🟢 正常收載</span>
                                    </div>
                                    <div style="margin-top: 10px;">
                                        <div class="remark-box"><div class="remark-line">該航商無針對此查詢品項設定特殊禁收限制。</div></div>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        # 有精確號碼撞線，或者是被 2.3 大類株連禁收
                        for row in matched_rows:
                            status_text = row['Clean_Status']
                            un_display = row['Clean_UN'] if row['Clean_UN'] != '' else "大類限制"
                            
                            if any(k in status_text.upper() for k in ["🔴", "禁收", "YES", "PROHIBITED"]):
                                border_color = "#ef4444"; bg_badge = "#fee2e2"; text_badge = "#991b1b"
                                display_status = "🔴 絕對禁收"
                            else:
                                border_color = "#f59e0b"; bg_badge = "#fef3c7"; text_badge = "#92400e"
                                display_status = "🟡 特定收載 / 須注意備註"

                            # 收集本行自己的特殊備註
                            collected_remarks = []
                            for r_col in remark_cols:
                                r_val = str(row[r_col]).strip()
                                if r_val and r_val.lower() != 'nan' and r_val != '':
                                    collected_remarks.append({"col_name": r_col, "text": r_val})

                            # 💡 核心魔法：把剛剛在別行抓到的「Class 3 大類通用閃點限制」強行塞進這張卡片裡合併顯示！
                            combined_remarks = []
                            combined_remarks.extend(collected_remarks)
                            for g_rem in global_class_remarks:
                                # 避免重複加入相同的文字
                                if g_rem["text"] not in [c["text"] for c in combined_remarks]:
                                    combined_remarks.append(g_rem)

                            st.markdown(f"""
                                <div class="partner-card" style="border-left-color: {border_color};">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span class="partner-title">🏢 航商：{sheet_name} (Excel欄位對應: {un_display})</span>
                                        <span class="status-badge" style="background-color: {bg_badge}; color: {text_badge};">{display_status}</span>
                                    </div>
                                    <div style="margin-top: 10px;">
                                        <div style="font-weight: bold; color: #64748b; margin-bottom: 5px; font-size: 14px;">📝 航商完整備註清單（含大類繼承規範）：</div>
                                        <div class="remark-box">
                                            {"".join([f'<div class="remark-header">📌 [{rem["col_name"]}]</div><div class="remark-line">{rem["text"]}</div>' for rem in combined_remarks]) if combined_remarks else '<div class="remark-line">此項禁收無額外備註條件。</div>'}
                                        </div>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                            
    except Exception as e:
        st.error(f"❌ 讀取檔案失敗。錯誤訊息: {e}")
