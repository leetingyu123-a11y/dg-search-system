import streamlit as st
import pandas as pd
import os

# 【已修正】設定網頁標題與版面寬度
st.set_page_config(page_title="各航商 DG 禁收清單查詢", layout="wide")

st.title("🚢 各航商 DG 禁收清單查詢")
st.caption("🔥 智能子項目版：支援 Class 子類別（如 1.1, 5.1）與特定 UN 號碼交叉判斷")

# 檢查檔案是否存在（優先檢查根目錄，再檢查子資料夾）
excel_file = "dg_list.xlsx"
if not os.path.exists(excel_file):
    excel_file = os.path.join("DG_System", "dg_list.xlsx")

if not os.path.exists(excel_file):
    st.error("❌ 找不到 dg_list.xlsx 檔案！請確認 Excel 檔案是否跟程式放在同一個倉庫或資料夾中。")
else:
    # 讀取資料庫，將所有關鍵欄位轉成文字以利精準比對
    df = pd.read_excel(excel_file)
    df['Class'] = df['Class'].astype(str).str.strip()
    df['UN'] = df['UN'].astype(str).str.strip()
    df['Is_Absolute_Prohibited'] = df['Is_Absolute_Prohibited'].astype(str).str.upper().str.strip()

    # 欄位輸入介面
    st.markdown("### 1. 請輸入 Class 類別 (例如: 1, 1.1, 3, 5.1)")
    input_class = st.text_input("Class", label_visibility="collapsed").strip()

    st.markdown("### 2. 請輸入 UN 號碼 (例如: 1993, 3480)")
    input_un = st.text_input("UN Number", label_visibility="collapsed").strip()

    if st.button("開始查詢", type="primary"):
        if not input_class or not input_un:
            st.warning("⚠️ 請同時輸入 Class 和 UN 號碼再進行查詢！")
        else:
            st.markdown("---")
            st.markdown(f"### 🔍 查詢結果 (Class: `{input_class}` / UN: `{input_un}`)")
            
            # 找出 Excel 中所有不重複的航商
            partners = df['Partner'].unique()
            
            # 用於建立結果表格的清單
            result_data = []
            
            for partner in partners:
                # 篩選出該航商的資料
                partner_df = df[df['Partner'] == partner]
                
                # 【核心邏輯升級】：支援子項目模糊比對
                # 確保不論使用者輸入 "1" 還是 "1.1"，只要彼此開頭吻合就能成功對齊
                match_class_df = partner_df[
                    partner_df['Class'].apply(lambda x: input_class.startswith(x) or x.startswith(input_class))
                ]
                
                if match_class_df.empty:
                    # 如果連大類別或子類別都沒對到，代表該航商無此限制
                    status = "🟢 正常收載"
                    remarks = "Excel 中無此 Class 禁收限制"
                else:
                    # 1. 優先檢查是否有該 Class 類別的「絕對禁收 (ALL)」
                    absolute_row = match_class_df[
                        (match_class_df['UN'].str.upper() == 'ALL') & 
                        (match_class_df['Is_Absolute_Prohibited'] == 'TRUE')
                    ]
                    
                    if not absolute_row.empty:
                        status = "🔴 絕對禁收"
                        remarks = absolute_row.iloc[0]['Remarks']
                    else:
                        # 2. 如果不是絕對禁收，檢查輸入的 UN 號碼是否有在黑名單清單內
                        un_match = False
                        un_remarks = ""
                        
                        for _, row in match_class_df.iterrows():
                            # 將 Excel 裡用逗號或空格隔開的 UN 號碼拆開成獨立清單
                            un_list = [u.strip() for u in row['UN'].replace(',', ' ').split()]
                            if input_un in un_list:
                                un_match = True
                                un_remarks = row['Remarks']
                                break
                        
                        if un_match:
                            status = "🔴 特定UN禁收"
                            remarks = un_remarks
                        else:
                            status = "🟢 正常收載"
                            # 拿該類別第一個條款當作提醒（例如長榮的 5.1 條款需文件審查）
                            remarks = match_class_df.iloc[0]['Remarks'] if pd.notna(match_class_df.iloc[0]['Remarks']) else "無特殊限制"
                
                result_data.append({
                    "航商 (Partner)": partner,
                    "收載狀態": status,
                    "航商備註 / 限制條件": remarks
                })
            
            # 轉換為 DataFrame 格式
            result_df = pd.DataFrame(result_data)
            
            # 根據收載狀態給予漂亮的顏色高亮（禁收紅色，正常綠色）
            def highlight_status(val):
                if "🔴" in val:
                    return 'background-color: #ffcccc; color: #cc0000; font-weight: bold;'
                return 'background-color: #d4edda; color: #155724;'

            # 輸出美化後的表格
            st.dataframe(
                result_df.style.applymap(highlight_status, subset=['收載狀態']),
                use_container_width=True,
                hide_index=True
            )
