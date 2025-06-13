import streamlit as st
import pandas as pd
from database import BookDatabase # Uses the new CSV-based BookDatabase
import os
from datetime import datetime
import math

# 数据库文件
DB_FILENAME = "bookCategory.csv" # CHANGED TO CSV
# 尝试构建绝对路径
try:
    current_dir = os.path.dirname(os.path.realpath(__file__))
    DB_PATH = os.path.join(current_dir, DB_FILENAME)
    if not os.path.exists(DB_PATH) and not os.path.isabs(DB_FILENAME):
        DB_PATH = os.path.join(os.getcwd(), DB_FILENAME)
except NameError: 
    DB_PATH = os.path.join(os.getcwd(), DB_FILENAME)

# Database instance
db = BookDatabase(DB_PATH) # Initialize with CSV path

ITEMS_PER_PAGE = 15

st.set_page_config(page_title="管理员操作后台", layout="wide")
st.title("图书管理后台")

# --- 简单的密码保护管理员页面 ---
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

def display_admin_login():
    st.sidebar.header("管理员登录")
    password = st.sidebar.text_input("请输入管理员密码", type="password", key="admin_password_input_admin_page")
    if st.sidebar.button("登录", key="admin_login_button_admin_page"):
        if password == "admin123":  # 示例密码
            st.session_state.admin_logged_in = True
            st.sidebar.success("登录成功!")
            st.rerun()
        else:
            st.sidebar.error("密码错误")

# --- 分页组件 ---
def pagination_controls(total_items, current_page_session_key, key_suffix=""):
    """生成分页控件"""
    total_pages = math.ceil(total_items / ITEMS_PER_PAGE) if ITEMS_PER_PAGE > 0 else 1
    total_pages = max(1, total_pages) # Ensure at least 1 page
    current_page_val = st.session_state.get(current_page_session_key, 1)
    current_page_val = min(current_page_val, total_pages) # Cap current page if it exceeds total
    st.session_state[current_page_session_key] = current_page_val


    if total_pages <= 1 and total_items <= ITEMS_PER_PAGE : # Only show if more than one page or more items than fit
        if total_items > 0:
            st.caption(f"共 {total_items} 条记录")
        return current_page_val

    cols = st.columns([1, 1, 1, 1, 2, 1])

    if cols[0].button("首页", key=f"first_{key_suffix}_admin", disabled=(current_page_val == 1)):
        st.session_state[current_page_session_key] = 1
        st.rerun()

    if cols[1].button("上一页", key=f"prev_{key_suffix}_admin", disabled=(current_page_val == 1)):
        st.session_state[current_page_session_key] -= 1
        st.rerun()

    if cols[2].button("下一页", key=f"next_{key_suffix}_admin", disabled=(current_page_val == total_pages)):
        st.session_state[current_page_session_key] += 1
        st.rerun()

    if cols[3].button("末页", key=f"last_{key_suffix}_admin", disabled=(current_page_val == total_pages)):
        st.session_state[current_page_session_key] = total_pages
        st.rerun()
    
    # Ensure jump_to_page value is within valid range for number_input
    jump_value = current_page_val
    if 'jump_value_for_input' in st.session_state and f"jump_{key_suffix}_admin" in st.session_state:
        if st.session_state[f"jump_{key_suffix}_admin"] != current_page_val: # if user typed something
             jump_value = st.session_state[f"jump_{key_suffix}_admin"]

    jump_to_page = cols[4].number_input(
        f"页码 (1-{total_pages})",
        min_value=1,
        max_value=total_pages,
        value=jump_value, # Use current_page_val to reflect actual page
        step=1,
        key=f"jump_{key_suffix}_admin",
        label_visibility="collapsed"
    )
    if cols[5].button("跳转", key=f"jump_btn_{key_suffix}_admin"):
        st.session_state[current_page_session_key] = jump_to_page
        st.session_state['jump_value_for_input'] = jump_to_page # Store it for consistency
        st.rerun()

    st.caption(f"当前第 {current_page_val} 页 / 共 {total_pages} 页 (共 {total_items} 条记录)")
    return current_page_val

# --- 管理员操作页面 ---
def admin_operations_page():
    """管理员操作页面主函数"""
    st.header("管理员操作")
    # db is already initialized globally

    admin_action = st.selectbox("选择操作", ["浏览和管理图书", "添加图书"], key="admin_main_action_admin_page")

    if admin_action == "浏览和管理图书":
        st.subheader("浏览所有图书")
        if 'browse_current_page_admin' not in st.session_state: 
            st.session_state.browse_current_page_admin = 1

        offset = (st.session_state.browse_current_page_admin - 1) * ITEMS_PER_PAGE
        all_books_df, total_books = db.get_all_books(limit=ITEMS_PER_PAGE, offset=offset)

        if not all_books_df.empty:
            # Columns from CSV: 'id', 'bookorder', 'indexnumber', 'bookname', 'author', 
            # 'publishdepartment', 'price', 'publishdate', 'isdelete'
            display_cols_browse = ['id', 'bookorder', 'indexnumber', 'bookname', 'author', 'publishdepartment', 'price', 'publishdate']
            display_cols_browse = [col for col in display_cols_browse if col in all_books_df.columns]
            st.dataframe(all_books_df[display_cols_browse].reset_index(drop=True), use_container_width=True)
            pagination_controls(total_books, 'browse_current_page_admin', key_suffix="browse_admin")
        else:
            st.info("数据库中没有图书。")

    elif admin_action == "添加图书":
        st.subheader("添加新图书")
        with st.form("add_book_form_admin", clear_on_submit=True):
            book_order = st.text_input("图书编号 *", key="add_bo_admin")
            index_number = st.text_input("书目索引号 *", key="add_in_admin")
            book_name = st.text_input("书名 *", key="add_bn_admin")
            author = st.text_input("作者 *", key="add_au_admin")
            publisher = st.text_input("出版社 *", key="add_pd_admin")
            price_val = st.number_input("价格", min_value=0.0, value=None, format="%.2f", key="add_pr_admin", help="留空则为无价格")
            publish_year = st.number_input("出版年份", min_value=1000, max_value=datetime.now().year + 10, step=1, value=None, format="%d", key="add_py_admin", help="若填写，月份也必填")
            publish_month = st.number_input("出版月份", min_value=1, max_value=12, step=1, value=None, format="%d", key="add_pm_admin", help="若填写，年份也必填")

            submitted_add = st.form_submit_button("确认添加")
            if submitted_add:
                required = {"图书编号": book_order, "书目索引号": index_number, "书名": book_name, "作者": author, "出版社": publisher}
                empty_fields = [k for k, v in required.items() if not str(v).strip()]

                if (publish_year is not None and publish_month is None) or \
                   (publish_year is None and publish_month is not None):
                    st.error("若要填写出版日期，年份和月份必须同时填写。")
                elif empty_fields:
                    st.error(f"以下必填字段不能为空：{', '.join(empty_fields)}")
                else:
                    book_data = {
                        "bookorder": book_order.strip(), 
                        "indexnumber": index_number.strip(), 
                        "bookname": book_name.strip(), 
                        "author": author.strip(),
                        "publishdepartment": publisher.strip(), 
                        "price": price_val, # Already float or None
                        "year": int(publish_year) if publish_year is not None else None,
                        "month": int(publish_month) if publish_month is not None else None
                    }
                    try:
                        db.add_book(book_data)
                        st.success("图书添加成功！")
                    except ValueError as ve: 
                        st.error(f"添加失败：{ve}")
                    except Exception as e: 
                        st.error(f"添加图书时发生错误：{e}")
                        st.exception(e) # Provides more details for debugging

# --- 主程序入口 ---
if __name__ == "__main__":
    if not st.session_state.admin_logged_in:
        display_admin_login()
    else:
        admin_operations_page()
        if st.sidebar.button("退出登录", key="admin_logout_btn_admin_page"):
            st.session_state.admin_logged_in = False
            # Clear relevant admin session state keys
            keys_to_clear_admin = [
                'admin_logged_in', 'browse_current_page_admin',
                # 'edit_search_df_admin', 'selected_book_id_for_edit_admin', # If you re-add edit
                # 'del_search_df_admin', 'sel_book_id_for_del_admin'      # If you re-add delete
            ]
            for key in keys_to_clear_admin:
                if key in st.session_state: 
                    del st.session_state[key]
            st.rerun()