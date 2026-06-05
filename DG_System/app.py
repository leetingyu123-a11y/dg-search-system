import pandas as pd
import streamlit as st

st.set_page_config(page_title="航商 DG 查詢系統", layout="centered")
st.title("🚢 各航商 DG 禁收清單查詢")
st.caption("🔥 終極防呆版：優先判斷 Class 大原則 ➡️ 通過後才判斷特定 UN 號碼")

# 讓使用者輸入
search_class = st.text_input("1. 請輸入 Class 類別 (例如: 1, 3, 5.1):").strip()
search_un = st.text_input("2. 請輸入 UN 號碼 (例如: 1993, 3480):").strip()

if st.button("開始查詢", type="primary"):
    if not search_class:
        st.warning("請務必輸入【Class 類別】（因為系統需要先進行 Class 判定）！")
    else:
        try:
            excel_file = "dg_list.xlsx"
            results = []

            # 自動讀取 Excel 裡所有的工作表 (各家船公司)
            all_sheets = pd.read_excel(excel_file, sheet_name=None)

            for ocean_carrier, df in all_sheets.items():
                # 確保欄位名稱乾淨
                df.columns = df.columns.str.strip()

                # 【核心防呆】把所有欄位轉換成純文字字串，並去掉所有隱藏空格
                df["Class"] = (
                    df["Class"]
                    .astype(str)
                    .str.replace(r"\.0$", "", regex=True)
                    .str.strip()
                )
                df["UN號碼"] = df["UN號碼"].astype(str).str.strip()
                df["狀態"] = df["狀態"].astype(str).str.strip()
                df["限制條件"] = df["限制條件"].astype(str).str.strip()

                # 使用者輸入的 Class 也做標準化
                target_class = str(search_class).replace(".0", "").strip()

                # 預設放行狀態
                status = "🟢 正常申報"
                remark = "該航商清單未特別限制，依 IMDG 國際危規辦理。"

                # ==========================================
                # 【第一步：嚴格檢查 Class 大原則】
                # ==========================================
                # 尋找有沒有「Class 相同」且「UN號碼包含 所有/ALL」的整類禁收規則
                class_block = df[
                    (df["Class"] == target_class)
                    & (df["UN號碼"].str.contains("所有|ALL|all", na=False))
                ]

                if not class_block.empty:
                    # 如果找到了 Class 的全面禁收大原則，直接判定！
                    status = class_block.iloc[0]["狀態"]
                    remark = class_block.iloc[0]["限制條件"]

                # ==========================================
                # 【第二步：Class 通過，才檢查特定 UN 號碼】
                # ==========================================
                else:
                    if search_un:
                        target_un = str(search_un).strip()
                        # 在該 Class 內，尋找有沒有包含這個特定 UN 號碼的「點名限制」
                        un_match = df[
                            (df["Class"] == target_class)
                            & (df["UN號碼"].str.contains(target_un, na=False))
                        ]
                        if not un_match.empty:
                            status = un_match.iloc[0]["狀態"]
                            remark = un_match.iloc[0]["限制條件"]

                # 收集這家船公司的結果
                results.append(
                    {
                        "船公司": ocean_carrier,
                        "檢查結果": status,
                        "備註說明": remark,
                    }
                )

            # 把最終對照結果用漂亮的表格秀在網頁上
            res_df = pd.DataFrame(results)
            st.write("### 🔍 查詢結果對照表")
            st.dataframe(res_df, use_container_width=True)

        except FileNotFoundError:
            st.error(
                "找不到 dg_list.xlsx 檔案！請確認 Excel 檔案是否跟程式放在同一個資料夾。"
            )