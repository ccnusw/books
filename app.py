import streamlit as st
import pandas as pd
from database import BookDatabase
import os
from datetime import datetime
import math

# --- 页面配置 ---
st.set_page_config(
    page_title="图书查询系统",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 自定义CSS样式 ---
st.markdown("""
<style>
    body, .stApp {font-family: 'Roboto', 'Arial', sans-serif; background-color: #eef2f5;}
    h1 {color: #1a5276; text-align: center; padding-bottom: 25px; margin-bottom: 30px; font-weight: 600; letter-spacing: 1px;}
    h2, h3 {color: #2980b9;}
    .search-subheader {color: #34495e; border-bottom: 2px solid #aed6f1; padding-bottom: 10px; margin-bottom: 20px; font-size: 1.5em;}
    .results-subheader {color: #34495e; border-bottom: 2px solid #aed6f1; padding-bottom: 10px; margin-top: 30px; margin-bottom: 20px; font-size: 1.5em;}
    .stTextInput input, .stNumberInput input {border-radius: 6px; border: 1px solid #ced4da; padding: 12px 15px; box-shadow: inset 0 1px 2px rgba(0,0,0,0.075); font-size: 1em;}
    .stTextInput input:focus, .stNumberInput input:focus {border-color: #80bdff; box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25);}
    .stButton>button {border-radius: 6px; background-color: #007bff; color: white; padding: 10px 20px; border: none; box-shadow: 0 2px 5px rgba(0,0,0,0.15); transition: background-color 0.2s ease, transform 0.1s ease; font-weight: 500; font-size: 1em;}
    .stButton>button:hover {background-color: #0069d9; transform: translateY(-1px);}
    .stButton>button:active {background-color: #0056b3; transform: translateY(0px);}
    .stForm {background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.08); margin-bottom: 30px;}
    div[data-testid="stDataFrameResizable"] {background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.08);}
    .stDataFrame table {width: 100%; border-collapse: separate; border-spacing: 0; border: 1px solid #dee2e6; border-radius: 8px; overflow: hidden;}
    .stDataFrame th {background-color: #f8f9fa; color: #495057; font-weight: 600; padding: 14px 18px; text-align: left; border-bottom: 2px solid #007bff;}
    .stDataFrame td {padding: 12px 18px; border-bottom: 1px solid #e9ecef; color: #212529; vertical-align: middle;}
    .stDataFrame tr:last-child td {border-bottom: none;}
    .stDataFrame tr:hover td {background-color: #e9f5ff;}
    .stCaption {text-align: center; color: #5a6773; margin-top: 20px; font-size: 0.95em;}
    div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {padding-right: 15px;}
    div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child {padding-right: 0px;}
    .stAlert {border-radius: 6px; padding: 15px; font-size: 1em;}
    .stAlert strong {font-weight: 500;}

    /* --- 页脚样式 --- */
    .footer {
        margin-top: 60px;
        padding-top: 20px;
        border-top: 1px solid #dee2e6; /* 淡灰色横线 */
        text-align: center;
        color: #888; /* 页脚文字颜色 */
        font-size: 0.9em;
    }
    .footer p {
        margin-top: 4px;
        margin-bottom: 4px;
    }
    .footer a {
        color: #007bff; /* 链接颜色 */
        text-decoration: none;
    }
    .footer a:hover {
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)

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
    if 'query_conditions' not in st.session_state: st.session_state.query_conditions = {}
    if 'search_results' not in st.session_state: st.session_state.search_results = pd.DataFrame()
    if 'current_page' not in st.session_state: st.session_state.current_page = 1
    if 'total_results' not in st.session_state: st.session_state.total_results = 0

def book_query_page():
    init_session_state()
    st.markdown("<h1><span style='font-weight:300;'>语言研究所资料室</span><br>图书查询系统</h1>", unsafe_allow_html=True)

    with st.form("search_form"):
        st.markdown("<h2 class='search-subheader'>🔍 搜书导航</h2>", unsafe_allow_html=True)
        cols_inputs = st.columns([2, 2, 2, 1])
        with cols_inputs[0]: book_name_search = st.text_input("书名", value=st.session_state.query_conditions.get('bookname',''), placeholder="输入书名关键词...", key="book_name_input")
        with cols_inputs[1]: author_search = st.text_input("作者", value=st.session_state.query_conditions.get('author',''), placeholder="输入作者名...", key="author_input")
        with cols_inputs[2]: publisher_search = st.text_input("出版社", value=st.session_state.query_conditions.get('publishdepartment',''), placeholder="输入出版社名...", key="publisher_input")
        
        year_from_session = st.session_state.query_conditions.get('year')
        default_year_val = None
        if year_from_session:
            try: default_year_val = int(year_from_session)
            except (ValueError, TypeError): default_year_val = None

        with cols_inputs[3]: 
            publish_year_search = st.number_input(
                "出版年份", 
                min_value=1000, max_value=datetime.now().year + 5, 
                step=1, value=default_year_val, 
                format="%d", placeholder="YYYY", key="year_input"
            )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        spacer_ratio = 1.5 
        button_ratio = 1   
        gap_ratio = 0.1    

        cols_buttons = st.columns([spacer_ratio, button_ratio, gap_ratio, button_ratio, spacer_ratio]) 
        with cols_buttons[1]:
            search_submitted = st.form_submit_button("开始查询", use_container_width=True)
        with cols_buttons[3]:
            clear_submitted = st.form_submit_button("清空所有", use_container_width=True, type="secondary")

    if clear_submitted:
        st.session_state.query_conditions = {'bookname': '', 'author': '', 'publishdepartment': '', 'year': None}
        st.session_state.search_results = pd.DataFrame()
        st.session_state.total_results = 0
        st.session_state.current_page = 1
        st.rerun()

    if search_submitted:
        st.session_state.query_conditions = {'bookname': book_name_search.strip(), 'author': author_search.strip(), 'publishdepartment': publisher_search.strip(), 'year': str(publish_year_search).strip() if publish_year_search is not None else None}
        st.session_state.current_page = 1
    
    active_conditions = {k: v for k, v in st.session_state.query_conditions.items() if v is not None and str(v).strip() != ''}

    if active_conditions:
        current_offset = (st.session_state.current_page - 1) * ITEMS_PER_PAGE
        results_df, total_count = db.search_books(active_conditions, limit=ITEMS_PER_PAGE, offset=current_offset)
        st.session_state.search_results = results_df
        st.session_state.total_results = total_count

        if not results_df.empty:
            st.markdown("<h2 class='results-subheader'>📖 查询结果</h2>", unsafe_allow_html=True)
            display_df = results_df.copy()
            start_global_index = current_offset + 1
            display_df.index = pd.RangeIndex(start=start_global_index, stop=start_global_index + len(display_df))
            display_df.index.name = "序号"
            display_columns = ['bookorder', 'indexnumber', 'bookname', 'author', 'publishdepartment', 'price', 'publishdate']
            display_columns_present = [col for col in display_columns if col in display_df.columns]
            
            # 移除固定的高度设置，以防止页面出现主滚动条
            # 表格现在将根据需要拥有自己的内部滚动条
            st.dataframe(display_df[display_columns_present], use_container_width=True)
            
            total_pages = math.ceil(st.session_state.total_results / ITEMS_PER_PAGE) if ITEMS_PER_PAGE > 0 and st.session_state.total_results > 0 else 1
            
            if st.session_state.total_results > 0 and total_pages > 1:
                st.caption(f"共 {st.session_state.total_results} 条记录，当前显示第 {st.session_state.current_page} / {total_pages} 页")
                nav_cols = st.columns((1, 1, 0.2, 1, 1))
                with nav_cols[0]:
                    if st.button("⏪ 首页", key="app_first_page", disabled=st.session_state.current_page == 1, use_container_width=True):
                        st.session_state.current_page = 1; st.rerun()
                with nav_cols[1]:
                    if st.button("◀️ 上一页", key="app_prev_page", disabled=st.session_state.current_page == 1, use_container_width=True):
                        st.session_state.current_page -= 1; st.rerun()
                with nav_cols[3]:
                    if st.button("▶️ 下一页", key="app_next_page", disabled=st.session_state.current_page == total_pages, use_container_width=True):
                        st.session_state.current_page += 1; st.rerun()
                with nav_cols[4]:
                    if st.button("⏩ 末页", key="app_last_page", disabled=st.session_state.current_page == total_pages, use_container_width=True):
                        st.session_state.current_page = total_pages; st.rerun()
            elif st.session_state.total_results > 0:
                 st.caption(f"共 {st.session_state.total_results} 条记录")

        elif st.session_state.total_results == 0 and active_conditions:
             st.info("🤷‍♀️ 抱歉，没有找到符合条件的图书。请尝试调整查询条件。")
    elif (search_submitted and not active_conditions) and not clear_submitted : 
        st.warning("⚠️ 请至少输入一个查询条件后再试。")
        st.session_state.search_results = pd.DataFrame(); st.session_state.total_results = 0
    elif not clear_submitted: 
        st.info("💡 请输入查询条件以查找图书。例如，输入作者名或书名的一部分。")
    
    # --- 新增的页脚 ---
    st.markdown("""
    <div class="footer">
        <p>Copyright © 2025-长期 版权所有：华中师大语言研究所</p>
        <p>本检索系统由沈威制作，在使用中如果有任何问题可以发邮件至：<a href="mailto:sw@ccnu.edu.cn">sw@ccnu.edu.cn</a></p>
    </div>
    """, unsafe_allow_html=True)


def main():
    book_query_page()

if __name__ == "__main__":
    main()
