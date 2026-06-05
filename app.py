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
st.caption("🔥 完美修正版：優化前導零（0005）清洗機制 ＆ 支援 Class 與 UN 號碼雙欄自由選填")

# 定義檔案路徑
excel_file = "dg_list.xlsx"
if not os.path.exists(excel_file):
    excel_file = os.path.join("DG_System", "dg_list.xlsx")

master_file = "imdg_master.xlsx"
if not os.path.exists(master_file):
    master_file = os.path.join("DG_System", "imdg_master.xlsx")

# 清洗 Class 欄位，只留下數字與小數點 (例如 "Division 1.1" -> "1.1")
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

# 💡 超強效極致清洗：確保 0005 不管在 Excel 裡怎麼變形，通通被強行還原成 "0005"
def format_un_number(un_val):
    if pd.isna(un_val):
        return ""
    
    # 處理可能被讀成 float 的情況 (如 5.0 -> 5)
    if isinstance(un_val, float):
        if un_val.is_integer():
            un_val = int(un_val)
            
    val_str = str(un_val).strip()
    
    # 再次防呆處理字串尾巴帶有 .0 的情況
    if val_str.endswith('.0'):
        val_str = val_str[:-2]
        
    if val_str.upper() == 'ALL':
        return 'ALL'
        
    # 如果整串都是數字，強行補足 4 位數（解決 5 -> 0005 的問題）
    if val_str.isdigit():
        return val_str.zfill(4)
        
    # 如果是帶有非數字的（如某些特別欄位），提取數字部分來補零
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

        # 建立篩選介面 (兩者皆為選填)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 1. 請輸入 Class 類別 (選填)")
            user_input_class = st.text_input("Class Input", placeholder="例如: 1, 3, 5.1", label_visibility="collapsed").strip()
            
        with col2:
            st.markdown("### 2. 請輸入 UN 號碼 (選填)")
            raw_input_un = st.text_input("UN Number Input", placeholder="例如: 0005, 3480", label_visibility="collapsed").strip()
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
                
            # 🧠 智慧判斷：透過輸入的 UN 去捞官方字典
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
                    
                    # 如果使用者沒手填 Class，自動由系統代入官方分類
                    if not final_class:
                        final_class = official_class_from_db
                        st.info(f"💡 系統自動識別法規類別：Class `{final_class}`")
                    else:
                        # 如果使用者自己有填，做交叉驗證
                        clean_user_cls = clean_class_string(final_class)
                        official_classes_clean = [clean_class_string(c) for c in un_exists['Class'].tolist()]
                        class_match = any(is_class_matching(clean_user_cls, c) for c in official_classes_clean if c)
                        
                        if not class_match:
                            st.error(f"❌ 警告：官方總表中 UN {input_un} 對應的合法 Class 為 `{un_exists['Class'].tolist()}`。")
                            st.error(f"🚨 但您手動輸入的 Class 是 `{user_input_class}`，兩者完全對不上！")
                            is_valid_input = False

            clean_final_class = clean_class_string(final_class)

            # ==================== 🚨 第二關：航商黑名單對比 ====================
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
                    
                    required_cols = ['UN號碼', 'Class', '狀態', '限制條件']
                    if any(col not in df.columns for col in required_cols):
                        st.error(f"⚠️ 航商分頁 `{sheet_name}` 格式不符，請確認是否包含：UN號碼、Class、狀態、限制條件")
                        continue
                    
                    # 💡 關鍵強力清洗：在進行任何篩選前，先把航商 Excel 裡面的 UN 號碼全部強制洗成 4 碼字串
                    df['UN號碼'] = df['UN號碼'].apply(format_un_number)
                    df['Clean_Class'] = df['Class'].apply(clean_class_string)
                    df['狀態'] = df['狀態'].astype(str).str.strip()
                    df['限制條件'] = df['限制條件'].astype(str).str.strip()

                    entries_to_show = []

                    # 🟢 分流 A：使用者沒填 UN 號碼 ➡️ 依據 Class 攤開所有列
                    if not input_un:
                        match_class_df = df[
                            df['Clean_Class'].apply(lambda x: is_class_matching(clean_final_class, x))
                        ]
                        for _, row in match_class_df.iterrows():
                            entries_to_show.append({"un": row['UN號碼'], "status": row['狀態'], "remark": row['限制條件']})
                    
                    # 🔵 分流 B：使用者有填寫特定 UN 號碼 ➡️ 絕對強行精準對比
                    else:
                        # 經過上面強大清洗後，這裡比對的 input_un ("0005") 就能精準擊中 df['UN號碼'] 裡的 "0005"
                        exact_un_match = df[df['UN號碼'] == input_un]
                        
                        if not exact_un_match.empty:
                            for _, row in exact_un_match.iterrows():
                                entries_to_show.append({"un": row['UN號碼'], "status": row['狀態'], "remark": row['限制條件']})
                        else:
                            # 沒單獨號碼條款，改找該 Class 的通用 ALL 條款
                            if clean_final_class:
                                match_class_all_df = df[
                                    (df['UN號碼'].str.upper() == 'ALL') & 
                                    (df['Clean_Class'].apply(lambda x: is_class_matching(clean_final_class, x)))
                                ]
                                for _, row in match_class_all_df.iterrows():
                                    entries_to_show.append({"un": "ALL (通用條款)", "status": row['狀態'], "remark": row['限制條件']})

                    # 如果都完全沒中，才是安全放行
                    if not entries_to_show:
                        entries_to_show.append({"un": input_un if input_un else "該 Class", "status": "🟢 正常收載", "remark": "該航商無針對此查詢品項設定特殊禁收限制"})

                    # --- 🎨 渲染卡片 ---
                    for entry in entries_to_show:
                        status = entry['status']
                        # 只要狀態文字裡包含「YES」、「禁收」、「不能收」、「🔴」等字眼，一律上紅牌
                        if "🔴" in status or "禁收" in status or status.upper() == "YES":
                            border_color = "#ef4444"; bg_badge = "#fee2e2"; text_badge = "#991b1b"
                            display_status = "🔴 絕對禁收"
                        elif "🟡" in status or "特定" in status or "注意" in status:
                            border_color = "#f59e0b"; bg_badge = "#fef3c7"; text_badge = "#92400e"
                            display_status = status
                        else:
                            border_color = "#10b981"; bg_badge = "#d1fae5"; text_badge = "#065f46"
                            display_status = status
                        
                        # 如果航商限制條件是空的（像 IAL 的 0005 後面是空的），幫它美化補字
                        display_remark = entry['remark']
                        if not display_remark or display_remark.lower() == 'nan' or display_remark == '':
                            display_remark = "該航商對此品項公告為禁止收載，無額外備註條件。"

                        st.markdown(f"""
                            <div class="partner-card" style="border-left-color: {border_color};">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span class="partner-title">🏢 航商：{sheet_name} (對應UN: {entry['un']})</span>
                                    <span class="status-badge" style="background-color: {bg_badge}; color: {text_badge};">{display_status}</span>
                                </div>
                                <div style="margin-top: 10px;">
                                    <div style="font-weight: bold; color: #64748b; margin-bottom: 5px; font-size: 14px;">📝 限制條件與完整備註：</div>
                                    <div class="remark-text">{display_remark}</div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        
    except Exception as e:
        st.error(f"❌ 讀取檔案失敗。錯誤訊息: {e}")
