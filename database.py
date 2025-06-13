import pyodbc
import pandas as pd
from datetime import datetime

class BookDatabase:
    def __init__(self, db_file_path):
        """初始化数据库连接

        Args:
            db_file_path (str): Access数据库（.mdb文件）的完整路径。
        """
        self.db_file_path = db_file_path
        self.conn_str = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={self.db_file_path};"
        self.conn = None
        self.cursor = None

    def connect(self):
        """建立数据库连接"""
        if not self.conn:
            try:
                self.conn = pyodbc.connect(self.conn_str)
                self.cursor = self.conn.cursor()
                # 创建索引（如果不存在）
                self._create_indexes()
            except pyodbc.InterfaceError as e:
                # 增强错误提示，帮助用户诊断驱动问题
                if "IM002" in str(e):
                    raise pyodbc.InterfaceError(
                        f"{e} - 请确保已安装 Microsoft Access Database Engine (ODBC驱动程序)，并且数据库文件路径 '{self.db_file_path}' 正确。"
                        f"连接字符串为: {self.conn_str}"
                    ) from e
                raise # 重新抛出原始异常

    def _create_indexes(self):
        """为常用查询字段创建索引以提高检索速度"""
        try:
            # 为bookname创建索引
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_bookname ON bookCategory (bookname);
            """)
            # 为author创建索引
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_author ON bookCategory (author);
            """)
            # 为publishdepartment创建索引
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_publishdepartment ON bookCategory (publishdepartment);
            """)
            # 为publishdate创建索引
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_publishdate ON bookCategory (publishdate);
            """)
            self.conn.commit()
        except pyodbc.Error:
            # Access数据库可能不支持CREATE INDEX IF NOT EXISTS语法
            pass

    def search_books(self, conditions, limit=15, offset=0):
        """根据条件搜索图书，支持分页

        Args:
            conditions: 包含搜索条件的字典。
            limit: 每页记录数。
            offset: 偏移量。
        
        Returns:
            一个元组 (books_df, total_count)，其中 books_df 是包含当前页图书的 DataFrame，
            total_count 是符合条件的总记录数。
        """
        self.connect()
        
        base_query = "FROM bookCategory WHERE isdelete = 0"
        count_query_sql = "SELECT COUNT(*) " + base_query
        data_query_sql = "SELECT id, bookorder, indexnumber, bookname, author, publishdepartment, price, publishdate " + base_query
        
        params = []
        query_conditions = []

        if conditions.get('bookname'):
            query_conditions.append("bookname LIKE ?")
            params.append(f'%{conditions["bookname"]}%')

        if conditions.get('author'):
            query_conditions.append("author LIKE ?")
            params.append(f'%{conditions["author"]}%')

        if conditions.get('publishdepartment'):
            query_conditions.append("publishdepartment LIKE ?")
            params.append(f'%{conditions["publishdepartment"]}%')

        # 修改日期查询以适应 'YYYY年M月' 格式
        # 注意：Access SQL 对于字符串操作和日期部分提取可能有限，
        # 如果直接用 LIKE '%year年%' AND LIKE '%month月%' 可能会不精确或效率低。
        # 更稳妥的方式是在应用层处理或确保数据库中日期格式统一，然后精确匹配。
        # 这里我们假设 publishdate 存储的是 'YYYY年M月' 或 'YYYY年MM月' 格式
        if conditions.get('year'):
            year_str = str(conditions['year'])
            query_conditions.append("publishdate LIKE ?")
            params.append(f'{year_str}年%') # 匹配以 'YYYY年' 开头的
        
        if conditions.get('month'):
            month_str = str(conditions['month'])
            # 为了更精确匹配月份，可以这样，但如果年份也选了，上面的条件已经部分覆盖
            # 如果年份没选，单独选月份，这个条件可能匹配到其他年份的同月份
            # 理想情况是数据库能支持更灵活的日期部分提取
            query_conditions.append("publishdate LIKE ?")
            params.append(f'%年{month_str}月%') 

        if query_conditions:
            data_query_sql += " AND " + " AND ".join(query_conditions)
            count_query_sql += " AND " + " AND ".join(query_conditions)

        # 获取总记录数
        self.cursor.execute(count_query_sql, tuple(params))
        total_count = self.cursor.fetchone()[0]

        # 添加排序和分页
        data_query_sql += " ORDER BY id ASC LIMIT ? OFFSET ?" # Access 不支持 LIMIT ?, OFFSET ?
        # MS Access SQL分页语法是不同的，通常使用 TOP 和子查询，或者 ROW_NUMBER() OVER (ORDER BY ...)
        # 鉴于 pyodbc 和 pandas 的配合，我们可以先获取所有符合条件的数据，然后在 pandas层面分页
        # 或者构造复杂的 Access SQL。为了简化，这里先获取所有，后续在 app.py 中用 pandas 分页
        # 如果数据量非常大，这种方式效率不高，需要优化SQL
        
        # 修正：直接在SQL层面尝试分页，如果不行再回退到pandas分页
        # Access SQL 分页的典型做法 (假设 id 是唯一且递增的):
        # SELECT TOP limit * FROM (SELECT TOP (offset + limit) * FROM table ORDER BY id ASC) ORDER BY id DESC (取最后limit条)
        # 或者 SELECT * FROM (SELECT TOP limit * FROM (SELECT TOP (offset + limit) * FROM table ORDER BY id DESC) ORDER BY id ASC) (取最前limit条)
        # 另一种方法是使用 NOT IN 和子查询，但效率较低
        # 对于 Access, 更通用的分页方式 (如果 id 不是严格连续的，但可以排序):
        # SELECT * FROM bookCategory WHERE isdelete = 0 AND id NOT IN (SELECT TOP offset id FROM bookCategory WHERE isdelete = 0 ORDER BY id ASC) ORDER BY id ASC
        # 然后再取 TOP limit
        # 考虑到复杂性和驱动兼容性，我们先用pandas分页，如果性能瓶颈再优化SQL

        # 重新构建不含分页的查询，让pandas处理分页
        data_query_sql_no_paging = data_query_sql.split(" ORDER BY")[0] # 移除默认的排序和分页
        if query_conditions: # 确保 AND 在正确的位置
             data_query_sql_no_paging = "SELECT id, bookorder, indexnumber, bookname, author, publishdepartment, price, publishdate FROM bookCategory WHERE isdelete = 0 AND " + " AND ".join(query_conditions)
        else:
             data_query_sql_no_paging = "SELECT id, bookorder, indexnumber, bookname, author, publishdepartment, price, publishdate FROM bookCategory WHERE isdelete = 0"
        data_query_sql_no_paging += " ORDER BY id ASC" # 确保排序一致性

        df = pd.read_sql(data_query_sql_no_paging, self.conn, params=params)
        
        # 在 pandas DataFrame层面进行分页
        paginated_df = df.iloc[offset : offset + limit]
        
        return paginated_df, total_count

    def add_book(self, book_data):
        """添加新图书
        
        Args:
            book_data: 包含图书信息的字典，必须包含：
                - bookorder: 图书编号
                - indexnumber: 书目索引号
                - bookname: 书名
                - author: 作者
                - publishdepartment: 出版社
                可选包含：
                - price: 价格
                - year: 出版年份 (int)
                - month: 出版月份 (int)
        """
        self.connect()

        required_fields = ['bookorder', 'indexnumber', 'bookname', 'author', 'publishdepartment']
        for field in required_fields:
            if not book_data.get(field):
                raise ValueError(f"{field} 是必填字段")

        publishdate = None
        year = book_data.get('year')
        month = book_data.get('month')
        if year and month:
            try:
                # 确保年份和月份是有效的数字
                year_int = int(year)
                month_int = int(month)
                if not (1 <= month_int <= 12):
                    raise ValueError("月份必须在1到12之间")
                publishdate = f"{year_int}年{month_int}月"
            except ValueError as e:
                raise ValueError(f"无效的年份或月份: {e}")
        
        self.cursor.execute("""
            INSERT INTO bookCategory 
            (bookorder, indexnumber, bookname, author, publishdepartment, price, publishdate, isdelete)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            book_data['bookorder'],
            book_data['indexnumber'],
            book_data['bookname'],
            book_data['author'],
            book_data['publishdepartment'],
            book_data.get('price', None), # 允许价格为空
            publishdate
        ))
        self.conn.commit()

    def update_book(self, book_id, book_data):
        """更新图书信息
        
        Args:
            book_id: 图书ID
            book_data: 包含更新信息的字典，键可以是表中的任何字段，
                       外加 'year' 和 'month' 用于更新 publishdate。
        """
        self.connect()

        update_parts = []
        params = []

        for field, value in book_data.items():
            if field in ['year', 'month', 'id']: # id 不应通过此方法更新，year/month单独处理
                continue
            # 允许更新为空字符串或None，除非有特定业务逻辑禁止
            update_parts.append(f"[{field}] = ?") # 使用方括号以防字段名是保留字
            params.append(value)

        year = book_data.get('year')
        month = book_data.get('month')
        
        # 检查是否需要更新publishdate
        # 如果只提供了year或month中的一个，或者都提供了但值为空，则可能需要清空publishdate或保持不变
        # 这里假设如果提供了year和month，就更新；如果只提供一个或都为空，则不主动修改publishdate，除非显式传入 publishdate=None
        if year and month:
            try:
                year_int = int(year)
                month_int = int(month)
                if not (1 <= month_int <= 12):
                    raise ValueError("月份必须在1到12之间")
                update_parts.append("[publishdate] = ?")
                params.append(f"{year_int}年{month_int}月")
            except ValueError as e:
                # 如果日期转换失败，可以选择不更新日期或抛出错误
                print(f"更新日期时出错: {e}, publishdate 未更新") # 或者 raise e
        elif 'publishdate' in book_data and book_data['publishdate'] is None: # 允许显式将publishdate设为NULL
            update_parts.append("[publishdate] = ?")
            params.append(None)

        if not update_parts:
            return # 没有需要更新的字段

        query = f"UPDATE bookCategory SET {', '.join(update_parts)} WHERE id = ?"
        params.append(book_id)
        
        try:
            self.cursor.execute(query, tuple(params))
            self.conn.commit()
        except pyodbc.Error as e:
            # 可以记录错误或重新抛出
            print(f"更新图书失败 (ID: {book_id}): {e}")
            raise

    def delete_book(self, book_id):
        """删除图书（软删除）
        
        Args:
            book_id: 图书ID
        """
        self.connect()
        self.cursor.execute("""
            UPDATE bookCategory SET isdelete = 1 WHERE id = ?
        """, (book_id,))
        self.conn.commit()

    def get_book_by_id(self, book_id):
        """根据ID获取图书信息
        
        Args:
            book_id: 图书ID
        Returns:
            一个 pandas Series 包含图书信息，如果未找到则为 None。
        """
        self.connect()
        # 选择特定列，避免用 SELECT *
        query = "SELECT id, bookorder, indexnumber, bookname, author, publishdepartment, price, publishdate FROM bookCategory WHERE id = ? AND isdelete = 0"
        df = pd.read_sql(query, self.conn, params=[book_id])
        return df.iloc[0] if not df.empty else None

    def get_all_books(self, limit=15, offset=0):
        """获取所有未删除的图书，支持分页

        Args:
            limit: 每页记录数。
            offset: 偏移量。
        
        Returns:
            一个元组 (books_df, total_count)，其中 books_df 是包含当前页图书的 DataFrame，
            total_count 是所有未删除图书的总数。
        """
        self.connect()
        
        count_query_sql = "SELECT COUNT(*) FROM bookCategory WHERE isdelete = 0"
        self.cursor.execute(count_query_sql)
        total_count = self.cursor.fetchone()[0]
        
        # 使用 pandas 进行分页
        data_query_sql = "SELECT id, bookorder, indexnumber, bookname, author, publishdepartment, price, publishdate FROM bookCategory WHERE isdelete = 0 ORDER BY id ASC"
        df_all = pd.read_sql(data_query_sql, self.conn)
        paginated_df = df_all.iloc[offset : offset + limit]
        
        return paginated_df, total_count

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None