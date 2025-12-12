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

  // 处理从新API获取的数据格式
  const months = props.data.map((d) => d.month)
  const unitPrices = props.data.map((d) => d.avg_unit_price)
  const totalPrices = props.data.map((d) => d.avg_total_price)

  const option = {
    backgroundColor: 'transparent',
    grid: {
      left: 40,
      right: 40,
      top: 40,
      bottom: 40
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        let result = params[0].name + '<br/>'
        params.forEach(param => {
          result += `${param.marker}${param.seriesName}: ${param.value.toLocaleString()}<br/>`
        })
        return result
      }
    },
    legend: {
      data: ['平均单价', '平均总价'],
      textStyle: {
        color: '#9ca3af',
        fontSize: 11
      },
      top: 0
    },
    xAxis: {
      type: 'category',
      data: months,
      boundaryGap: false,
      axisLine: { lineStyle: { color: '#4b5563' } },
      axisLabel: {
        color: '#9ca3af',
        fontSize: 11,
        rotate: 45
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '平均单价',
        nameTextStyle: {
          color: '#9ca3af',
          fontSize: 11
        },
        axisLine: { show: false },
        splitLine: { lineStyle: { color: '#1f2937' } },
        axisLabel: {
          color: '#9ca3af',
          fontSize: 11,
          formatter: '{value}'
        }
      },
      {
        type: 'value',
        name: '平均总价(万元)',
        nameTextStyle: {
          color: '#9ca3af',
          fontSize: 11
        },
        axisLine: { show: false },
        splitLine: { show: false },
        axisLabel: {
          color: '#9ca3af',
          fontSize: 11,
          formatter: '{value}'
        }
      }
    ],
    series: [
      {
        name: '平均单价',
        type: 'line',
        data: unitPrices,
        smooth: true,
        showSymbol: false,
        lineStyle: {
          width: 2,
          color: '#38bdf8'
        },
        areaStyle: {
          opacity: 0.25,
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [{
              offset: 0, color: 'rgba(56, 189, 248, 0.5)'
            }, {
              offset: 1, color: 'rgba(56, 189, 248, 0.0)'
            }]
          }
        },
        yAxisIndex: 0
      },
      {
        name: '平均总价',
        type: 'line',
        data: totalPrices,
        smooth: true,
        showSymbol: false,
        lineStyle: {
          width: 2,
          color: '#fbbf24'
        },
        areaStyle: {
          opacity: 0.25,
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [{
              offset: 0, color: 'rgba(251, 191, 36, 0.5)'
            }, {
              offset: 1, color: 'rgba(251, 191, 36, 0.0)'
            }]
          }
        },
        yAxisIndex: 1
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
