<script setup>
import { ref, computed, onMounted } from 'vue'
import { fetchCities, fetchHouses, fetchPriceTrend } from './api'
import HouseFilter from './components/HouseFilter.vue'
import HouseTable from './components/HouseTable.vue'
import PriceChart from './components/PriceChart.vue'

const cities = ref([])
const selectedCityId = ref(null)
const houses = ref([])
const priceTrend = ref([])
const loading = ref(false)

const filters = ref({
  district: '',
  house_type: ''
})

const selectedCity = computed(() =>
  cities.value.find((c) => c.id === selectedCityId.value)
)

async function initData() {
  loading.value = true
  try {
    const cityList = await fetchCities()
    cities.value = cityList
    if (cityList.length) {
      selectedCityId.value = cityList[0].id
      await Promise.all([loadHouses(), loadPriceTrend()])
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function loadHouses() {
  if (!selectedCityId.value) return
  loading.value = true
  try {
    const data = await fetchHouses({
      city_id: selectedCityId.value,
      district: filters.value.district,
      house_type: filters.value.house_type
    })
    houses.value = data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function loadPriceTrend() {
  if (!selectedCityId.value) return
  try {
    const data = await fetchPriceTrend(selectedCityId.value)
    priceTrend.value = data
  } catch (e) {
    console.error(e)
  }
}

function handleCityChange(cityId) {
  selectedCityId.value = cityId
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
        <div class="logo">HPQAQ · 房价大盘</div>
        <nav class="nav-links">
          <span class="nav-link active">房价大盘</span>
          <span class="nav-link">成交记录</span>
          <span class="nav-link">城市排行</span>
        </nav>
      </div>
      <div class="navbar-right">
        <span class="nav-subtitle">中国一线 & 台湾城市房价趋势分析</span>
      </div>
    </header>

    <main class="main">
      <aside class="sidebar">
        <HouseFilter
          :cities="cities"
          :selectedCityId="selectedCityId"
          :filters="filters"
          @update:city="handleCityChange"
          @update:filters="handleFilterChange"
        />

        <section v-if="selectedCity" class="city-card">
          <h3>{{ selectedCity.name }}</h3>
          <p>区域：{{ selectedCity.region === 'cn' ? '中国大陆' : '台湾地区' }}</p>
          <p>等级：{{ selectedCity.level || '—' }}</p>
          <p class="city-tip">数据源：爬虫定期抓取房价与成交记录</p>
        </section>
      </aside>

      <section class="content">
        <section class="panel panel-chart">
          <div class="panel-header">
            <h2>
              {{ selectedCity ? selectedCity.name : '城市' }} · 近三年价格走势
            </h2>
            <span v-if="loading" class="tag">加载中...</span>
          </div>
          <PriceChart :data="priceTrend" />
        </section>

        <section class="panel panel-table">
          <div class="panel-header">
            <h2>
              {{ selectedCity ? selectedCity.name : '城市' }} · 房源列表
            </h2>
            <span class="panel-subtitle">
              共 {{ houses.length }} 条记录
            </span>
          </div>
          <HouseTable :houses="houses" />
        </section>
      </section>
    </main>
  </div>
</template>

<style scoped>
.layout {
  min-height: 100vh;
  background: #0f172a;
  color: #e5e7eb;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.navbar {
  height: 56px;
  padding: 0 24px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.3);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: radial-gradient(circle at top left, #1e293b, #020617);
}

.navbar-left {
  display: flex;
  align-items: center;
  gap: 24px;
}

.logo {
  font-weight: 700;
  font-size: 18px;
  color: #38bdf8;
}

.nav-links {
  display: flex;
  gap: 12px;
  font-size: 14px;
  color: #94a3b8;
}

.nav-link {
  padding: 4px 8px;
  border-radius: 999px;
  cursor: default;
}

.nav-link.active {
  background: rgba(56, 189, 248, 0.1);
  color: #e5e7eb;
}

.navbar-right {
  font-size: 13px;
  color: #64748b;
}

.main {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 16px;
  padding: 16px 24px 24px;
}

.sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.city-card {
  padding: 12px 14px;
  border-radius: 12px;
  background: linear-gradient(145deg, #0b1120, #020617);
  border: 1px solid rgba(148, 163, 184, 0.4);
  font-size: 13px;
}

.city-card h3 {
  margin-bottom: 8px;
  font-size: 15px;
}

.city-tip {
  margin-top: 8px;
  color: #64748b;
}

.content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel {
  border-radius: 14px;
  background: #020617;
  border: 1px solid rgba(30, 64, 175, 0.6);
  padding: 14px 16px 12px;
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.9);
}

.panel-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 8px;
}

.panel-header h2 {
  font-size: 16px;
  font-weight: 600;
}

.panel-subtitle {
  font-size: 12px;
  color: #64748b;
}

.tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.2);
  color: #e5e7eb;
}

/* 简单响应式 */
@media (max-width: 900px) {
  .main {
    grid-template-columns: 1fr;
  }
}
</style>
