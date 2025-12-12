<script setup>
import { ref, computed, onMounted } from 'vue'
import { fetchHouses, fetchPriceTrend } from './api'
import HouseFilter from './components/HouseFilter.vue'
import HouseTable from './components/HouseTable.vue'
import PriceChart from './components/PriceChart.vue'
import StatisticsPanel from './components/StatisticsPanel.vue'

const selectedCity = ref('北京') // 默认选择北京
const houses = ref([])
const priceTrend = ref([])
const loading = ref(false)
const totalCount = ref(0)
const activeTab = ref('statistics')
const timeRange = ref(12) // 默认显示12个月的数据

const filters = ref({
  district: '',
  house_type: '',
  min_price: '',
  max_price: '',
  min_area: '',
  max_area: ''
})

const selectedCityName = computed(() => selectedCity.value)

async function initData() {
  loading.value = true
  try {
    await Promise.all([loadHouses(), loadPriceTrend()])
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function loadHouses() {
  if (!selectedCity.value) return
  loading.value = true
  try {
    // 构建查询参数
    const params = {
      city: selectedCity.value,
      district: filters.value.district,
      house_type: filters.value.house_type,
      min_price: filters.value.min_price,
      max_price: filters.value.max_price,
      min_area: filters.value.min_area,
      max_area: filters.value.max_area,
      page: 1,
      page_size: 50 // 每页显示50条数据
    }
    
    const response = await fetchHouses(params)
    if (response.code === 200) {
      houses.value = response.data.houses
      totalCount.value = response.data.total_count
    } else {
      console.error('获取房源数据失败:', response.message)
      houses.value = []
      totalCount.value = 0
    }
  } catch (e) {
    console.error('获取房源数据时发生错误:', e)
    houses.value = []
    totalCount.value = 0
  } finally {
    loading.value = false
  }
}

async function loadPriceTrend() {
  if (!selectedCity.value) return
  try {
    const response = await fetchPriceTrend(selectedCity.value, timeRange.value) // 获取指定时间范围的数据
    if (response.code === 200) {
      priceTrend.value = response.data
    } else {
      console.error('获取价格走势数据失败:', response.message)
      priceTrend.value = []
    }
  } catch (e) {
    console.error('获取价格走势数据时发生错误:', e)
    priceTrend.value = []
  }
}

function handleCityChange(city) {
  selectedCity.value = city
  loadHouses()
  loadPriceTrend()
}

function handleFilterChange(newFilters) {
  filters.value = newFilters
  loadHouses()
}

onMounted(() => {
  initData()
})
</script>

<template>
  <div class="layout">
    <!-- 顶部导航栏，仿 csqaq -->
    <header class="navbar">
      <div class="navbar-left">
        <div class="logo">房价趋势分析</div>
        <nav class="nav-links">
          <span 
            :class="['nav-link', { active: activeTab === 'statistics' }]"
            @click="activeTab = 'statistics'"
          >
            统计面板
          </span>
          <span 
            :class="['nav-link', { active: activeTab === 'data' }]"
            @click="activeTab = 'data'"
          >
            房源数据
          </span>
        </nav>
      </div>
      <div class="navbar-right">
        <span class="nav-subtitle">中国一线城市房价趋势分析</span>
      </div>
    </header>

    <main class="main" :class="{ 'no-sidebar': activeTab === 'statistics' }">
      <aside class="sidebar" v-if="activeTab !== 'statistics'">
        <HouseFilter
          :selectedCity="selectedCity"
          :filters="filters"
          @update:city="handleCityChange"
          @update:filters="handleFilterChange"
        />
      </aside>

      <section class="content">
        <!-- 统计面板 -->
        <template v-if="activeTab === 'statistics'">
          <!-- 价格走势放在上面 -->
          <div class="panel panel-chart">
            <div class="panel-header">
              <div class="chart-header-top">
                <h2>
                  {{ selectedCityName }} · 价格走势
                </h2>
                <div class="city-selector-inline">
                  <label>选择城市：</label>
                  <select :value="selectedCity" @change="handleCityChange($event.target.value)">
                    <option value="" disabled>请选择城市</option>
                    <option v-for="city in ['北京', '上海', '杭州', '深圳']" :key="city" :value="city">
                      {{ city }}
                    </option>
                  </select>
                </div>
              </div>
              <div class="time-range-selector">
                <button 
                  v-for="range in [3, 6, 12, 36]" 
                  :key="range"
                  :class="['time-btn', { active: timeRange === range }]"
                  @click="timeRange = range; loadPriceTrend()"
                >
                  {{ range === 3 ? '3个月' : range === 6 ? '6个月' : range === 12 ? '1年' : '3年' }}
                </button>
              </div>
            </div>
            <PriceChart :data="priceTrend" />
          </div>

          <!-- 房价排行放在下面 -->
          <div class="panel panel-stats">
            <StatisticsPanel />
          </div>
        </template>

        <!-- 房源数据面板 -->
        <template v-if="activeTab === 'data'">
          <div class="panel panel-table">
            <div class="panel-header">
              <h2>
                {{ selectedCityName }} · 房源列表
              </h2>
              <span class="panel-subtitle">
                共 {{ totalCount }} 条记录
              </span>
            </div>
            <HouseTable :houses="houses" />
          </div>
        </template>
      </section>
    </main>
  </div>
</template>

<style scoped>
.layout {
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  color: #333333;
  background: #f5f5f5;
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.navbar {
  height: 56px;
  padding: 0 24px;
  border-bottom: 1px solid rgba(0, 174, 102, 0.3);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #00ae66;
  backdrop-filter: blur(10px);
}

.navbar-left {
  display: flex;
  align-items: center;
  gap: 24px;
}

.logo {
  font-weight: 700;
  font-size: 18px;
  color: #333333;
}

.nav-links {
  display: flex;
  gap: 12px;
  font-size: 14px;
  color: #666666;
}

.nav-link {
  padding: 4px 8px;
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.nav-link:hover {
  background: rgba(0, 0, 0, 0.05);
}

.nav-link.active {
  background: #333333;
  color: #ffffff;
  font-weight: 500;
}

.navbar-right {
  font-size: 13px;
  color: #64748b;
}

.main {
  display: flex;
  gap: 16px;
  padding: 16px 0 24px;
  background: #f5f5f5;
  height: calc(100vh - 60px);
  width: 100%;
  box-sizing: border-box;
  overflow: hidden;
}

.sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 320px;
  margin: 0 24px;
  flex-shrink: 0;
}

.content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: calc(100% - 48px);
  height: 100%;
  min-height: 0;
  box-sizing: border-box;
  flex: 1;
  margin: 0 auto;
}

/* 当侧边栏隐藏时（统计面板），让内容区域完全铺满 */
.main.no-sidebar .content {
  width: 100%;
  margin: 0;
}

.panel {
  border-radius: 14px;
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.1);
  padding: 14px 16px 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  width: 100%;
  box-sizing: border-box;
  overflow: hidden;
}

.panel-chart {
  width: 100%;
  flex: 1;
  min-height: 300px;
  box-sizing: border-box;
}

.panel-stats {
  width: 100%;
  box-sizing: border-box;
}

.panel-table {
  width: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.panel-header {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
  flex-shrink: 0;
}

.chart-header-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.city-selector-inline {
  display: flex;
  align-items: center;
  gap: 8px;
}

.city-selector-inline label {
  font-size: 13px;
  font-weight: 500;
  color: #64748b;
}

.city-selector-inline select {
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  background: #f5f5f5;
  color: #333;
  font-size: 13px;
  outline: none;
  width: auto;
}

.time-range-selector {
  display: flex;
  gap: 8px;
}

.time-btn {
  padding: 6px 12px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  background: #f5f5f5;
  color: #333;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.time-btn:hover {
  background: #e0e0e0;
}

.time-btn.active {
  background: #00ae66;
  color: white;
  border-color: #00ae66;
}

.panel-header h2 {
  font-size: 16px;
  font-weight: 600;
}

.panel-subtitle {
  font-size: 12px;
  color: #666666;
}

.tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(0, 174, 102, 0.1);
  color: #00ae66;
}

.nav-link {
  padding: 4px 8px;
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-link:hover {
  background: rgba(56, 189, 248, 0.05);
}

.nav-link.active {
  background: rgba(56, 189, 248, 0.1);
  color: #e5e7eb;
}

/* 表格样式增强 */
.house-title {
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 简单响应式 */
@media (max-width: 900px) {
  .main {
    grid-template-columns: 1fr;
    padding: 16px 16px 24px;
  }
  
  .sidebar {
    margin: 0;
  }
  
  .content {
    margin: 0;
  }
  
  .statistics-layout {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .panel-stats {
    grid-column: 1;
  }
}
</style>
