import streamlit as st
import pandas as pd
import os

st.set_page_index_config(page_title="各航商 DG 禁收清單查詢", layout="wide")
st.title("🚢 各航商 DG 禁收清單查詢")
st.caption("🔥 優先判斷 Class 大原則 ➡️ 通過後才判斷特定 UN 號碼")

# 檢查檔案是否存在
excel_file = "dg_list.xlsx"
if not os.path.exists(excel_file):
    # 彈性檢查子資料夾路徑
    excel_file = os.path.join("DG_System", "dg_list.xlsx")

if not os.path.exists(excel_file):
    st.error(f"❌ 找不到 dg_list.xlsx 檔案！請確認 Excel 檔案是否跟程式放在同一個資料夾。")
else:
    # 讀取資料庫，將所有欄位轉成文字以利比對
    df = pd.read_excel(excel_file)
    df['Class'] = df['Class'].astype(str).str.strip()
    df['UN'] = df['UN'].astype(str).str.strip()
    df['Is_Absolute_Prohibited'] = df['Is_Absolute_Prohibited'].astype(str).str.upper().str.strip()

    # 欄位輸入
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
            
            # 找出所有不重複的航商
            partners = df['Partner'].unique()
            
            # 用建立表格的方式呈現結果
            result_data = []
            
            for partner in partners:
                # 篩選該航商的資料
                partner_df = df[df['Partner'] == partner]
                
                # 【核心邏輯升級】：支援子項目比對
                # 如果使用者輸入 1.1，會去對抗 Excel 裡的 "1" 或 "1.1"
                # 如果使用者輸入 1，會去對抗 Excel 裡的 "1" 或 "1.1"、"1.2" 等只要是 1 開頭的
                match_class_df = partner_df[
                    partner_df['Class'].apply(lambda x: input_class.startswith(x) or x.startswith(input_class))
                ]
                
                if match_class_df.empty:
                    # 如果連大類別都沒對到，預設為可收
                    status = "🟢 正常收載"
                    remarks = "Excel 中無此 Class 禁收限制"
                else:
                    # 檢查是否有該類別的「絕對禁收 (ALL)」
                    absolute_row = match_class_df[
                        (match_class_df['UN'].str.upper() == 'ALL') & 
                        (match_class_df['Is_Absolute_Prohibited'] == 'TRUE')
                    ]
                    
                    if not absolute_row.empty:
                        status = "🔴 絕對禁收"
                        remarks = absolute_row.iloc[0]['Remarks']
                    else:
                        # 如果不是絕對禁收，檢查特定 UN 號碼是否有在黑名單內
                        un_match = False
                        un_remarks = ""
                        
                        for _, row in match_class_df.iterrows():
                            # 將 Excel 裡的 UN 欄位用逗號或空格拆開成清單
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
                            # 拿該類別第一個備註當作提醒（例如：特殊文件審查等）
                            remarks = match_class_df.iloc[0]['Remarks'] if pd.notna(match_class_df.iloc[0]['Remarks']) else "無特殊限制"
                
                result_data.append({
                    "航商 (Partner)": partner,
                    "收載狀態": status,
                    "航商備註 / 限制條件": remarks
                })
            
            # 轉成 Dataframe 並美化輸出
            result_df = pd.DataFrame(result_data)
            
            # 根據狀態給予顏色高亮
            def highlight_status(val):
                if "🔴" in val:
                    return 'background-color: #ffcccc; color: #cc0000; font-weight: bold;'
                return 'background-color: #d4edda; color: #155724;'

            st.dataframe(
                result_df.style.applymap(highlight_status, subset=['收載狀態']),
                use_container_width=True,
                hide_index=True
            )
