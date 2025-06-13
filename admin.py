import streamlit as st
import pandas as pd
from database import BookDatabase # Uses the new CSV-based BookDatabase
import os
from datetime import datetime
import math

# --- 页面配置 ---
st.set_page_config(
    page_title="图书管理后台",
    page_icon="📚",  # Favicon
    layout="wide",
    initial_sidebar_state="expanded" # Keep sidebar open initially for login
)

# --- 自定义CSS样式 ---
st.markdown("""
<style>
    /* 全局字体和背景 */
    body, .stApp {
        font-family: 'Roboto', 'Arial', sans-serif; /* 现代、清晰的字体 */
        background-color: #f4f6f8; /* 后台常用的淡灰色背景 */
    }

    /* 标题样式 */
    h1, h2, h3, h4, h5, h6 {
        color: #2c3e50; /* 深灰蓝，更沉稳 */
    }
    h1 { /* 主标题 */
        text-align: center;
        padding-bottom: 20px;
        border-bottom: 3px solid #3498db; /* 蓝色强调线 */
        margin-bottom: 30px;
    }
    h2 { /* 副标题/操作区域标题 */
        color: #3498db; /* 主题蓝 */
        border-left: 5px solid #3498db;
        padding-left: 10px;
        margin-top: 40px;
        margin-bottom: 20px;
    }

    /* 输入框和按钮样式 */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox div[data-baseweb="select"] > div {
        border-radius: 6px;
        border: 1px solid #bdc3c7; /* 浅灰色边框 */
        padding: 10px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #3498db;
        box-shadow: 0 0 0 0.2rem rgba(52, 152, 219, 0.25);
    }

    .stButton>button {
        border-radius: 6px;
        background-color: #3498db; /* 主题蓝 */
        color: white;
        padding: 10px 24px;
        border: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: background-color 0.2s ease, transform 0.1s ease;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #2980b9; /* 悬停时加深 */
        transform: translateY(-1px);
    }
    .stButton>button:active {
        background-color: #2573a7;
        transform: translateY(0px);
    }
    .stButton>button[kind="secondary"] { /* Streamlit 1.18+ secondary button */
        background-color: #e0e0e0;
        color: #333;
    }
     .stButton>button[kind="secondary"]:hover {
        background-color: #d0d0d0;
    }


    /* 表单和容器样式 */
    .stForm, div[data-testid="stExpander"] { /* Expander and Form styling */
        background-color: #ffffff; /* 白色背景 */
        padding: 25px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08); /* 更柔和的阴影 */
        margin-bottom: 25px;
    }
    div[data-testid="stExpander"] summary { /* Expander header */
        font-size: 1.1em;
        font-weight: 500;
        color: #2c3e50;
    }


    /* DataFrame 样式 */
    .stDataFrame table {
        width: 100%;
        border-collapse: separate; /* Allows for border-radius on cells */
        border-spacing: 0;
        border: 1px solid #dfe6e9; /* 表格外边框 */
        border-radius: 6px;
        overflow: hidden; /* For border-radius to apply correctly */
    }
    .stDataFrame th {
        background-color: #e9ecef; /* 更淡的表头背景 */
        color: #495057; /* 表头文字颜色 */
        font-weight: 600; /* 加粗 */
        padding: 12px 15px;
        text-align: left;
        border-bottom: 2px solid #3498db; /* 蓝色下边框 */
    }
    .stDataFrame td {
        padding: 10px 15px;
        border-bottom: 1px solid #f1f3f5; /* 更细的单元格分割线 */
        color: #34495e;
    }
    .stDataFrame tr:last-child td {
        border-bottom: none; /*移除最后一行分割线*/
    }
    .stDataFrame tr:hover td {
        background-color: #f8f9fa; /* 悬停行高亮 */
    }

    /* 登录区域美化 */
    div[data-testid="stSidebarNav"] + div[data-testid="stVerticalBlock"] { /* Target login form in sidebar */
        background-color: #ffffff;
        padding: 20px;
        border-radius: 8px;
        margin: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    div[data-testid="stSidebarNav"] + div[data-testid="stVerticalBlock"] h2, /* Sidebar Header */
    div[data-testid="stSidebarNav"] + div[data-testid="stVerticalBlock"] .stMarkdown p { /* For st.sidebar.header */
        color: #2c3e50 !important;
    }


    /* 页面元素间距 */
    .stAlert { /* Alerts (success, error, info, warning) */
        border-radius: 6px;
        padding: 15px;
        font-size: 0.95em;
    }

</style>
""", unsafe_allow_html=True)


# --- 全局变量和数据库初始化 ---
DB_FILENAME = "bookCategory.csv"
try:
    current_dir = os.path.dirname(os.path.realpath(__file__))
    DB_PATH = os.path.join(current_dir, DB_FILENAME)
    if not os.path.exists(DB_PATH) and not os.path.isabs(DB_FILENAME):
        DB_PATH = os.path.join(os.getcwd(), DB_FILENAME)
except NameError:
    DB_PATH = os.path.join(os.getcwd(), DB_FILENAME)

db = BookDatabase(DB_PATH)
ITEMS_PER_PAGE = 10 

st.title("📚 图书管理后台")

if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False
if 'login_error_message' not in st.session_state:
    st.session_state.login_error_message = ""
if 'add_book_success' not in st.session_state:
    st.session_state.add_book_success = False
if 'add_book_message' not in st.session_state:
    st.session_state.add_book_message = ""

def display_admin_login():
    with st.container():
        st.markdown("<br><br>", unsafe_allow_html=True) 
        cols_login = st.columns([1, 1.5, 1]) 
        with cols_login[1]: 
            with st.form("login_form_main"):
                st.markdown("<h2 style='text-align: center; color: #3498db;'>管理员登录</h2>", unsafe_allow_html=True)
                username = st.text_input("👤 用户名", value="admin", disabled=True) 
                password = st.text_input("🔑 密码", type="password", key="admin_password_input_admin_page")
                login_button = st.form_submit_button("登录", use_container_width=True)
                if login_button:
                    if password == "xm@8287": 
                        st.session_state.admin_logged_in = True
                        st.session_state.login_error_message = "" 
                        st.balloons() 
                        st.success("登录成功！正在进入管理界面...")
                        st.rerun() 
                    else:
                        st.session_state.login_error_message = "密码错误，请重试。"
                        st.rerun() 
            if st.session_state.login_error_message: 
                st.error(st.session_state.login_error_message)
                st.session_state.login_error_message = "" 
        st.markdown("<br><br>", unsafe_allow_html=True)

def pagination_controls(total_items, current_page_session_key, key_suffix=""):
    total_pages = math.ceil(total_items / ITEMS_PER_PAGE) if ITEMS_PER_PAGE > 0 else 1
    total_pages = max(1, total_pages)
    current_page_val = st.session_state.get(current_page_session_key, 1)
    current_page_val = min(current_page_val, total_pages)
    st.session_state[current_page_session_key] = current_page_val
    if total_pages <= 1 and total_items <= ITEMS_PER_PAGE :
        if total_items > 0: st.caption(f"共 {total_items} 条记录")
        return current_page_val
    nav_cols = st.columns((1, 1, 1, 1, 0.5, 1.5, 0.7)) 
    if nav_cols[0].button("首页", key=f"first_{key_suffix}_admin", disabled=(current_page_val == 1), use_container_width=True):
        st.session_state[current_page_session_key] = 1; st.rerun()
    if nav_cols[1].button("上一页", key=f"prev_{key_suffix}_admin", disabled=(current_page_val == 1), use_container_width=True):
        st.session_state[current_page_session_key] -= 1; st.rerun()
    if nav_cols[2].button("下一页", key=f"next_{key_suffix}_admin", disabled=(current_page_val == total_pages), use_container_width=True):
        st.session_state[current_page_session_key] += 1; st.rerun()
    if nav_cols[3].button("末页", key=f"last_{key_suffix}_admin", disabled=(current_page_val == total_pages), use_container_width=True):
        st.session_state[current_page_session_key] = total_pages; st.rerun()
    nav_cols[4].markdown(f"<p style='text-align:right; margin-top:8px; color:#555;'>跳至</p>", unsafe_allow_html=True)
    jump_to_page = nav_cols[5].number_input("页码", min_value=1, max_value=total_pages, value=current_page_val, step=1, key=f"jump_{key_suffix}_admin", label_visibility="collapsed")
    if nav_cols[6].button("跳转", key=f"jump_btn_{key_suffix}_admin", use_container_width=True):
        st.session_state[current_page_session_key] = jump_to_page; st.rerun()
    st.caption(f"当前第 {current_page_val} 页 / 共 {total_pages} 页 (共 {total_items} 条记录)")
    return current_page_val

def admin_operations_page():
    with st.sidebar:
        st.markdown("---"); st.markdown(f"### 欢迎, 管理员! 👋")
        if st.button("退出登录", key="admin_logout_btn_admin_page", use_container_width=True, type="secondary"):
            st.session_state.admin_logged_in = False
            keys_to_clear_admin = ['admin_logged_in', 'browse_current_page_admin', 'add_book_success', 'add_book_message']
            for key in keys_to_clear_admin:
                if key in st.session_state: del st.session_state[key]
            st.rerun()
        st.markdown("---"); st.info("请在下方选择操作。")

    st.header("⚙️ 管理员控制面板")
    tab1, tab2 = st.tabs(["📊 浏览和管理图书", "➕ 添加新图书"])

    with tab1:
        st.subheader("所有图书概览")
        if 'browse_current_page_admin' not in st.session_state: st.session_state.browse_current_page_admin = 1
        current_offset = (st.session_state.browse_current_page_admin - 1) * ITEMS_PER_PAGE
        all_books_df, total_books = db.get_all_books(limit=ITEMS_PER_PAGE, offset=current_offset)
        if not all_books_df.empty:
            start_global_index = current_offset + 1
            display_df_browse = all_books_df.copy()
            display_df_browse.index = pd.RangeIndex(start=start_global_index, stop=start_global_index + len(display_df_browse))
            display_df_browse.index.name = "序号"
            
            # --- MODIFICATION: Removed 'id' from the list of columns to display ---
            display_cols_browse = ['bookorder', 'indexnumber', 'bookname', 'author', 'publishdepartment', 'price', 'publishdate']
            # --- END OF MODIFICATION ---
            
            display_cols_browse_present = [col for col in display_cols_browse if col in display_df_browse.columns]
            st.dataframe(display_df_browse[display_cols_browse_present], use_container_width=True)
            pagination_controls(total_books, 'browse_current_page_admin', key_suffix="browse_admin")
        else: st.info("ℹ️ 数据库中当前没有图书记录。")

    with tab2:
        st.subheader("添加一本新书")
        if st.session_state.add_book_message:
            if st.session_state.add_book_success: st.success(st.session_state.add_book_message)
            else: st.error(st.session_state.add_book_message)
            st.session_state.add_book_message = "" 
        with st.form("add_book_form_admin", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                book_order = st.text_input("图书编号 (Book Order) *", key="add_bo_admin_v2", placeholder="例如: A001-2023")
                index_number = st.text_input("书目索引号 (Index No.) *", key="add_in_admin_v2", placeholder="例如: TP312/L45")
                book_name = st.text_input("书名 (Title) *", key="add_bn_admin_v2", placeholder="例如: Python编程从入门到实践")
                author = st.text_input("作者 (Author) *", key="add_au_admin_v2", placeholder="例如: 张三")
            with col2:
                publisher = st.text_input("出版社 (Publisher) *", key="add_pd_admin_v2", placeholder="例如: 人民邮电出版社")
                price_val = st.number_input("价格 (Price)", min_value=0.0, value=None, format="%.2f", key="add_pr_admin_v2", help="留空则为无价格信息")
                date_col1, date_col2 = st.columns(2)
                with date_col1: publish_year = st.number_input("出版年份 (Year)", min_value=1000, max_value=datetime.now().year + 10, step=1, value=None, format="%d", key="add_py_admin_v2", placeholder="YYYY")
                with date_col2: publish_month = st.number_input("出版月份 (Month)", min_value=1, max_value=12, step=1, value=None, format="%d", key="add_pm_admin_v2", placeholder="MM")
            st.markdown("带有 * 号的为必填项。")
            submitted_add = st.form_submit_button("✔️ 确认添加图书", use_container_width=True)
            if submitted_add:
                st.session_state.add_book_success = False 
                required_fields_map = {"图书编号": book_order, "书目索引号": index_number, "书名": book_name, "作者": author, "出版社": publisher}
                empty_fields = [k for k, v in required_fields_map.items() if not str(v).strip()]
                if (publish_year is not None and publish_month is None) or (publish_year is None and publish_month is not None):
                    st.session_state.add_book_message = "⚠️ 若要填写出版日期，年份和月份必须同时填写或都留空。"
                elif empty_fields:
                    st.session_state.add_book_message = f"⚠️ 以下必填字段不能为空：{', '.join(empty_fields)}"
                else:
                    book_data = {"bookorder": book_order.strip(), "indexnumber": index_number.strip(), "bookname": book_name.strip(), "author": author.strip(), "publishdepartment": publisher.strip(), "price": price_val, "year": int(publish_year) if publish_year is not None else None, "month": int(publish_month) if publish_month is not None else None}
                    try:
                        db.add_book(book_data)
                        st.session_state.add_book_success = True
                        st.session_state.add_book_message = f"🎉 图书《{book_name.strip()}》添加成功！"
                    except ValueError as ve: st.session_state.add_book_message = f"🚫 添加失败：{ve}"
                    except Exception as e: st.session_state.add_book_message = f"🚫 添加图书时发生严重错误：{e}"
                st.rerun() 

if __name__ == "__main__":
    if not st.session_state.admin_logged_in:
        display_admin_login()
    else:
        admin_operations_page()