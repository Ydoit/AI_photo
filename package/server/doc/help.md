不会自动增加。

你现在的 `User` 模型只是 **Python 代码里的表结构定义**，它不会直接让数据库自动同步变化。
如果你后来在 `User` 里加了一个新字段，比如：

```python
phone = Column(String, index=True)
```

数据库里原有的 `users` 表不会自己添加 `phone` 列。你必须**手动执行数据库迁移**，常用做法是使用 **Alembic** 来管理数据库结构的变更。

---

## 常见流程（以 Alembic 为例）

1. **安装 Alembic**

   ```bash
   pip install alembic
   ```

2. **初始化 Alembic**
   在项目根目录执行：

   ```bash
   alembic init alembic
   ```

3. **配置 Alembic**
   在 `alembic.ini` 里设置你的数据库连接字符串，例如：

   ```
   sqlalchemy.url = postgresql+psycopg2://user:password@localhost/dbname
   ```

4. **生成迁移脚本**
   当你修改了 `User` 模型（比如加了 `phone` 字段）后：

   ```bash
   alembic revision --autogenerate -m "add phone column to users"
   ```

5. **执行迁移**

   ```bash
   alembic upgrade head
   ```

这样数据库才会真正新增列。

---

📌 **小结**

* SQLAlchemy 本身不会自动改数据库结构。
* 改模型后，需要用 Alembic 这类迁移工具同步结构。
* 如果直接在生产环境手改表结构，会导致代码和模型不同步，容易出错。

如果你想，我可以帮你画一张 **模型修改到数据库迁移** 的流程图，这样会更直观。
你要我画吗？
