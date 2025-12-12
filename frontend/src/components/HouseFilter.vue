<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({
  selectedCity: { type: String, default: null },
  filters: {
    type: Object,
    default: () => ({ district: '', house_type: '', min_price: '', max_price: '', min_area: '', max_area: '' })
  }
})

const emit = defineEmits(['update:city', 'update:filters'])

const localFilters = reactive({
  district: '',
  house_type: '',
  min_price: '',
  max_price: '',
  min_area: '',
  max_area: ''
})

// 支持的城市列表
const cities = [
  { name: '北京' },
  { name: '上海' },
  { name: '杭州' },
  { name: '深圳' }
]

watch(
  () => props.filters,
  (val) => {
    if (!val) return
    localFilters.district = val.district || ''
    localFilters.house_type = val.house_type || ''
    localFilters.min_price = val.min_price || ''
    localFilters.max_price = val.max_price || ''
    localFilters.min_area = val.min_area || ''
    localFilters.max_area = val.max_area || ''
  },
  { immediate: true, deep: true }
)

function onCityChange(e) {
  const city = e.target.value
  emit('update:city', city)
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
      <select :value="selectedCity ?? ''" @change="onCityChange">
        <option value="" disabled>请选择城市</option>
        <option v-for="c in cities" :key="c.name" :value="c.name">
          {{ c.name }}
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

    <div class="field-row">
      <div class="field field-half">
        <label>最低总价(万元)</label>
        <input
          v-model="localFilters.min_price"
          @input="onFilterChange"
          type="number"
          placeholder="0"
        />
      </div>
      <div class="field field-half">
        <label>最高总价(万元)</label>
        <input
          v-model="localFilters.max_price"
          @input="onFilterChange"
          type="number"
          placeholder="不限"
        />
      </div>
    </div>

    <div class="field-row">
      <div class="field field-half">
        <label>最小面积(㎡)</label>
        <input
          v-model="localFilters.min_area"
          @input="onFilterChange"
          type="number"
          placeholder="0"
        />
      </div>
      <div class="field field-half">
        <label>最大面积(㎡)</label>
        <input
          v-model="localFilters.max_area"
          @input="onFilterChange"
          type="number"
          placeholder="不限"
        />
      </div>
    </div>

    <p class="hint">
      提示：区域、房型支持模糊匹配，价格和面积支持范围筛选。
    </p>
  </section>
</template>

<style scoped>
.filter-card {
  padding: 14px 14px 10px;
  border-radius: 14px;
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.1);
  font-size: 13px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 10px;
  color: #000000;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 10px;
}

.field-row {
  display: flex;
  gap: 8px;
  width: 100%;
}

.field-half {
  flex: 1;
  width: calc(50% - 4px); /* 减去gap的一半，确保两个元素加上gap正好是100% */
}

label {
  color: rgba(0, 0, 0, 0.7);
  font-size: 12px;
}

input,
select {
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.2);
  background: #ffffff;
  color: #000000;
  font-size: 13px;
  outline: none;
  width: 100%;
  box-sizing: border-box;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

input:focus,
select:focus {
  border-color: rgba(255, 255, 255, 0.6);
}

.hint {
  margin-top: 4px;
  font-size: 11px;
  color: rgba(0, 0, 0, 0.5);
  line-height: 1.4;
}
</style>
