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
st.caption("🔥 完美改版：支援單查 Class 彈性判定 ＆ 備註大字體完整展開卡片")

# 檢查路徑與檔案
excel_file = "dg_list.xlsx"
if not os.path.exists(excel_file):
    excel_file = os.path.join("DG_System", "dg_list.xlsx")

if not os.path.exists(excel_file):
    st.error("❌ 找不到 dg_list.xlsx 檔案！請確認 Excel 檔案是否已經上傳至 GitHub。")
else:
    try:
        # 讀取 Excel 的所有工作頁 (Sheet)
        excel_sheets = pd.read_excel(excel_file, sheet_name=None)
        
        # 撈出所有可用的航商清單
        all_partners = [sheet for sheet in excel_sheets.keys() if not (sheet.startswith("Sheet") and excel_sheets[sheet].empty)]
        
        # 建立篩選介面
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 1. 請輸入 Class 類別 (必填)")
            input_class = st.text_input("Class", placeholder="例如: 1, 3, 5.1", label_visibility="collapsed").strip()
            
        with col2:
            st.markdown("### 2. 請輸入 UN 號碼 (選填)")
            input_un = st.text_input("UN Number", placeholder="留空則查詢整個 Class 規則", label_visibility="collapsed").strip()
            
        with col3:
            st.markdown("### 3. 選擇特定航商 (選填)")
            partner_options = ["全部航商"] + all_partners
            selected_partner = st.selectbox("Partner Filter", partner_options, label_visibility="collapsed")

        # 點擊查詢按鈕
        if st.button("開始查詢", type="primary", use_container_width=True):
            if not input_class:
                st.warning("⚠️ 請至少輸入 Class 類別再進行查詢！")
            else:
                st.markdown("---")
                un_display = f"`{input_un}`" if input_un else "未填寫 (展開全類別)"
                st.markdown(f"## 🔍 查詢結果 (Class: `{input_class}` / UN: {un_display} / 篩選: `{selected_partner}`)")
                
                # 決定這次要查詢哪些航商
                search_targets = all_partners if selected_partner == "全部航商" else [selected_partner]
                
                # 依序讀取目標航商的工作頁
                for sheet_name in search_targets:
                    df = excel_sheets[sheet_name]
                    df.columns = df.columns.astype(str).str.strip()
                    
                    # 檢查基本欄位
                    required_cols = ['UN號碼', 'Class', '狀態', '限制條件']
                    if any(col not in df.columns for col in required_cols):
                        st.error(f"⚠️ 航商分頁 `{sheet_name}` 格式不符，請確認是否包含：UN號碼、Class、狀態、限制條件")
                        continue
                    
                    # 資料清洗
                    df['Class'] = df['Class'].astype(str).str.strip()
                    df['UN號碼'] = df['UN號碼'].astype(str).str.strip()
                    df['狀態'] = df['狀態'].astype(str).str.strip()
                    df['限制條件'] = df['限制條件'].astype(str).str.strip()

                    # 篩選符合 Class 的資料
                    match_class_df = df[
                        df['Class'].apply(lambda x: input_class.startswith(x) or x.startswith(input_class))
                    ]
                    
                    entries_to_show = []
                    
                    if match_class_df.empty:
                        # 如果完全沒設定該 Class 的規則
                        entries_to_show.append({
                            "un": input_un if input_un else "該 Class 全品項",
                            "status": "🟢 正常收載",
                            "remark": "Excel 中無此 Class 任何禁收限制"
                        })
                    else:
                        # 💡 核心修正邏輯：如果使用者「沒有填寫 UN 號碼」
                        if not input_un:
                            # 直接把該 Class 在 Excel 裡登記的所有行通通抓出來秀給使用者看
                            for _, row in match_class_df.iterrows():
                                entries_to_show.append({
                                    "un": row['UN號碼'],
                                    "status": row['狀態'],
                                    "remark": row['限制條件']
                                })
                        else:
                            # 💡 如果有填寫 UN 號碼，執行精準交叉比對
                            # 1. 檢查有無設 ALL 絕對禁收
                            absolute_row = match_class_df[
                                (match_class_df['UN號碼'].str.upper() == 'ALL') & 
                                (match_class_df['狀態'].str.contains('絕對禁收'))
                            ]
                            
                            if not absolute_row.empty:
                                entries_to_show.append({"un": "ALL", "status": "🔴 絕對禁收", "remark": absolute_row.iloc[0]['限制條件']})
                            else:
                                # 2. 精準找有沒有完全等於輸入的 UN 號碼（可能有多行！）
                                exact_un_match = match_class_df[match_class_df['UN號碼'] == input_un]
                                
                                if not exact_un_match.empty:
                                    for _, row in exact_un_match.iterrows():
                                        entries_to_show.append({"un": row['UN號碼'], "status": row['狀態'], "remark": row['限制條件']})
                                else:
                                    # 3. 如果沒有精準符合的 UN，再找看看有沒有 Class 通用提示 (ALL)
                                    all_property_row = match_class_df[match_class_df['UN號碼'].str.upper() == 'ALL']
                                    if not all_property_row.empty:
                                        for _, row in all_property_row.iterrows():
                                            entries_to_show.append({"un": "ALL (通用條款)", "status": row['狀態'], "remark": row['限制條件']})
                                    else:
                                        entries_to_show.append({"un": input_un, "status": "🟢 正常收載", "remark": "無特殊禁收限制"})

                    # --- 🎨 渲染精美大卡片 ---
                    for entry in entries_to_show:
                        status = entry['status']
                        if "🔴" in status:
                            border_color = "#ef4444"
                            bg_badge = "#fee2e2"
                            text_badge = "#991b1b"
                        elif "🟡" in status or "特定" in status or "注意" in status:
                            border_color = "#f59e0b"
                            bg_badge = "#fef3c7"
                            text_badge = "#92400e"
                        else:
                            border_color = "#10b981"
                            bg_badge = "#d1fae5"
                            text_badge = "#065f46"
                        
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
        st.error(f"❌ 讀取 Excel 失敗，請確認檔案。錯誤訊息: {e}")
