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
DB_FILENAME = "语言所资料室图书目录.mdb"
# 尝试构建绝对路径
try:
    current_dir = os.path.dirname(os.path.realpath(__file__))
    DB_PATH = os.path.join(current_dir, DB_FILENAME)
    if not os.path.exists(DB_PATH):
        DB_PATH = os.path.join(os.getcwd(), DB_FILENAME) # Fallback to CWD
except NameError:
    DB_PATH = os.path.join(os.getcwd(), DB_FILENAME)

# 数据库实例化 (使用 BookDatabase)
db = BookDatabase(DB_PATH) # 确保使用正确的类名和全局DB_PATH

ITEMS_PER_PAGE = 15

# 初始化 session_state 的通用函数
def init_session_state():
    """初始化应用所需的 session_state 变量。"""
    if 'query_conditions' not in st.session_state:
        st.session_state.query_conditions = {}
    if 'search_results' not in st.session_state:
        st.session_state.search_results = pd.DataFrame()
    if 'current_page' not in st.session_state: # 通用的当前页码
        st.session_state.current_page = 1

# 分页组件
def paginator(label, items, items_per_page=10, on_sidebar=False):
    """生成分页控件"""
    # 确保 current_page 已初始化
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
        
    n_pages = (len(items) - 1) // items_per_page + 1 if items else 1

    # 根据 on_sidebar 决定控件位置和更新方式
    if on_sidebar:
        page_format_func = lambda i: f"Page {i}"
        # 使用 session_state 中的 current_page 作为 selectbox 的默认值
        # selectbox 的 key 必须唯一，这里使用 label 来区分
        selected_page_sb = st.sidebar.selectbox(label, range(1, n_pages + 1), 
                                                index=st.session_state.current_page -1, # selectbox index is 0-based
                                                format_func=page_format_func, key=f"{label}_sb")
        # 如果 selectbox 的值改变，则更新 session_state.current_page
        if st.session_state.current_page != selected_page_sb:
            st.session_state.current_page = selected_page_sb
            st.rerun() # 当页码通过下拉框改变时，需要 rerun 来刷新显示
        current_page_display = selected_page_sb
    else:
        col1, col_page_info, col3 = st.columns([1,2,1])
        with col1:
            if st.button("上一页", key=f"{label}_prev"):
                if st.session_state.current_page > 1:
                    st.session_state.current_page -= 1
                    st.rerun()
        with col3:
            if st.button("下一页", key=f"{label}_next"):
                if st.session_state.current_page < n_pages:
                    st.session_state.current_page += 1
                    st.rerun()
        with col_page_info:
             st.write(f"第 {st.session_state.current_page} / {n_pages} 页")
        current_page_display = st.session_state.current_page

    start_idx = (current_page_display - 1) * items_per_page
    end_idx = start_idx + items_per_page
    return items[start_idx:end_idx] if items else []

# 图书查询页面
def book_query_page():
    """图书查询页面主函数"""
    init_session_state() # 确保 session_state 在页面加载时初始化
    st.title("语言研究所资料室图书查询系统")

    # 查询表单
    with st.form("search_form"):
        st.subheader("图书搜索")
        # 从 session_state 获取默认值，以便在翻页后保持输入框内容
        book_name_search = st.text_input("书名", value=st.session_state.query_conditions.get('bookname',''))
        author_search = st.text_input("作者", value=st.session_state.query_conditions.get('author',''))
        publisher_search = st.text_input("出版社", value=st.session_state.query_conditions.get('publishdepartment',''))
        
        # 处理年份输入，确保从 session_state 获取并正确处理 None 和类型
        year_from_session = st.session_state.query_conditions.get('publishdate') # publishdate 存储的是年份字符串或None
        default_year_val = None
        if year_from_session:
            try:
                default_year_val = int(year_from_session)
            except ValueError:
                default_year_val = None # 如果不能转为int，则为None

        publish_year_search = st.number_input(
            "出版年份 (例如: 2023)", 
            min_value=1000, 
            max_value=datetime.now().year + 5, # 动态设置最大年份，允许未来5年
            step=1, 
            value=default_year_val, # 使用处理后的默认值
            format="%d" # 确保显示为整数
        )
        search_submitted = st.form_submit_button("查询")

    # 表单提交处理: 更新查询条件并重置页码
    if search_submitted:
        st.session_state.query_conditions = {
            'bookname': book_name_search,
            'author': author_search,
            'publishdepartment': publisher_search,
            'publishdate': str(publish_year_search) if publish_year_search is not None else None
        }
        st.session_state.current_page = 1 # 新查询重置到第一页
        # Streamlit 会自动 rerun 脚本，无需显式调用 st.rerun() 此处

    # 数据获取和显示逻辑: 始终在脚本执行时运行（包括表单提交后、翻页后）
    active_conditions = {
        k: v for k, v in st.session_state.query_conditions.items() 
        if v is not None and str(v).strip() != ''
    }

    if active_conditions: # 只有当有有效查询条件时才获取数据
        results_df, total_count = db.search_books(
            active_conditions, 
            limit=ITEMS_PER_PAGE, 
            offset=(st.session_state.current_page - 1) * ITEMS_PER_PAGE
        )
        st.session_state.search_results = results_df
        st.session_state.total_results = total_count

        if not results_df.empty:
            st.subheader("查询结果")
            display_df = results_df.copy()
            # 选择要显示的列和顺序，与数据库中的列名一致
            display_df = display_df[['bookorder', 'indexnumber', 'bookname', 'author', 'publishdepartment', 'price', 'publishdate']]
            st.dataframe(display_df.reset_index(drop=True), use_container_width=True)

            # 分页控件
            total_pages = math.ceil(st.session_state.total_results / ITEMS_PER_PAGE) if ITEMS_PER_PAGE > 0 and st.session_state.total_results > 0 else 0
            
            if total_pages > 0: # 只有在有内容且总页数大于0时才显示分页
                st.caption(f"共 {st.session_state.total_results} 条记录，第 {st.session_state.current_page} / {total_pages} 页")
                
                # 使用更紧凑的布局或根据需要调整列数
                nav_cols = st.columns([1, 1, 1, 1]) # 首页，上一页，下一页，末页
                
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
        elif st.session_state.total_results == 0 and active_conditions: # 有查询条件但数据库返回0条
             st.info("没有找到符合条件的图书。")

    elif search_submitted and not active_conditions: # 点击了查询按钮，但所有条件都为空
        st.warning("请输入至少一个查询条件。")
        st.session_state.search_results = pd.DataFrame() # 清空旧结果
        st.session_state.total_results = 0

# 主应用逻辑
def main():
    """主应用函数，用于设置页面导航和显示选定页面。"""
    # st.sidebar.title("导航") # 移除侧边栏标题
    # 暂时只启用图书查询页面，其他页面后续实现
    page_options = {"图书查询": book_query_page}
    
    # 由于移除了侧边栏导航，直接调用图书查询页面函数
    # selected_page_name = st.sidebar.radio("选择功能", list(page_options.keys())) # 移除侧边栏radio选择

    # 默认显示图书查询页面
    page_options["图书查询"]()

    # 调用选定页面的函数 (这部分逻辑在单页面应用中不再需要，因为我们直接调用了唯一的页面)
    # if selected_page_name in page_options:
    #     page_options[selected_page_name]()
    # else:
    #     st.error("页面未找到!")

    # st.info("提示：请使用 `streamlit run app.py` 命令来运行此应用以确保所有功能正常。")

if __name__ == "__main__":
    main()