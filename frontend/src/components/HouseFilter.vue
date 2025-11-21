<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({
  cities: { type: Array, default: () => [] },
  selectedCityId: { type: Number, default: null },
  filters: {
    type: Object,
    default: () => ({ district: '', house_type: '' })
  }
})

const emit = defineEmits(['update:city', 'update:filters'])

const localFilters = reactive({
  district: '',
  house_type: ''
})

watch(
  () => props.filters,
  (val) => {
    if (!val) return
    localFilters.district = val.district || ''
    localFilters.house_type = val.house_type || ''
  },
  { immediate: true, deep: true }
)

function onCityChange(e) {
  const id = Number(e.target.value)
  emit('update:city', id)
}

function onFilterChange() {
  emit('update:filters', { ...localFilters })
}
</script>

<template>
  <section class="filter-card">
    <h3 class="title">筛选条件</h3>

    <div class="field">
      <label>城市</label>
      <select :value="selectedCityId ?? ''" @change="onCityChange">
        <option value="" disabled>请选择城市</option>
        <option v-for="c in cities" :key="c.id" :value="c.id">
          {{ c.name }}（{{ c.region === 'cn' ? '大陆' : '台湾' }}）
        </option>
      </select>
    </div>

    <div class="field">
      <label>区域</label>
      <input
        v-model="localFilters.district"
        @input="onFilterChange"
        placeholder="如 海淀, 南山区"
      />
    </div>

    <div class="field">
      <label>房型</label>
      <input
        v-model="localFilters.house_type"
        @input="onFilterChange"
        placeholder="如 二室一厅"
      />
    </div>

    <p class="hint">
      提示：区域、房型支持模糊匹配，将在后端 SQL 中使用 LIKE 检索。
    </p>
  </section>
</template>

<style scoped>
.filter-card {
  padding: 14px 14px 10px;
  border-radius: 14px;
  background: radial-gradient(circle at top, #020617, #020617);
  border: 1px solid rgba(148, 163, 184, 0.6);
  font-size: 13px;
}

.title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 10px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 10px;
}

label {
  color: #9ca3af;
  font-size: 12px;
}

input,
select {
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px solid #1f2937;
  background: #020617;
  color: #e5e7eb;
  font-size: 13px;
  outline: none;
}

input:focus,
select:focus {
  border-color: #38bdf8;
}

.hint {
  margin-top: 4px;
  font-size: 11px;
  color: #64748b;
  line-height: 1.4;
}
</style>
