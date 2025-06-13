import pandas as pd
import os
from datetime import datetime
import uuid # For generating unique IDs if needed, though we'll try sequential int

class BookDatabase:
    def __init__(self, csv_file_path):
        """初始化数据库，使用CSV文件作为数据存储。

        Args:
            csv_file_path (str): CSV文件的完整路径。
        """
        self.csv_file_path = csv_file_path
        print(f"[DEBUG] BookDatabase initialized with path: {self.csv_file_path}") # DEBUG
        self.columns = ['id', 'bookorder', 'indexnumber', 'bookname', 'author', 
                        'publishdepartment', 'price', 'publishdate', 'isdelete']
        self.df = self._load_data()

    def _load_data(self):
        """加载CSV文件数据，如果文件不存在则创建一个空的DataFrame。"""
        print(f"[DEBUG] _load_data: Attempting to load {self.csv_file_path}") # DEBUG
        if os.path.exists(self.csv_file_path):
            try:
                df = pd.read_csv(self.csv_file_path, dtype={'bookorder': str, 'indexnumber': str}) # Specify some dtypes
                print(f"[DEBUG] _load_data: CSV loaded successfully. Shape: {df.shape}") # DEBUG
                if not df.empty:
                    print("[DEBUG] _load_data: CSV head:\n", df.head()) # DEBUG
                    print("[DEBUG] _load_data: CSV dtypes:\n", df.dtypes) # DEBUG

                # Ensure all necessary columns exist, fill with defaults if not
                for col in self.columns:
                    if col not in df.columns:
                        print(f"[DEBUG] _load_data: Column '{col}' missing, adding it.") # DEBUG
                        if col == 'isdelete':
                            df[col] = 0
                        elif col == 'id':
                             # Simple sequential ID generation if 'id' column is missing entirely
                            if df.empty:
                                df[col] = pd.Series(dtype=int)
                            else:
                                df[col] = range(1, len(df) + 1)
                        else:
                            df[col] = None
                
                # Ensure correct data types, especially critical ones
                if 'id' in df.columns:
                    df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0)
                    if not df.empty and df['id'].max() > 0 : # only convert to int if there are values
                        df['id'] = df['id'].astype(int)
                    else: # if all are NaN or 0 after coerce
                        df['id'] = pd.Series(dtype=int)


                if 'price' in df.columns:
                    df['price'] = pd.to_numeric(df['price'], errors='coerce') 
                if 'isdelete' in df.columns:
                    df['isdelete'] = pd.to_numeric(df['isdelete'], errors='coerce').fillna(0).astype(int)
                
                # Ensure 'author' and other text columns are strings
                for col_name in ['bookname', 'author', 'publishdepartment', 'publishdate', 'bookorder', 'indexnumber']:
                    if col_name in df.columns:
                        df[col_name] = df[col_name].astype(str).fillna('') # Convert to string, fill NaN with empty string

                return df[self.columns] # Ensure column order
            except pd.errors.EmptyDataError:
                print(f"[DEBUG] _load_data: CSV file {self.csv_file_path} is empty.") # DEBUG
                return pd.DataFrame(columns=self.columns)
            except Exception as e:
                print(f"[ERROR] _load_data: Error loading CSV {self.csv_file_path}: {e}") # ERROR
                return pd.DataFrame(columns=self.columns)
        else:
            print(f"[DEBUG] _load_data: CSV file NOT FOUND at {self.csv_file_path}, creating empty DataFrame.") # DEBUG
            df = pd.DataFrame(columns=self.columns)
            df = df.astype({
                'id': int, 'bookorder': str, 'indexnumber': str, 'bookname': str,
                'author': str, 'publishdepartment': str, 'price': float,
                'publishdate': str, 'isdelete': int
            })
            return df

    def _save_data(self):
        """保存DataFrame数据到CSV文件。"""
        try:
            # Ensure correct types before saving
            if not self.df.empty:
                self.df['id'] = self.df['id'].astype(int)
                self.df['isdelete'] = self.df['isdelete'].astype(int)
                if 'price' in self.df.columns:
                    self.df['price'] = pd.to_numeric(self.df['price'], errors='coerce')
            
            self.df.to_csv(self.csv_file_path, index=False, encoding='utf-8-sig')
            print(f"[DEBUG] _save_data: Data saved to {self.csv_file_path}") # DEBUG
        except Exception as e:
            print(f"[ERROR] _save_data: Error saving CSV {self.csv_file_path}: {e}") # ERROR
            raise

    def connect(self):
        pass 

    def close(self):
        pass 

    def _create_indexes(self):
        pass 

    def search_books(self, conditions, limit=15, offset=0):
        print(f"[DEBUG] search_books: Received conditions: {conditions}") # DEBUG
        # self._load_data() # Usually not needed if df is a class member and updated, but for safety:
        self.df = self._load_data() # Force reload to ensure latest data for searching

        if self.df.empty:
            print("[DEBUG] search_books: DataFrame is empty. Returning no results.") #DEBUG
            return pd.DataFrame(columns=self.columns), 0
            
        # Start with non-deleted books
        print(f"[DEBUG] search_books: Initial DataFrame shape before any filtering: {self.df.shape}") # DEBUG
        filtered_df = self.df[self.df['isdelete'] == 0].copy()
        print(f"[DEBUG] search_books: Shape after (isdelete == 0) filter: {filtered_df.shape}") # DEBUG
        if filtered_df.empty and not self.df[self.df['isdelete'] == 0].empty :
             print("[DEBUG] search_books: All books are marked as deleted or isdelete column issue.")


        if conditions.get('bookname'):
            search_term = str(conditions['bookname']).strip()
            if search_term:
                print(f"[DEBUG] search_books: Filtering by bookname: '{search_term}'") # DEBUG
                filtered_df = filtered_df[filtered_df['bookname'].str.contains(search_term, case=False, na=False)]
                print(f"[DEBUG] search_books: Shape after bookname filter: {filtered_df.shape}") # DEBUG
        
        if conditions.get('author'):
            search_term = str(conditions['author']).strip()
            if search_term:
                print(f"[DEBUG] search_books: Filtering by author: '{search_term}'") # DEBUG
                # Let's see some sample authors from the filtered_df before this specific filter
                if not filtered_df.empty:
                    print(f"[DEBUG] Sample authors in current filtered_df (up to 5): {filtered_df['author'].unique()[:5]}")
                
                # Apply the filter
                filtered_df = filtered_df[filtered_df['author'].str.contains(search_term, case=False, na=False)]
                print(f"[DEBUG] search_books: Shape after author filter: {filtered_df.shape}") # DEBUG
                if not filtered_df.empty:
                    print(f"[DEBUG] search_books: Result head after author filter:\n{filtered_df.head()}")
            
        if conditions.get('publishdepartment'):
            search_term = str(conditions['publishdepartment']).strip()
            if search_term:
                print(f"[DEBUG] search_books: Filtering by publishdepartment: '{search_term}'") # DEBUG
                filtered_df = filtered_df[filtered_df['publishdepartment'].str.contains(search_term, case=False, na=False)]
                print(f"[DEBUG] search_books: Shape after publishdepartment filter: {filtered_df.shape}") # DEBUG

        search_year = conditions.get('year') or conditions.get('publishdate')
        search_month = conditions.get('month')

        if search_year:
            year_str = str(search_year).strip()
            if year_str:
                print(f"[DEBUG] search_books: Filtering by year: '{year_str}'") # DEBUG
                filtered_df['publishdate'] = filtered_df['publishdate'].astype(str) # Ensure string
                filtered_df = filtered_df[filtered_df['publishdate'].str.startswith(f'{year_str}年', na=False)]
                print(f"[DEBUG] search_books: Shape after year filter: {filtered_df.shape}") # DEBUG
        
        if search_month:
            month_str = str(search_month).strip()
            if month_str:
                print(f"[DEBUG] search_books: Filtering by month: '{month_str}'") # DEBUG
                pattern = f'年{month_str}月' 
                filtered_df['publishdate'] = filtered_df['publishdate'].astype(str) # Ensure string
                filtered_df = filtered_df[filtered_df['publishdate'].str.contains(pattern, na=False, regex=False)]
                print(f"[DEBUG] search_books: Shape after month filter: {filtered_df.shape}") # DEBUG

        total_count = len(filtered_df)
        print(f"[DEBUG] search_books: Total count before pagination: {total_count}") # DEBUG
        
        paginated_df = filtered_df.sort_values(by='id', ascending=True).iloc[offset : offset + limit] #Ensure sorting by ID for consistent pagination
        print(f"[DEBUG] search_books: Shape after pagination: {paginated_df.shape}") # DEBUG
        
        return paginated_df, total_count

    def add_book(self, book_data):
        self.df = self._load_data() 

        required_fields = ['bookorder', 'indexnumber', 'bookname', 'author', 'publishdepartment']
        for field in required_fields:
            if not book_data.get(field) or not str(book_data.get(field)).strip(): # check if None or empty string
                raise ValueError(f"'{field}' 是必填字段，且不能为空值")

        publishdate_str = "" # Default to empty string if no year/month
        year = book_data.get('year')
        month = book_data.get('month')
        if year and month:
            try:
                year_int = int(year)
                month_int = int(month)
                if not (1 <= month_int <= 12):
                    raise ValueError("月份必须在1到12之间")
                publishdate_str = f"{year_int}年{month_int}月"
            except ValueError as e:
                raise ValueError(f"无效的年份或月份: {e}")
        
        if not self.df.empty and 'id' in self.df.columns and self.df['id'].notna().any() and len(self.df['id']) > 0 :
            new_id = self.df['id'].max() + 1 if pd.api.types.is_numeric_dtype(self.df['id']) and self.df['id'].max() >=0 else 1
        else:
            new_id = 1
            if 'id' not in self.df.columns or self.df.empty: # Reinitialize if was problematic
                 self.df = pd.DataFrame(columns=self.columns).astype({'id': int, 'isdelete': int, 'price': float})


        new_entry = {
            'id': new_id,
            'bookorder': str(book_data['bookorder']).strip(),
            'indexnumber': str(book_data['indexnumber']).strip(),
            'bookname': str(book_data['bookname']).strip(),
            'author': str(book_data['author']).strip(),
            'publishdepartment': str(book_data['publishdepartment']).strip(),
            'price': float(book_data['price']) if book_data.get('price') is not None else None,
            'publishdate': publishdate_str,
            'isdelete': 0
        }
        
        new_row_df = pd.DataFrame([new_entry])
        # Ensure dtypes match before concat if df is not empty
        if not self.df.empty:
            for col in self.df.columns:
                if col in new_row_df.columns and self.df[col].dtype != new_row_df[col].dtype:
                    try:
                        new_row_df[col] = new_row_df[col].astype(self.df[col].dtype)
                    except Exception as e:
                        print(f"[WARN] add_book: Could not cast column {col} to match DataFrame dtype: {e}")
        
        self.df = pd.concat([self.df, new_row_df], ignore_index=True)
        self._save_data()

    def update_book(self, book_id, book_data):
        self.df = self._load_data() 
        
        book_id = int(book_id) 
        idx_series = self.df[self.df['id'] == book_id].index
        
        if idx_series.empty:
            raise ValueError(f"未找到ID为 {book_id} 的图书")
        idx = idx_series[0] # Get the first (and should be only) index

        publishdate_str = self.df.loc[idx, 'publishdate'] 
        year = book_data.get('year')
        month = book_data.get('month')
        
        if year and month: 
            try:
                year_int = int(year)
                month_int = int(month)
                if not (1 <= month_int <= 12):
                    raise ValueError("月份必须在1到12之间")
                publishdate_str = f"{year_int}年{month_int}月"
            except ValueError as e:
                print(f"更新日期时出错: {e}, publishdate 未更新") 
        elif 'publishdate' in book_data and book_data['publishdate'] is None: 
            publishdate_str = "" # Use empty string for None
        
        for col in self.df.columns:
            if col in book_data and col not in ['id', 'year', 'month', 'isdelete']: 
                value = book_data[col]
                if col == 'price':
                    value = float(value) if value is not None else None
                # Ensure value is stripped if it's a string field
                if isinstance(value, str):
                    value = value.strip()
                self.df.loc[idx, col] = value
        
        self.df.loc[idx, 'publishdate'] = publishdate_str 
        self._save_data()

    def delete_book(self, book_id):
        self.df = self._load_data() 
        book_id = int(book_id)
        idx = self.df[self.df['id'] == book_id].index
        if not idx.empty:
            self.df.loc[idx, 'isdelete'] = 1
            self._save_data()
        else:
            raise ValueError(f"未找到ID为 {book_id} 的图书")


    def get_book_by_id(self, book_id):
        self.df = self._load_data() 
        book_id = int(book_id)
        # Ensure 'id' column is of integer type for comparison if it's not already
        if not pd.api.types.is_integer_dtype(self.df['id']):
             self.df['id'] = pd.to_numeric(self.df['id'], errors='coerce').fillna(-1).astype(int)

        book_series_df = self.df[(self.df['id'] == book_id) & (self.df['isdelete'] == 0)]
        return book_series_df.iloc[0] if not book_series_df.empty else None

    def get_all_books(self, limit=15, offset=0):
        self.df = self._load_data() 
        
        if self.df.empty:
            return pd.DataFrame(columns=self.columns), 0
            
        active_books_df = self.df[self.df['isdelete'] == 0].copy()
        total_count = len(active_books_df)
        
        paginated_df = active_books_df.sort_values(by='id', ascending=True).iloc[offset : offset + limit]
        
        return paginated_df, total_count