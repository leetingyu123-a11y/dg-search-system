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

# 💡 清洗 Class 欄位，只留下數字與小數點
def clean_class_string(class_val):
    if pd.isna(class_val):
        return ""
    val_str = str(class_val).strip()
    match = re.search(r'[0-9]+(?:\.[0-9]+)?', val_str)
    return match.group(0) if match else val_str

# 💡 全 Class 家族雙向穿透演算法
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
            st.warning("💡 提示：目前 GitHub 中尚未配置有效的官方總表 `imdg_master.xlsx`。系統目前無法啟用「免填 Class 自動識別」及官方防呆功能。")

        # 建立篩選介面
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 1. 輸入 UN 號碼 (必填/選填)")
            raw_input_un = st.text_input("UN Number", placeholder="例如: 0004, 3480", label_visibility="collapsed").strip()
            input_un = format_un_number(raw_input_un) if raw_input_un else ""
            
        with col2:
            st.markdown("### 2. 輸入 Class 類別 (選填)")
            input_class = st.text_input("Class", placeholder="不填則由系統依 UN 自動追隨判定", label_visibility="collapsed").strip()
            
        with col3:
            st.markdown("### 3. 選擇特定航商 (選填)")
            partner_options = ["全部航商"] + all_partners
            selected_partner = st.selectbox("Partner Filter", partner_options, label_visibility="collapsed")

        if st.button("開始查詢", type="primary", use_container_width=True):
            # 決定最終要比對的 Class 條款
            final_class = input_class.strip()
            official_psn_en = ""
            official_psn_ch = ""
            is_valid_input = True
            
            # 🚨 防呆攔截：如果兩個都沒填
            if not input_un and not final_class:
                st.warning("⚠️ 請至少輸入「UN 號碼」或「Class 類別」其中一項再進行查詢！")
                is_valid_input = False
                
            # 🧠 核心自動化功能：如果使用者有填 UN，但沒填 Class
            if is_valid_input and input_un and has_master:
                un_exists = master_df[master_df['UN Number'] == input_un]
                
                if un_exists.empty:
                    st.error(f"❌ 嚴重警告：在最新 IMDG Code 官方總表中，根本【查無此 UN 號碼：{input_un}】！")
                    st.error("🚨 訂艙人員極可能手誤 key 錯品項，請立即重新核對 MSDS，切勿直接放行！")
                    is_valid_input = False
                else:
                    # 抓取官方定義的 Class
                    official_class_from_db = str(un_exists.iloc[0]['Class']).strip()
                    
                    # 抓取官方正式品名 (PSN)
                    if 'PSN' in un_exists.columns:
                        official_psn_en = str(un_exists.iloc[0]['PSN']).strip()
                    if 'PSN_CH' in un_exists.columns:
                        official_psn_ch = str(un_exists.iloc[0]['PSN_CH']).strip()
                    
                    # 如果使用者放空 Class，幫他自動填寫！
                    if not final_class:
                        final_class = official_class_from_db
                        st.info(f"💡 系統偵測：已自動識別標準法規為 Class `{final_class}`")
                    else:
                        # 如果使用者自己有填 Class，則做交叉驗證防錯
                        clean_user_cls = clean_class_string(final_class)
                        official_classes_clean = [clean_class_string(c) for c in un_exists['Class'].tolist()]
                        class_match = any(is_class_matching(clean_user_cls, c) for c in official_classes_clean if c)
                        
                        if not class_match:
                            st.error(f"❌ 警告：官方總表中 UN {input_un} 對應的合法 Class 為 `{un_exists['Class'].tolist()}`。")
                            st.error(f"🚨 但您手動輸入的 Class 是 `{final_class}`，兩者完全對不上！請確認是否填錯。")
                            is_valid_input = False

            # 清洗最終用於比對的 Class 字串
            clean_final_class = clean_class_string(final_class)

            # ==================== 第二關：航商黑名單精準比對 (過關才執行) ====================
            if is_valid_input:
                st.markdown("---")
                
                # 🎨 渲染官方大品名宣告卡片
                if input_un and official_psn_en:
                    ch_display = f" / {official_psn_ch}" if official_psn_ch and official_psn_ch != "nan" else ""
                    st.markdown(f"""
                        <div class="psn-card">
                            <div style="font-size: 16px; opacity: 0.8; font-weight: bold; margin-bottom: 5px;">🌍 IMDG Code 42-24 官方標準品名 (PSN)：</div>
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
                    
                    df['Clean_Class'] = df['Class'].apply(clean_class_string)
                    df['UN號碼'] = df['UN號碼'].apply(format_un_number)
                    df['狀態'] = df['狀態'].astype(str).str.strip()
                    df['限制條件'] = df['限制條件'].astype(str).str.strip()

                    # 使用清洗後的 Class 進行家族穿透篩選
                    match_class_df = df[
                        df['Clean_Class'].apply(lambda x: is_class_matching(clean_final_class, x))
                    ]
                    
                    entries_to_show = []
                    
                    if match_class_df.empty:
                        entries_to_show.append({
                            "un": input_un if input_un else "該 Class 全品項",
                            "status": "🟢 正常收載", "remark": "Excel 中無此 Class 任何禁收限制"
                        })
                    else:
                        # 情況一：使用者沒有輸入 UN 號碼 ➡️ 展開該 Class 的所有禁收
                        if not input_un:
                            for _, row in match_class_df.iterrows():
                                entries_to_show.append({
                                    "un": row['UN號碼'], "status": row['狀態'], "remark": row['限制條件']
                                })
                        # 情況二：使用者輸入了特定 UN 號碼 ➡️ 進行精準分流
                        else:
                            absolute_all_row = match_class_df[
                                (match_class_df['UN號碼'].str.upper() == 'ALL') & 
                                (match_class_df['狀態'].str.contains('絕對禁收'))
                            ]
                            exact_un_match = match_class_df[match_class_df['UN號碼'] == input_un]
                            general_all_row = match_class_df[match_class_df['UN號碼'].str.upper() == 'ALL']
                            
                            if not absolute_all_row.empty:
                                entries_to_show.append({"un": "ALL", "status": "🔴 絕對禁收", "remark": absolute_all_row.iloc[0]['限制條件']})
                            elif not exact_un_match.empty:
                                for _, row in exact_un_match.iterrows():
                                    entries_to_show.append({"un": row['UN號碼'], "status": row['狀態'], "remark": row['限制條件']})
                                if not general_all_row.empty:
                                    for _, row in general_all_row.iterrows():
                                        entries_to_show.append({"un": "ALL (通用條款)", "status": row['狀態'], "remark": row['限制條件']})
                            elif not general_all_row.empty:
                                for _, row in general_all_row.iterrows():
                                    entries_to_show.append({"un": "ALL (通用條款)", "status": row['狀態'], "remark": row['限制條件']})
                            else:
                                entries_to_show.append({"un": input_un, "status": "🟢 正常收載", "remark": "無特殊禁收限制"})

                    # --- 🎨 渲染航商限制卡片 ---
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
