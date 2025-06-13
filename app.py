import streamlit as st
import pandas as pd
from database import BookDatabase # 确保导入的是 BookDatabase
import os
from datetime import datetime
import math

# 页面配置 (确保这是第一个Streamlit命令)
st.set_page_config(page_title="图书查询系统", layout="wide")

# 自定义CSS样式 (只定义和应用一次)
st.markdown("""
<style>
    /* 全局字体和背景 */
    body {
        font-family: 'Arial', sans-serif; /* 更现代的字体 */
        background-color: #f0f2f6; /* 淡雅的背景色 */
    }
    .stApp {
        background-color: #f0f2f6;
    }
    /* 标题样式 */
    h1 {
        color: #1e3a8a; /* 深蓝色标题 */
        text-align: center;
        padding-bottom: 20px;
        border-bottom: 2px solid #1e3a8a;
    }
    h2, h3 {
        color: #3b82f6; /* 亮蓝色副标题 */
    }
    /* 输入框和按钮样式 */
    .stTextInput input, .stNumberInput input {
        border-radius: 8px;
        border: 1px solid #d1d5db;
        padding: 10px;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    .stButton>button {
        border-radius: 8px;
        background-color: #2563eb; /* 鲜艳的按钮蓝色 */
        color: white;
        padding: 10px 20px;
        border: none;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #1d4ed8; /* 按钮悬停颜色加深 */
    }
    /* 表单和容器样式 */
    .stForm, .stDataFrame {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin-bottom: 20px;
    }
    /* DataFrame 样式 */
    .stDataFrame table {
        width: 100%;
        border-collapse: collapse;
    }
    .stDataFrame th {
        background-color: #e5e7eb; /* 表头背景色 */
        color: #1f2937; /* 表头文字颜色 */
        font-weight: bold;
        padding: 12px;
        text-align: left;
    }
    .stDataFrame td {
        padding: 10px;
        border-bottom: 1px solid #f3f4f6; /*单元格分割线*/
    }
    /* 分页控件样式 */
    .stCaption {
        text-align: center;
        color: #6b7280; /* 辅助文字颜色 */
        margin-top: 15px;
    }
    /* 优化查询条件区域布局 */
    div[data-testid="stForm"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        padding-right: 10px; /* 给列之间增加一些间距 */
    }
</style>
""", unsafe_allow_html=True)

# 获取当前文件所在的目录
DB_FILENAME = "bookCategory.csv"
try:
    current_dir = os.path.dirname(os.path.realpath(__file__))
    DB_PATH = os.path.join(current_dir, DB_FILENAME)
    if not os.path.exists(DB_PATH) and not os.path.isabs(DB_FILENAME):
        DB_PATH = os.path.join(os.getcwd(), DB_FILENAME)
except NameError:
    DB_PATH = os.path.join(os.getcwd(), DB_FILENAME)

db = BookDatabase(DB_PATH)
ITEMS_PER_PAGE = 15

def init_session_state():
    if 'query_conditions' not in st.session_state:
        st.session_state.query_conditions = {}
    if 'search_results' not in st.session_state:
        st.session_state.search_results = pd.DataFrame()
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
    if 'total_results' not in st.session_state:
        st.session_state.total_results = 0

def book_query_page():
    init_session_state()
    st.title("语言研究所资料室图书查询系统")

    with st.form("search_form"):
        st.subheader("图书搜索")
        book_name_search = st.text_input("书名", value=st.session_state.query_conditions.get('bookname',''))
        author_search = st.text_input("作者", value=st.session_state.query_conditions.get('author',''))
        publisher_search = st.text_input("出版社", value=st.session_state.query_conditions.get('publishdepartment',''))
        
        year_from_session = st.session_state.query_conditions.get('year')
        default_year_val = None
        if year_from_session:
            try:
                default_year_val = int(year_from_session)
            except ValueError:
                default_year_val = None

        publish_year_search = st.number_input(
            "出版年份 (例如: 2023)", 
            min_value=1000, 
            max_value=datetime.now().year + 5,
            step=1, 
            value=default_year_val,
            format="%d"
        )
        search_submitted = st.form_submit_button("查询")

    if search_submitted:
        st.session_state.query_conditions = {
            'bookname': book_name_search.strip(),
            'author': author_search.strip(),
            'publishdepartment': publisher_search.strip(),
            'year': str(publish_year_search).strip() if publish_year_search is not None else None 
        }
        st.session_state.current_page = 1 
    
    active_conditions = {
        k: v for k, v in st.session_state.query_conditions.items() 
        if v is not None and str(v).strip() != ''
    }

    if active_conditions:
        current_offset = (st.session_state.current_page - 1) * ITEMS_PER_PAGE
        results_df, total_count = db.search_books(
            active_conditions, 
            limit=ITEMS_PER_PAGE, 
            offset=current_offset
        )
        st.session_state.search_results = results_df
        st.session_state.total_results = total_count

        if not results_df.empty:
            st.subheader("查询结果")
            display_df = results_df.copy()
            
            # --- MODIFICATION START ---
            # 1. Set index to start from 1 for the current page
            # display_df.index = range(1, len(display_df) + 1) # This makes index per page start at 1

            # 2. For global continuous numbering:
            # Calculate the starting global index for the current page
            start_global_index = current_offset + 1
            # Create a new index Series for display
            display_df.index = pd.RangeIndex(start=start_global_index, stop=start_global_index + len(display_df))
            # Rename the index to '序号' for display
            display_df.index.name = "序号"
            # --- MODIFICATION END ---

            display_columns = ['bookorder', 'indexnumber', 'bookname', 'author', 'publishdepartment', 'price', 'publishdate']
            display_columns_present = [col for col in display_columns if col in display_df.columns]
            
            # To display the new '序号' index, we need to reset it into a column or st.dataframe will hide it by default if it's just the index.
            # However, st.dataframe has a feature to display the index. If we want it as the first column, we can do this:
            st.dataframe(display_df[display_columns_present], use_container_width=True) # The named index "序号" should now be displayed

            total_pages = math.ceil(st.session_state.total_results / ITEMS_PER_PAGE) if ITEMS_PER_PAGE > 0 and st.session_state.total_results > 0 else 1
            
            if st.session_state.total_results > 0 :
                st.caption(f"共 {st.session_state.total_results} 条记录，第 {st.session_state.current_page} / {total_pages} 页")
                
                nav_cols = st.columns([1, 1, 1, 1]) 
                
                with nav_cols[0]:
                    if st.button("首页", key="first_page_query", disabled=st.session_state.current_page == 1):
                        st.session_state.current_page = 1
                        st.rerun()
                with nav_cols[1]:
                    if st.button("上一页", key="prev_page_query", disabled=st.session_state.current_page == 1):
                        st.session_state.current_page -= 1
                        st.rerun()
                with nav_cols[2]:
                    if st.button("下一页", key="next_page_query", disabled=st.session_state.current_page == total_pages):
                        st.session_state.current_page += 1
                        st.rerun()
                with nav_cols[3]:
                    if st.button("末页", key="last_page_query", disabled=st.session_state.current_page == total_pages):
                        st.session_state.current_page = total_pages
                        st.rerun()
        elif st.session_state.total_results == 0 and active_conditions:
             st.info("没有找到符合条件的图书。")

    elif search_submitted and not active_conditions:
        st.warning("请输入至少一个查询条件。")
        st.session_state.search_results = pd.DataFrame()
        st.session_state.total_results = 0

def main():
    page_options = {"图书查询": book_query_page}
    page_options["图书查询"]()

if __name__ == "__main__":
    main()