import streamlit as st
import pandas as pd
import os

# 設定網頁標題與寬度版面
st.set_page_config(page_title="各航商 DG 禁收清單查詢", layout="wide")

st.title("🚢 各航商 DG 禁收清單查詢")
st.caption("🔥 智能分頁版：自動讀取 Excel 每個工作頁名稱作為航商 (Partner)")

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
        
        # 網頁輸入介面
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
                
                result_data = []
                
                # 依序讀取每一個工作頁
                for sheet_name, df in excel_sheets.items():
                    # 排除 Excel 預設的空白頁
                    if sheet_name.startswith("Sheet") and df.empty:
                        continue
                        
                    # 移除欄位名稱的前後空格
                    df.columns = df.columns.astype(str).str.strip()
                    
                    # 檢查該分頁必備欄位
                    required_cols = ['UN號碼', 'Class', '狀態', '限制條件']
                    missing_cols = [col for col in required_cols if col not in df.columns]
                    
                    if missing_cols:
                        result_data.append({
                            "航商 (Partner)": sheet_name,
                            "收載狀態": "⚠️ 格式錯誤",
                            "航商備註 / 限制條件": f"此分頁遺失欄位: {missing_cols}，請修正 Excel 標題"
                        })
                        continue
                    
                    # 資料清洗與型態轉換
                    df['Class'] = df['Class'].astype(str).str.strip()
                    df['UN號碼'] = df['UN號碼'].astype(str).str.strip()
                    df['狀態'] = df['狀態'].astype(str).str.strip()
                    df['限制條件'] = df['限制條件'].astype(str).str.strip()

                    # 支援 Class 子項目模糊比對
                    match_class_df = df[
                        df['Class'].apply(lambda x: input_class.startswith(x) or x.startswith(input_class))
                    ]
                    
                    if match_class_df.empty:
                        status = "🟢 正常收載"
                        remarks = "Excel 中無此 Class 禁收限制"
                    else:
                        # 1. 先判定該 Class 是否為「絕對禁收」
                        absolute_row = match_class_df[
                            (match_class_df['UN號碼'].str.upper() == 'ALL') & 
                            (match_class_df['狀態'].str.contains('絕對禁收'))
                        ]
                        
                        if not absolute_row.empty:
                            status = "🔴 絕對禁收"
                            remarks = absolute_row.iloc[0]['限制條件']
                        else:
                            # 2. 如果不是絕對禁收，拆解特定 UN 號碼進行交叉比對
                            un_match = False
                            un_remarks = ""
                            
                            for _, row in match_class_df.iterrows():
                                un_list = [u.strip() for u in row['UN號碼'].replace(',', ' ').split()]
                                if input_un in un_list:
                                    un_match = True
                                    un_remarks = row['限制條件']
                                    break
                            
                            if un_match:
                                status = "🔴 特定UN禁收"
                                remarks = un_remarks
                            else:
                                status = "🟢 正常收載"
                                remarks = match_class_df.iloc[0]['限制條件'] if pd.notna(match_class_df.iloc[0]['限制條件']) else "無特殊限制"
                    
                    result_data.append({
                        "航商 (Partner)": sheet_name,
                        "收載狀態": status,
                        "航商備註 / 限制條件": remarks
                    })
                
                # 打包成表格輸出
                if result_data:
                    result_df = pd.DataFrame(result_data)
                    
                    def highlight_status(val):
                        if "🔴" in val:
                            return 'background-color: #ffcccc; color: #cc0000; font-weight: bold;'
                        elif "⚠️" in val:
                            return 'background-color: #fff3cd; color: #856404;'
                        return 'background-color: #d4edda; color: #155724;'

                    st.dataframe(
                        result_df.style.applymap(highlight_status, subset=['收載狀態']),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("💡 目前 Excel 中沒有建立任何有效的航商分頁。")
                    
    except Exception as e:
        st.error(f"❌ 讀取 Excel 失敗，請確認檔案是否損壞。錯誤訊息: {e}")
