# 历史均价统计 API 文档

## 概述

新增的统计功能提供了按年度统计城市/商圈历史均价的能力，支持 2023-2025 年度数据查询。

---

## API 端点

### 1. 获取历史均价统计

**端点**: `GET /api/historical_avg_price`

**描述**: 按年度统计指定城市（或商圈）的历史均价数据

**查询参数**:
- `city` (必填): 城市代码，如 `beijing`, `shanghai`, `guangzhou` 等
- `bizcircle` (可选): 商圈名称，如 `中关村`, `北蔡` 等
- `start_year` (可选): 起始年份，默认 `2023`
- `end_year` (可选): 结束年份，默认 `2025`

**返回格式**:
```json
{
  "ok": true,
  "source": "mysql",  // 或 "json"
  "city": "beijing",
  "bizcircle": "中关村",  // 如果指定了商圈
  "data": [
    {
      "year": 2023,
      "avg_unit_price_yuan_sqm": 85000,
      "avg_total_price_wan": 520.5,
      "count": 1234
    },
    {
      "year": 2024,
      "avg_unit_price_yuan_sqm": 88000,
      "avg_total_price_wan": 540.2,
      "count": 1456
    },
    {
      "year": 2025,
      "avg_unit_price_yuan_sqm": 90000,
      "avg_total_price_wan": 560.8,
      "count": 987
    }
  ]
}
```

**示例请求**:
```bash
# 查询北京市整体历史均价
curl "http://127.0.0.1:5000/api/historical_avg_price?city=beijing"

# 查询北京市中关村商圈历史均价
curl "http://127.0.0.1:5000/api/historical_avg_price?city=beijing&bizcircle=中关村"

# 查询上海市 2024-2025 年历史均价
curl "http://127.0.0.1:5000/api/historical_avg_price?city=shanghai&start_year=2024&end_year=2025"
```

---

### 2. 获取城市商圈列表

**端点**: `GET /api/bizcircles`

**描述**: 获取指定城市的所有商圈列表（用于前端下拉选择）

**查询参数**:
- `city` (必填): 城市代码

**返回格式**:
```json
{
  "ok": true,
  "source": "mysql",  // 或 "json"
  "city": "beijing",
  "bizcircles": [
    "安定门",
    "北蔡",
    "中关村",
    "望京",
    ...
  ]
}
```

**示例请求**:
```bash
# 获取北京市所有商圈
curl "http://127.0.0.1:5000/api/bizcircles?city=beijing"
```

---

## 前端集成示例

### JavaScript 调用示例

```javascript
// 获取历史均价统计
async function fetchHistoricalAvgPrice(city, bizcircle = null) {
  const params = new URLSearchParams({ city });
  if (bizcircle) params.append('bizcircle', bizcircle);
  
  const response = await fetch(`/api/historical_avg_price?${params}`);
  const data = await response.json();
  
  if (data.ok) {
    console.log('历史均价数据:', data.data);
    // 渲染图表或表格
    renderHistoricalChart(data.data);
  }
}

// 获取商圈列表
async function fetchBizcircles(city) {
  const response = await fetch(`/api/bizcircles?city=${city}`);
  const data = await response.json();
  
  if (data.ok) {
    console.log('商圈列表:', data.bizcircles);
    // 填充下拉选择框
    populateBizcircleSelect(data.bizcircles);
  }
}

// 使用示例
fetchHistoricalAvgPrice('beijing');  // 北京整体
fetchHistoricalAvgPrice('beijing', '中关村');  // 北京中关村商圈
fetchBizcircles('shanghai');  // 获取上海所有商圈
```

---

## 数据源说明

- **MySQL 模式**: 当数据库可用时，从 `transactions` 表实时聚合统计
- **JSON 模式**: 当数据库不可用时，从 `data/crawl_history_*.json` 文件读取并统计

两种模式返回的数据格式完全一致，前端无需关心数据来源。

---

## 技术实现

### 后端模块
- `backend/statistics.py`: 核心统计逻辑
  - `get_historical_avg_price_from_db()`: 从数据库统计
  - `get_historical_avg_price_from_json()`: 从 JSON 统计
  - `get_available_bizcircles_from_db()`: 从数据库获取商圈列表
  - `get_available_bizcircles_from_json()`: 从 JSON 获取商圈列表

- `backend/app.py`: API 路由注册
  - `/api/historical_avg_price`: 历史均价统计接口
  - `/api/bizcircles`: 商圈列表接口

### 统计维度
- **时间维度**: 按年度（year）聚合
- **空间维度**: 城市（city）+ 商圈（bizcircle，可选）
- **指标维度**: 
  - 平均单价（元/㎡）
  - 平均总价（万元）
  - 样本数量

---

## 测试建议

1. **启动后端服务**:
   ```bash
   cd backend
   python app.py
   ```

2. **测试 API**:
   - 浏览器访问: `http://127.0.0.1:5000/api/historical_avg_price?city=beijing`
   - 或使用 Postman/curl 测试

3. **验证数据**:
   - 检查返回的 `data` 数组是否包含 2023-2025 年度数据
   - 检查 `count` 字段确认样本数量
   - 对比不同商圈的均价差异
