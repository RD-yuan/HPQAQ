<script setup>
import { ref, onMounted } from 'vue'
import { fetchCityStatistics } from '../api'

const cityStats = ref([])
const loading = ref(false)

async function loadCityStatistics() {
  loading.value = true
  try {
    const response = await fetchCityStatistics()
    if (response.code === 200) {
      cityStats.value = response.data
    }
  } catch (e) {
    console.error('获取城市统计数据失败:', e)
    cityStats.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadCityStatistics()
})
</script>

<template>
  <div class="statistics-panel">
    <h3 class="section-title">城市房价排行</h3>
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else class="city-rankings">
      <div v-for="(city, index) in cityStats.slice(0, 5)" :key="city.city" class="city-item">
        <div class="city-rank">{{ index + 1 }}</div>
        <div class="city-info">
          <div class="city-name">{{ city.city }}</div>
          <div class="city-stats">
            <span class="stat">{{ city.total_count }}套</span>
            <span class="stat">均价{{ city.avg_unit_price?.toLocaleString() }}元/㎡</span>
          </div>
        </div>
        <div class="city-price">
          {{ city.avg_total_price?.toFixed(1) }}万
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.statistics-panel {
  padding: 14px;
  border-radius: 14px;
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

/* 移除不必要的section样式 */

.section-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #000000;
}

.loading {
  text-align: center;
  color: #64748b;
  font-size: 13px;
  padding: 20px 0;
}

.city-rankings {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.city-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: 8px;
  background: #f8f8f8;
  transition: background 0.2s;
}

.city-item:hover {
  background: #f0f0f0;
}

.city-rank {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: linear-gradient(135deg, #38bdf8, #0ea5e9);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.city-info {
  flex: 1;
}

.city-name {
  font-weight: 500;
  font-size: 13px;
  margin-bottom: 2px;
}

.city-stats {
  display: flex;
  gap: 8px;
  font-size: 11px;
  color: #94a3b8;
}

.city-price {
  font-weight: 600;
  font-size: 13px;
  color: #fbbf24;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
}

.field label {
  color: #000000;
  font-size: 12px;
}

.field select {
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.2);
  background: #ffffff;
  color: #000000;
  font-size: 13px;
  outline: none;
  width: 100%;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.field select:focus {
  border-color: #38bdf8;
}

.district-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.district-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 8px;
  border-radius: 6px;
  background: #f8f8f8;
  font-size: 12px;
}

.district-name {
  font-weight: 500;
}

.district-stats {
  display: flex;
  gap: 8px;
  color: #94a3b8;
}

.stat {
  font-size: 11px;
}
</style>