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
    .remark-text {
        font-size: 22px !important; 
        line-height: 1.6;
        color: #1e293b;
        font-weight: 500;
        background-color: #ffffff;
        padding: 15px;
        border-radius: 6px;
        border: 1px solid #e2e8f0;
        white-space: pre-wrap; 
    }
    .partner-title {
        font-size: 26px !important;
        font-weight: bold;
        color: #0f172a;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🚢 各航商 DG 禁收清單查詢系統")
st.caption("🔥 全網最完備版：內建 IMDG Code 全 Class 家族雙向穿透演算法，徹底杜絕各航商 Excel 格式漏洞")

# 定義檔案路徑
excel_file = "dg_list.xlsx"
if not os.path.exists(excel_file):
    excel_file = os.path.join("DG_System", "dg_list.xlsx")

master_file = "imdg_master.xlsx"
if not os.path.exists(master_file):
    master_file = os.path.join("DG_System", "imdg_master.xlsx")

# 💡 核心優化：極致清洗，確保只留下數字與小數點 (例如 "Division 5.1" -> "5.1", "Class 3" -> "3")
def clean_class_string(class_val):
    if pd.isna(class_val):
        return ""
    val_str = str(class_val).strip()
    match = re.search(r'[0-9]+(?:\.[0-9]+)?', val_str)
    return match.group(0) if match else val_str

# 💡【核心重大升級】：全 Class 家族雙向穿透演算法
def is_class_matching(input_cls, target_cls):
    if not input_cls or not target_cls:
        return False
        
    # 1. 處理第 1 類（爆炸品大魔王）：不論子項，只要是 1 開頭一律視為相符
    if input_cls.startswith('1') and target_cls.startswith('1'):
        return True
        
    # 2. 精確字串相同（例如 5.1 對應 5.1，或 3 對應 3）
    if input_cls == target_cls:
        return True
        
    # 3. 雙向主類別包容性檢查（處理「主類別通用條款」與「細分亞類」的交叉盲區）
    # 情況 A：使用者輸入精確的 "5.1"，但航商 Excel 裡寫的是大類 "5"（代表第 5 類全禁）
    if '.' in input_cls and '.' not in target_cls:
        main_class = input_cls.split('.')[0]
        if main_class == target_cls:
            return True
            
    # 情況 B：使用者輸入大類 "5"，但航商 Excel 裡寫的是細分 "5.1"
    if '.' not in input_cls and '.' in target_cls:
        main_class = target_cls.split('.')[0]
        if main_class == input_cls:
            return True
            
    return False

# 輔助函式：將任何輸入的 UN 號碼統一標準化成 4 碼字串
def format_un_number(un_val):
    if pd.isna(un_val):
        return ""
    val_str = str(un_val).strip()
    if val_str.upper() == 'ALL':
        return 'ALL'
    if val_str.isdigit():
        return val_str.zfill(4)
    return val_str

if not os.path.exists(excel_file):
    st.error("❌ 找不到 dg_list.xlsx 檔案！請確認 Excel 檔案是否已經上傳至 GitHub。")
else:
    try:
        excel_sheets = pd.read_excel(excel_file, sheet_name=None)
        all_partners = [sheet for sheet in excel_sheets.keys() if not (sheet.startswith("Sheet") and excel_sheets[sheet].empty)]
        
        has_master = False
        official_psn_en = ""
        official_psn_ch = ""
        
        if os.path.exists(master_file):
            try:
                master_df = pd.read_excel(master_file, dtype=str)
                master_df.columns = master_df.columns.astype(str).str.strip()
                
                if 'UN Number' in master_df.columns and 'Class' in master_df.columns:
                    master_df['UN Number'] = master_df['UN Number'].apply(format_un_number)
                    has_master = True
                else:
                    st.warning(f"⚠️ 官方總表 `imdg_master.xlsx` 內缺少 'UN Number' 或 'Class' 欄位！")
            except Exception as e:
                st.warning(f"⚠️ 官方總表 imdg_master.xlsx 讀取失敗。錯誤: {e}")

        if not has_master:
            st.warning("💡 提示：目前 GitHub 中尚未配置有效的官方總表 `imdg_master.xlsx`。")

        # 建立篩選介面
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 1. 請輸入 Class 類別 (必填)")
            input_class = st.text_input("Class", placeholder="例如: 1, 3, 5.1, 9", label_visibility="collapsed").strip()
            clean_input_class = clean_class_string(input_class)
            
        with col2:
            st.markdown("### 2. 請輸入 UN 號碼 (選填)")
            raw_input_un = st.text_input("UN Number", placeholder="例如: 0004, 3480", label_visibility="collapsed").strip()
            input_un = format_un_number(raw_input_un) if raw_input_un else ""
            
        with col3:
            st.markdown("### 3. 選擇特定航商 (選填)")
            partner_options = ["全部航商"] + all_partners
            selected_partner = st.selectbox("Partner Filter", partner_options, label_visibility="collapsed")

        if st.button("開始查詢", type="primary", use_container_width=True):
            if not input_class:
                st.warning("⚠️ 請至少輸入 Class 類別再進行查詢！")
            else:
                # ==================== 🚨 第一關：官方字典防呆驗證 ＆ 提取 PSN ====================
                is_valid_input = True
                if has_master and input_un:
                    un_exists = master_df[master_df['UN Number'] == input_un]
                    
                    if un_exists.empty:
                        st.error(f"❌ 嚴重警告：在最新 IMDG Code 官方總表中，根本【查無此 UN 號碼：{input_un}】！")
                        is_valid_input = False
                    else:
                        official_classes = [clean_class_string(c) for c in un_exists['Class'].tolist()]
                        class_match = any(is_class_matching(clean_input_class, c) for c in official_classes if c)
                        
                        if not class_match:
                            st.error(f"❌ 警告：官方總表中 UN {input_un} 對應的合法 Class 為 `{un_exists['Class'].tolist()}`。")
                            st.error(f"🚨 但您輸入的 Class 是 `{input_class}`，兩者完全對不上！")
                            is_valid_input = False
                        else:
                            if 'PSN' in un_exists.columns:
                                official_psn_en = str(un_exists.iloc[0]['PSN']).strip()
                            if 'PSN_CH' in un_exists.columns:
                                official_psn_ch = str(un_exists.iloc[0]['PSN_CH']).strip()

                # ==================== 第二關：航商黑名單比對 (過關才執行) ====================
                if is_valid_input:
                    st.markdown("---")
                    
                    if input_un and official_psn_en:
                        ch_display = f" / {official_psn_ch}" if official_psn_ch and official_psn_ch != "nan" else ""
                        st.markdown(f"""
                            <div class="psn-card">
                                <div style="font-size: 16px; opacity: 0.8; font-weight: bold; margin-bottom: 5px;">🌍 IMDG Code 42-24 官方標準品名 (PSN)：</div>
                                <div style="font-size: 28px; font-weight: bold; line-height: 1.3;">UN {input_un} - {official_psn_en}{ch_display}</div>
                                <div style="font-size: 14px; opacity: 0.9; margin-top: 5px;">官方法定分類：Class {input_class}</div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    search_targets = all_partners if selected_partner == "全部航商" else [selected_partner]
                    
                    for sheet_name in search_targets:
                        df = excel_sheets[sheet_name]
                        df.columns = df.columns.astype(str).str.strip()
                        
                        required_cols = ['UN號碼', 'Class', '狀態', '限制條件']
                        if any(col not in df.columns for col in required_cols):
                            st.error(f"⚠️ 航商分頁 `{sheet_name}` 格式不符，請確認是否包含：UN號碼、Class、狀態、限制條件")
                            continue
                        
                        df['Clean_Class'] = df['Class'].apply(clean_class_string)
                        df['UN號碼'] = df['UN號碼'].apply(format_un_number)
                        df['狀態'] = df['狀態'].astype(str).str.strip()
                        df['限制條件'] = df['限制條件'].astype(str).str.strip()

                        # 💡 呼叫全新的全類別穿透演算法
                        match_class_df = df[
                            df['Clean_Class'].apply(lambda x: is_class_matching(clean_input_class, x))
                        ]
                        
                        entries_to_show = []
                        
                        if match_class_df.empty:
                            entries_to_show.append({
                                "un": input_un if input_un else "該 Class 全品項",
                                "status": "🟢 正常收載", "remark": "Excel 中無此 Class 任何禁收限制"
                            })
                        else:
                            if not input_un:
                                for _, row in match_class_df.iterrows():
                                    entries_to_show.append({
                                        "un": row['UN號碼'], "status": row['狀態'], "remark": row['限制條件']
                                    })
                            else:
                                absolute_row = match_class_df[
                                    (match_class_df['UN號碼'].str.upper() == 'ALL') & 
                                    (match_class_df['狀態'].str.contains('絕對禁收'))
                                ]
                                
                                if not absolute_row.empty:
                                    entries_to_show.append({"un": "ALL", "status": "🔴 絕對禁收", "remark": absolute_row.iloc[0]['限制條件']})
                                else:
                                    exact_un_match = match_class_df[match_class_df['UN號碼'] == input_un]
                                    
                                    if not exact_un_match.empty:
                                        for _, row in exact_un_match.iterrows():
                                            entries_to_show.append({"un": row['UN號碼'], "status": row['狀態'], "remark": row['限制條件']})
                                    else:
                                        all_property_row = match_class_df[match_class_df['UN號碼'].str.upper() == 'ALL']
                                        if not all_property_row.empty:
                                            for _, row in all_property_row.iterrows():
                                                entries_to_show.append({"un": "ALL (通用條款)", "status": row['狀態'], "remark": row['限制條件']})
                                        else:
                                            entries_to_show.append({"un": input_un, "status": "🟢 正常收載", "remark": "無特殊禁收限制"})

                        # --- 🎨 渲染大卡片 ---
                        for entry in entries_to_show:
                            status = entry['status']
                            if "🔴" in status:
                                border_color = "#ef4444"; bg_badge = "#fee2e2"; text_badge = "#991b1b"
                            elif "🟡" in status or "特定" in status or "注意" in status:
                                border_color = "#f59e0b"; bg_badge = "#fef3c7"; text_badge = "#92400e"
                            else:
                                border_color = "#10b981"; bg_badge = "#d1fae5"; text_badge = "#065f46"
                            
                            st.markdown(f"""
                                <div class="partner-card" style="border-left-color: {border_color};">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span class="partner-title">🏢 航商：{sheet_name} (對應UN: {entry['un']})</span>
                                        <span class="status-badge" style="background-color: {bg_badge}; color: {text_badge};">{status}</span>
                                    </div>
                                    <div style="margin-top: 10px;">
                                        <div style="font-weight: bold; color: #64748b; margin-bottom: 5px; font-size: 14px;">📝 限制條件與完整備註：</div>
                                        <div class="remark-text">{entry['remark']}</div>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                        
    except Exception as e:
        st.error(f"❌ 讀取檔案失敗。錯誤訊息: {e}")
