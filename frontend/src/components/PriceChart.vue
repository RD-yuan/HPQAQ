<script setup>
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: { type: Array, default: () => [] }
})

const chartRef = ref(null)
let chartInstance = null

function initChart() {
  if (!chartRef.value) return
  chartInstance = echarts.init(chartRef.value)

  window.addEventListener('resize', resizeChart)
  updateChart()
}

function resizeChart() {
  if (chartInstance) {
    chartInstance.resize()
  }
}

function updateChart() {
  if (!chartInstance) return

  const months = props.data.map((d) => `${d.year}-${String(d.month).padStart(2, '0')}`)
  const prices = props.data.map((d) => d.avg_unit_price)

  const option = {
    backgroundColor: 'transparent',
    grid: {
      left: 40,
      right: 20,
      top: 30,
      bottom: 30
    },
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: months,
      boundaryGap: false,
      axisLine: { lineStyle: { color: '#4b5563' } },
      axisLabel: { color: '#9ca3af', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#1f2937' } },
      axisLabel: { color: '#9ca3af', fontSize: 11 }
    },
    series: [
      {
        type: 'line',
        data: prices,
        smooth: true,
        showSymbol: false,
        lineStyle: {
          width: 2
        },
        areaStyle: {
          opacity: 0.25
        }
      }
    ]
  }

  chartInstance.setOption(option)
}

onMounted(() => {
  initChart()
})

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.dispose()
  }
  window.removeEventListener('resize', resizeChart)
})

watch(
  () => props.data,
  () => {
    if (chartInstance) {
      updateChart()
    }
  },
  { deep: true }
)
</script>

<template>
  <div class="chart-container">
    <div ref="chartRef" class="chart"></div>
    <p v-if="!data.length" class="empty-tip">暂无价格走势数据</p>
  </div>
</template>

<style scoped>
.chart-container {
  position: relative;
  height: 260px;
}

.chart {
  width: 100%;
  height: 100%;
}

.empty-tip {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #6b7280;
}
</style>
