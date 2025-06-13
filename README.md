# 资料室图书管理系统

这是一个使用 Streamlit 构建的资料室图书管理系统，允许用户查询图书信息，并为管理员提供添加、编辑和删除图书的功能。

## 功能

- **图书查询**：
  - 按书名、作者、出版社、出版年份和月份进行组合查询。
- **管理员操作**：
  - 添加新图书：包括图书编号、书目索引号、书名、作者、出版社、价格、出版时间等信息。
  - 编辑图书信息：搜索现有图书并修改其详细信息。
  - 删除图书：搜索并删除图书记录（软删除）。

## 技术栈

- Python
- Streamlit (用于构建Web界面)
- Pandas (用于数据处理)
- pyodbc (用于连接 Microsoft Access 数据库 .mdb 文件)

## 数据库

本系统使用名为 `语言所资料室图书目录.mdb` 的 Microsoft Access 数据库文件。
数据库中包含一个名为 `bookCategory` 的表，字段如下：

- `id` (自动编号, 主键)
- `bookorder` (图书编号, 文本)
- `indexnumber` (书目索引号, 文本)
- `bookname` (书名, 文本)
- `author` (作者, 文本)
- `publishdepartment` (出版社, 文本)
- `price` (价格, 数字)
- `publishdate` (出版日期, 文本, 格式: YYYY/MM)
- `isdelete` (是否删除, 数字, 0表示未删除, 1表示已删除)

## 安装与运行

1.  **克隆或下载项目**

2.  **安装依赖**

    确保你已经安装了 Python。然后通过 pip 安装项目所需的库：

    ```bash
    pip install -r requirements.txt
    ```

3.  **准备数据库**

    将 `语言所资料室图书目录.mdb` 文件放置在项目的根目录下，或者根据需要修改 `app.py` 和 `database.py` 文件中的 `DB_FILE` 路径。

    **重要**: 你可能需要安装 Microsoft Access 数据库引擎的驱动程序才能让 `pyodbc` 连接到 `.mdb` 文件。你可以从微软官方网站下载并安装 “Microsoft Access Database Engine Redistributable”。请选择与你的 Python 和操作系统位数（32位或64位）相匹配的版本。

4.  **运行应用**

    在项目根目录下打开终端或命令行，运行以下命令：

    ```bash
    streamlit run app.py
    ```

    应用将在你的默认浏览器中打开。

## 注意事项

-   **数据库驱动**：如上所述，确保正确安装了 Access 数据库驱动。
-   **文件路径**：数据库文件的路径在代码中是硬编码的。如果移动了 `.mdb` 文件，请相应更新 `app.py` 和 `database.py` 中的路径。
-   **索引创建**：`database.py` 中尝试为 `bookCategory` 表的 `bookname`, `author`, `publishdepartment`, `publishdate` 字段创建索引。如果你的 Access 版本或 `pyodbc` 驱动不支持 `CREATE INDEX IF NOT EXISTS` 语法，这部分可能会静默失败或报错。你可以手动通过 Access 打开数据库文件来创建这些索引以提高查询性能。

## 未来可能的改进

-   更美观的UI设计。
-   用户认证和权限管理（区分普通用户和管理员）。
-   更详细的错误处理和日志记录。
-   批量导入/导出图书数据。
-   更完善的表单验证。