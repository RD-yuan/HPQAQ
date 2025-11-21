<script setup>
const props = defineProps({
  houses: { type: Array, default: () => [] }
})
</script>

<template>
  <div class="table-wrapper">
    <table class="table">
      <thead>
        <tr>
          <th>城市</th>
          <th>区域</th>
          <th>房型</th>
          <th>面积(m²)</th>
          <th>单价(元/m²)</th>
          <th>总价(万元)</th>
          <th>楼层</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="!houses.length">
          <td colspan="7" class="empty">暂无数据</td>
        </tr>
        <tr v-for="h in houses" :key="h.id">
          <td>{{ h.city }}</td>
          <td>{{ h.district }}</td>
          <td>{{ h.house_type }}</td>
          <td>{{ h.area }}</td>
          <td>{{ h.unit_price }}</td>
          <td>{{ h.total_price }}</td>
          <td>{{ h.floor }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.table-wrapper {
  max-height: 360px;
  overflow: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

th,
td {
  padding: 6px 8px;
  text-align: center;
  border-bottom: 1px solid rgba(30, 64, 175, 0.5);
}

thead {
  background: rgba(15, 23, 42, 0.9);
  position: sticky;
  top: 0;
  z-index: 1;
}

th {
  font-weight: 500;
  color: #9ca3af;
}

tbody tr:nth-child(odd) {
  background: rgba(15, 23, 42, 0.6);
}

tbody tr:nth-child(even) {
  background: rgba(15, 23, 42, 0.3);
}

tbody tr:hover {
  background: rgba(56, 189, 248, 0.12);
}

.empty {
  padding: 20px 0;
  color: #6b7280;
}
</style>
