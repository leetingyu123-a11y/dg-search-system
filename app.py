import streamlit as st
import pandas as pd
import os

# 設定網頁標題與寬度版面
st.set_page_config(page_title="各航商 DG 禁收清單查詢系統", layout="wide")

# 強制放大網頁文字與備註區塊的自訂樣式 (CSS)
st.markdown("""
    <style>
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
st.caption("🔥 智能防錯版：內建 IMDG 官方字典驗證，嚴防打錯 UN 號碼漏報出事")

# 定義檔案路徑
excel_file = "dg_list.xlsx"
if not os.path.exists(excel_file):
    excel_file = os.path.join("DG_System", "dg_list.xlsx")

master_file = "imdg_master.csv"
if not os.path.exists(master_file):
    master_file = os.path.join("DG_System", "imdg_master.csv")

# 檢查必要的檔案是否存在
if not os.path.exists(excel_file):
    st.error("❌ 找不到 dg_list.xlsx 檔案！請確認 Excel 檔案是否已經上傳至 GitHub。")
else:
    try:
        # 讀取航商管制 Excel
        excel_sheets = pd.read_excel(excel_file, sheet_name=None)
        all_partners = [sheet for sheet in excel_sheets.keys() if not (sheet.startswith("Sheet") and excel_sheets[sheet].empty)]
        
        # 讀取官方總表字典 (CSV)
        has_master = False
        if os.path.exists(master_file):
            try:
                # 讀取官方字典，將 UN 號碼與 Class 都轉成字串防呆
                master_df = pd.read_csv(master_file, dtype=str)
                master_df.columns = master_df.columns.str.strip()
                # 確保必要欄位存在（對齊 GitHub 常見開源 DGL 欄位名）
                if 'UN Number' in master_df.columns and 'Class' in master_df.columns:
                    has_master = True
            except Exception as e:
                st.warning(f"⚠️ 官方總表 imdg_master.csv 讀取失敗，將跳過字典驗證。錯誤: {e}")

        if not has_master:
            st.warning("💡 提示：目前 GitHub 中尚未上傳有效的官方總表 `imdg_master.csv`。系統目前無法對手殘打錯的 UN 號碼進行防呆攔截，建議盡快補上檔案！")

        # 建立篩選介面
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 1. 請輸入 Class 類別 (必填)")
            input_class = st.text_input("Class", placeholder="例如: 1, 3, 5.1", label_visibility="collapsed").strip()
            
        with col2:
            st.markdown("### 2. 請輸入 UN 號碼 (選填)")
            input_un = st.text_input("UN Number", placeholder="例如: 1993, 3480", label_visibility="collapsed").strip()
            
        with col3:
            st.markdown("### 3. 選擇特定航商 (選填)")
            partner_options = ["全部航商"] + all_partners
            selected_partner = st.selectbox("Partner Filter", partner_options, label_visibility="collapsed")

        # 點擊查詢按鈕
        if st.button("開始查詢", type="primary", use_container_width=True):
            if not input_class:
                st.warning("⚠️ 請至少輸入 Class 類別再進行查詢！")
            else:
                # ==================== 🚨 第一關：官方字典防呆驗證 ====================
                is_valid_input = True
                if has_master and input_un:
                    # 檢查這份官方字典裡，有沒有這個 UN 號碼
                    un_exists = master_df[master_df['UN Number'] == input_un]
                    
                    if un_exists.empty:
                        st.error(f"❌ 嚴重警告：在最新 IMDG Code 官方危險品總表中，根本【查無此 UN 號碼：{input_un}】！")
                        st.error("🚨 訂艙人員極可能 key 錯資料打成不存在的號碼，請立即重新核對 MSDS，切勿直接放行！")
                        is_valid_input = False
                    else:
                        # 如果 UN 號碼存在，順便檢查他打的 Class 跟官方對不對得上 (支援模糊比對，如 2.1 對應 2)
                        official_classes = un_exists['Class'].tolist()
                        class_match = any(
                            input_class.startswith(c) or c.startswith(input_class) 
                            for c in official_classes
                        )
                        if not class_match:
                            st.error(f"❌ 警告：官方總表中 UN {input_un} 對應的合法 Class 為 `{official_classes}`。")
                            st.error(f"🚨 但您輸入的 Class 是 `{input_class}`，兩者完全對不上！請確認是否 key 錯欄位。")
                            is_valid_input = False

                # ==================== 第二關：航商黑名單比對 (過關才執行) ====================
                if is_valid_input:
                    st.markdown("---")
                    un_display = f"`{input_un}`" if input_un else "未填寫 (展開全類別)"
                    st.markdown(f"## 🔍 查詢結果 (Class: `{input_class}` / UN: {un_display} / 篩選: `{selected_partner}`)")
                    
                    search_targets = all_partners if selected_partner == "全部航商" else [selected_partner]
                    
                    for sheet_name in search_targets:
                        df = excel_sheets[sheet_name]
                        df.columns = df.columns.astype(str).str.strip()
                        
                        required_cols = ['UN號碼', 'Class', '狀態', '限制條件']
                        if any(col not in df.columns for col in required_cols):
                            st.error(f"⚠️ 航商分頁 `{sheet_name}` 格式不符，請確認是否包含：UN號碼、Class、狀態、限制條件")
                            continue
                        
                        df['Class'] = df['Class'].astype(str).str.strip()
                        df['UN號碼'] = df['UN號碼'].astype(str).str.strip()
                        df['狀態'] = df['狀態'].astype(str).str.strip()
                        df['限制條件'] = df['限制條件'].astype(str).str.strip()

                        match_class_df = df[
                            df['Class'].apply(lambda x: input_class.startswith(x) or x.startswith(input_class))
                        ]
                        
                        entries_to_show = []
                        
                        if match_class_df.empty:
                            entries_to_show.append({
                                "un": input_un if input_un else "該 Class 全品項",
                                "status": "🟢 正常收載",
                                "remark": "Excel 中無此 Class 任何禁收限制"
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
        st.error(f"❌ 讀取 檔案失敗。錯誤訊息: {e}")
