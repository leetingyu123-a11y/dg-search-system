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

# 輔助函式：將任何輸入的 UN 號碼統一標準化成 4 碼字串
def format_un_number(un_val):
    if pd.isna(un_val):
        return ""
    # 如果是浮點數（例如 Excel 讀進來變 4.0），先轉成整數再轉字串
    if isinstance(un_val, float):
        if un_val.is_integer():
            un_val = int(un_val)
    val_str = str(un_val).strip()
    # 移除可能夾帶的小數點（例如 "4.0" -> "4"）
    if val_str.endswith('.0'):
        val_str = val_str[:-2]
        
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
        if os.path.exists(master_file):
            try:
                master_df = pd.read_excel(master_file, dtype=str)
                master_df.columns = master_df.columns.astype(str).str.strip()
                
                if 'UN Number' in master_df.columns and 'Class' in master_df.columns:
                    master_df['UN Number'] = master_df['UN Number'].apply(format_un_number)
                    has_master = True
            except Exception as e:
                st.warning(f"⚠️ 官方總表 imdg_master.xlsx 讀取失敗。錯誤: {e}")

        # 建立篩選介面 (簡化介面，讓 UN Number 當大主角)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🔍 請輸入 4 碼 UN 號碼 (推薦直接輸入)")
            raw_input_un = st.text_input("UN Number Input", placeholder="例如: 0004, 3480", label_visibility="collapsed").strip()
            input_un = format_un_number(raw_input_un) if raw_input_un else ""
            
        with col2:
            st.markdown("### 🏢 選擇特定航商 (選填)")
            partner_options = ["全部航商"] + all_partners
            selected_partner = st.selectbox("Partner Filter", partner_options, label_visibility="collapsed")

        if st.button("開始查詢", type="primary", use_container_width=True):
            if not input_un:
                st.warning("⚠️ 請輸入 UN 號碼再進行查詢！")
            else:
                final_class = ""
                official_psn_en = ""
                official_psn_ch = ""
                is_valid_input = True
                
                # 🧠 1. 去官方總表撈出這顆 UN 號碼的法定 Class 與 PSN
                if has_master:
                    un_exists = master_df[master_df['UN Number'] == input_un]
                    if un_exists.empty:
                        st.error(f"❌ 嚴重警告：在最新 IMDG Code 官方總表中，根本【查無此 UN 號碼：{input_un}】！")
                        is_valid_input = False
                    else:
                        final_class = str(un_exists.iloc[0]['Class']).strip()
                        if 'PSN' in un_exists.columns:
                            official_psn_en = str(un_exists.iloc[0]['PSN']).strip()
                        if 'PSN_CH' in un_exists.columns:
                            official_psn_ch = str(un_exists.iloc[0]['PSN_CH']).strip()
                
                clean_final_class = clean_class_string(final_class)

                # ==================== 🚨 航商黑名單絕對攔截比對 ====================
                if is_valid_input:
                    st.markdown("---")
                    
                    # 🎨 渲染官方大品名宣告卡片
                    if official_psn_en:
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
                        
                        required_cols = ['UN號碼', 'Class', '狀態', '限制條件']
                        if any(col not in df.columns for col in required_cols):
                            st.error(f"⚠️ 航商分頁 `{sheet_name}` 格式不符，請確認是否包含：UN號碼、Class、狀態、限制條件")
                            continue
                        
                        # 格式化航商 Excel 內容
                        df['UN號碼'] = df['UN號碼'].apply(format_un_number)
                        df['Clean_Class'] = df['Class'].apply(clean_class_string)
                        df['狀態'] = df['狀態'].astype(str).str.strip()
                        df['限制條件'] = df['限制條件'].astype(str).str.strip()

                        entries_to_show = []

                        # 🔥【重大改動：第一優先級】直接在該航商 Excel 裡找有沒有這顆精確的 UN 號碼！
                        exact_un_match = df[df['UN號碼'] == input_un]

                        if not exact_un_match.empty:
                            # 只要號碼對中，直接吃這行的條款，完全不管 Class 欄位寫得多髒！
                            for _, row in exact_un_match.iterrows():
                                entries_to_show.append({"un": row['UN號碼'], "status": row['狀態'], "remark": row['限制條件']})
                        else:
                            # 倘若 Excel 裡沒有直接寫這個 UN 號碼，我們才去看有沒有「該 Class 家族的 ALL 通用條款」
                            if clean_final_class:
                                match_class_all_df = df[
                                    (df['UN號碼'].str.upper() == 'ALL') & 
                                    (df['Clean_Class'].apply(lambda x: is_class_matching(clean_final_class, x)))
                                ]
                                if not match_class_all_df.empty:
                                    for _, row in match_class_all_df.iterrows():
                                        entries_to_show.append({"un": "ALL (通用條款)", "status": row['狀態'], "remark": row['限制條件']})

                        # 如果以上兩者都沒抓到，代表該航商既沒有單獨封殺這個 UN，也沒有封殺這個大類 ➡️ 綠燈放行！
                        if not entries_to_show:
                            entries_to_show.append({"un": input_un, "status": "🟢 正常收載", "remark": "該航商無針對此 UN 號碼或其 Class 家族設定特殊禁收限制"})

                        # --- 🎨 渲染航商限制卡片 ---
                        for entry in entries_to_show:
                            status = entry['status']
                            if "🔴" in status or "禁收" in status:
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
