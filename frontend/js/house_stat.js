(() => {
  const $ = (id) => document.getElementById(id);

  const els = {
    // navbar
    navCity: $("nav-city"),
    navRefresh: $("nav-refresh"),
    badgeApi: $("badge-api"),
    badgeCities: $("badge-cities"),

    // filters
    chip: $("chip"),
    filterDesc: $("filter-desc"),
    btnModeSingle: $("btn-mode-single"),
    btnModeCompare: $("btn-mode-compare"),
    formSingle: $("form-single"),
    formCompare: $("form-compare"),
    statCity: $("stat-city"),
    statBizcircle: $("stat-bizcircle"),
    statStartYear: $("stat-start-year"),
    statStartMonth: $("stat-start-month"),
    statEndYear: $("stat-end-year"),
    statEndMonth: $("stat-end-month"),
    btnStatQuery: $("btn-stat-query"),
    btnQueryText: $("btn-query-text"),
    btnStatReset: $("btn-stat-reset"),
    statMeta: $("stat-meta"),

    // compare mode
    compareType: $("compare-type"),
    compareCitiesSection: $("compare-cities-section"),
    compareBizcirclesSection: $("compare-bizcircles-section"),
    compareCitiesCheckboxes: $("compare-cities-checkboxes"),
    compareCityBase: $("compare-city-base"),
    compareBizcirclesCheckboxes: $("compare-bizcircles-checkboxes"),
    compareStartYear: $("compare-start-year"),
    compareStartMonth: $("compare-start-month"),
    compareEndYear: $("compare-end-year"),
    compareEndMonth: $("compare-end-month"),

    // results
    statResultDesc: $("stat-result-desc"),
    statEmpty: $("stat-empty"),
    statContent: $("stat-content"),
    chartContainer: $("chart-container"),
    statChart: $("stat-chart"),
    statTableWrap: $("stat-table-wrap"),
    statTbody: $("stat-tbody"),

    // view buttons
    btnViewBar: $("btn-view-bar"),
    btnViewLine: $("btn-view-line"),
    btnViewBox: $("btn-view-box"),
    btnViewTable: $("btn-view-table"),

    // ui
    toast: $("toast"),
  };

  const state = {
    cities: [],
    loading: false,
    chartInstance: null,
    currentData: null,
    currentView: 'bar',
    mode: 'single', // 'single' or 'compare'
    compareData: null,
  };

  // ===== 城市显示名 =====
  const CITY_LABELS = {
    beijing: "北京",
    shanghai: "上海",
    guangzhou: "广州",
    shenzhen: "深圳",
    tianjin: "天津",
    taibei: "台北",
    xinbei: "新北",
  };

  function cityName(key) {
    if (!key) return "-";
    const k = String(key).toLowerCase();
    return CITY_LABELS[k] || k;
  }

  // ===== Toast 提示 =====
  function toast(msg) {
    if (!els.toast) return;
    els.toast.textContent = msg;
    els.toast.classList.add("show");
    setTimeout(() => els.toast.classList.remove("show"), 3000);
  }

  function setMeta(text) {
    if (els.statMeta) els.statMeta.textContent = text;
  }

  // ===== API 请求 =====
  async function apiGet(path, params = {}) {
    const qs = new URLSearchParams(params).toString();
    const url = qs ? `${path}?${qs}` : path;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  // ===== 数字格式化 =====
  function fmtNum0(n) {
    if (n == null || n === "") return "-";
    return Number(n).toLocaleString("zh-CN", { maximumFractionDigits: 0 });
  }

  function fmtPrice(n) {
    if (n == null || n === "") return "-";
    return Number(n).toLocaleString("zh-CN", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }

  // ===== 加载城市列表 =====
  async function loadHealthAndCities() {
    try {
      const data = await apiGet("/api/health");
      state.cities = data.cities || [];

      // 填充城市下拉框
      if (els.statCity) {
        els.statCity.innerHTML = '<option value="">请选择城市</option>';
        state.cities.forEach((code) => {
          const opt = document.createElement("option");
          opt.value = code;
          opt.textContent = cityName(code);
          els.statCity.appendChild(opt);
        });
      }

      // 同步 navbar 城市选择
      if (els.navCity) {
        els.navCity.innerHTML = "";
        state.cities.forEach((code) => {
          const opt = document.createElement("option");
          opt.value = code;
          opt.textContent = cityName(code);
          els.navCity.appendChild(opt);
        });
      }

      // 更新 badge
      if (els.badgeApi) els.badgeApi.textContent = `API：${data.db || "OK"}`;
      if (els.badgeCities) {
        const names = state.cities.map(cityName).join("、");
        els.badgeCities.textContent = `城市：${names}`;
      }

      if (els.chip) els.chip.textContent = "数据接口已连接";
    } catch (e) {
      if (els.badgeApi) els.badgeApi.textContent = "API：异常";
      if (els.chip) els.chip.textContent = "数据接口异常";
      throw e;
    }
  }

  // ===== 加载商圈列表 =====
  async function loadBizcircles(city, isCompareMode = false) {
    if (!city) return;

    try {
      const data = await apiGet("/api/bizcircles", { city });
      const bizcircles = data.bizcircles || [];

      if (isCompareMode && els.compareBizcirclesCheckboxes) {
        // 对比模式：生成复选框列表
        els.compareBizcirclesCheckboxes.innerHTML = '';
        bizcircles.forEach((biz) => {
          const label = document.createElement('label');
          label.style.cssText = 'display: flex; align-items: center; gap: 0.5rem; cursor: pointer; padding: 0.5rem; border-radius: 4px; transition: background 0.2s;';
          label.onmouseover = () => label.style.background = 'rgba(255,255,255,0.05)';
          label.onmouseout = () => label.style.background = 'transparent';
          
          const checkbox = document.createElement('input');
          checkbox.type = 'checkbox';
          checkbox.value = biz;
          checkbox.className = 'compare-bizcircle-checkbox';
          checkbox.style.cssText = 'cursor: pointer;';
          
          const span = document.createElement('span');
          span.textContent = biz;
          span.style.cssText = 'color: rgba(234,240,255,0.9); font-size: 0.9rem;';
          
          label.appendChild(checkbox);
          label.appendChild(span);
          els.compareBizcirclesCheckboxes.appendChild(label);
        });
      } else if (els.statBizcircle) {
        // 单选模式
        els.statBizcircle.innerHTML = '<option value="">全市整体</option>';
        bizcircles.forEach((biz) => {
          const opt = document.createElement("option");
          opt.value = biz;
          opt.textContent = biz;
          els.statBizcircle.appendChild(opt);
        });
      }
    } catch (e) {
      console.error("Failed to load bizcircles:", e);
      if (!isCompareMode && els.statBizcircle) {
        els.statBizcircle.innerHTML = '<option value="">全市整体</option>';
      }
    }
  }

  // ===== 查询历史均价 =====
  async function queryHistoricalAvgPrice() {
    if (state.mode === 'compare') {
      queryCompareData();
      return;
    }

    const city = els.statCity?.value;
    if (!city) {
      toast("请先选择城市");
      return;
    }

    const bizcircle = els.statBizcircle?.value || null;
    const startYear = els.statStartYear?.value || "2023";
    const startMonth = els.statStartMonth?.value || "01";
    const endYear = els.statEndYear?.value || "2025";
    const endMonth = els.statEndMonth?.value || "12";
    
    const startMonthStr = `${startYear}-${startMonth}`;
    const endMonthStr = `${endYear}-${endMonth}`;

    if (startMonthStr > endMonthStr) {
      toast("起始时间不能晚于结束时间");
      return;
    }

    state.loading = true;
    setMeta("查询中...");

    try {
      const params = { city, start_month: startMonthStr, end_month: endMonthStr };
      if (bizcircle) params.bizcircle = bizcircle;

      const result = await apiGet("/api/historical_avg_price", params);

      if (!result.ok) {
        toast("查询失败");
        setMeta("查询失败");
        return;
      }

      renderStatisticsTable(result.data, city, bizcircle, startMonthStr, endMonthStr);
      setMeta(`查询完成：共 ${result.data.length} 条记录`);
    } catch (e) {
      toast(e.message || "查询历史均价失败");
      setMeta("查询失败");
      console.error("Failed to load historical avg price:", e);
    } finally {
      state.loading = false;
    }
  }

  // ===== 查询对比数据 =====
  async function queryCompareData() {
    const compareType = els.compareType?.value;
    const startYear = els.compareStartYear?.value || "2023";
    const startMonth = els.compareStartMonth?.value || "01";
    const endYear = els.compareEndYear?.value || "2025";
    const endMonth = els.compareEndMonth?.value || "12";
    
    const startMonthStr = `${startYear}-${startMonth}`;
    const endMonthStr = `${endYear}-${endMonth}`;

    if (startMonthStr > endMonthStr) {
      toast("起始时间不能晚于结束时间");
      return;
    }

    let targets = [];
    let baseCity = null;

    if (compareType === 'cities') {
      // 多城市对比：从复选框获取选中的城市
      const checkboxes = document.querySelectorAll('.compare-city-checkbox:checked');
      if (checkboxes.length < 2) {
        toast("请至少选择 2 个城市进行对比");
        return;
      }
      targets = Array.from(checkboxes).map(cb => ({ 
        city: cb.value, 
        bizcircle: null, 
        label: cityName(cb.value) 
      }));
    } else {
      // 同城市多商圈对比：从复选框获取选中的商圈
      baseCity = els.compareCityBase?.value;
      if (!baseCity) {
        toast("请选择城市");
        return;
      }
      const checkboxes = document.querySelectorAll('.compare-bizcircle-checkbox:checked');
      if (checkboxes.length < 2) {
        toast("请至少选择 2 个商圈进行对比");
        return;
      }
      targets = Array.from(checkboxes).map(cb => ({ 
        city: baseCity, 
        bizcircle: cb.value, 
        label: cb.value 
      }));
    }

    state.loading = true;
    setMeta("加载对比数据中...");

    try {
      const requests = targets.map(target => {
        const params = { city: target.city, start_month: startMonthStr, end_month: endMonthStr };
        if (target.bizcircle) params.bizcircle = target.bizcircle;
        return apiGet("/api/historical_avg_price", params).then(res => ({
          ...target,
          data: res.ok ? res.data : []
        }));
      });

      const results = await Promise.all(requests);
      renderCompareData(results, compareType, startMonthStr, endMonthStr);
      setMeta(`对比完成：共 ${results.length} 个地区`);
    } catch (e) {
      toast(e.message || "加载对比数据失败");
      setMeta("查询失败");
      console.error("Failed to load compare data:", e);
    } finally {
      state.loading = false;
    }
  }

  // ===== 图表渲染函数 =====
  function renderChart(type, data, city, bizcircle) {
    if (!els.statChart || !data || data.length === 0) return;

    const scope = bizcircle ? `${cityName(city)} - ${bizcircle}` : cityName(city);
    const labels = data.map(d => d.year_month || `${d.year}-${String(d.month).padStart(2, '0')}`);
    const avgUnitPrices = data.map(d => d.avg_unit_price_yuan_sqm);
    const avgTotalPrices = data.map(d => d.avg_total_price_wan);
    const counts = data.map(d => d.count);

    // 销毁旧图表
    if (state.chartInstance) {
      state.chartInstance.destroy();
    }

    const ctx = els.statChart.getContext('2d');

    let config = {};

    if (type === 'bar') {
      // 柱状图：展示单价和总价
      config = {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [
            {
              label: '平均单价 (元/㎡)',
              data: avgUnitPrices,
              backgroundColor: 'rgba(121, 97, 255, 0.7)',
              borderColor: 'rgba(121, 97, 255, 1)',
              borderWidth: 2,
              yAxisID: 'y',
            },
            {
              label: '平均总价 (万元)',
              data: avgTotalPrices,
              backgroundColor: 'rgba(0, 213, 255, 0.7)',
              borderColor: 'rgba(0, 213, 255, 1)',
              borderWidth: 2,
              yAxisID: 'y1',
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: true,
              text: `${scope} 历史均价统计（柱状图）`,
              color: 'rgba(234, 240, 255, 0.9)',
              font: { size: 16 }
            },
            legend: {
              labels: { color: 'rgba(234, 240, 255, 0.8)' }
            }
          },
          scales: {
            x: {
              ticks: { color: 'rgba(234, 240, 255, 0.7)' },
              grid: { color: 'rgba(255, 255, 255, 0.1)' }
            },
            y: {
              type: 'linear',
              position: 'left',
              title: {
                display: true,
                text: '平均单价 (元/㎡)',
                color: 'rgba(234, 240, 255, 0.8)'
              },
              ticks: { color: 'rgba(234, 240, 255, 0.7)' },
              grid: { color: 'rgba(255, 255, 255, 0.1)' }
            },
            y1: {
              type: 'linear',
              position: 'right',
              title: {
                display: true,
                text: '平均总价 (万元)',
                color: 'rgba(234, 240, 255, 0.8)'
              },
              ticks: { color: 'rgba(234, 240, 255, 0.7)' },
              grid: { display: false }
            }
          }
        }
      };
    } else if (type === 'line') {
      // 折线图：展示趋势
      config = {
        type: 'line',
        data: {
          labels: labels,
          datasets: [
            {
              label: '平均单价 (元/㎡)',
              data: avgUnitPrices,
              borderColor: 'rgba(121, 97, 255, 1)',
              backgroundColor: 'rgba(121, 97, 255, 0.1)',
              borderWidth: 3,
              fill: true,
              tension: 0.4,
              yAxisID: 'y',
            },
            {
              label: '平均总价 (万元)',
              data: avgTotalPrices,
              borderColor: 'rgba(0, 213, 255, 1)',
              backgroundColor: 'rgba(0, 213, 255, 0.1)',
              borderWidth: 3,
              fill: true,
              tension: 0.4,
              yAxisID: 'y1',
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: true,
              text: `${scope} 历史均价趋势（折线图）`,
              color: 'rgba(234, 240, 255, 0.9)',
              font: { size: 16 }
            },
            legend: {
              labels: { color: 'rgba(234, 240, 255, 0.8)' }
            }
          },
          scales: {
            x: {
              ticks: { color: 'rgba(234, 240, 255, 0.7)' },
              grid: { color: 'rgba(255, 255, 255, 0.1)' }
            },
            y: {
              type: 'linear',
              position: 'left',
              title: {
                display: true,
                text: '平均单价 (元/㎡)',
                color: 'rgba(234, 240, 255, 0.8)'
              },
              ticks: { color: 'rgba(234, 240, 255, 0.7)' },
              grid: { color: 'rgba(255, 255, 255, 0.1)' }
            },
            y1: {
              type: 'linear',
              position: 'right',
              title: {
                display: true,
                text: '平均总价 (万元)',
                color: 'rgba(234, 240, 255, 0.8)'
              },
              ticks: { color: 'rgba(234, 240, 255, 0.7)' },
              grid: { display: false }
            }
          }
        }
      };
    } else if (type === 'box') {
      // 面积图：展示价格波动范围
      // 计算上下边界
      const upperBound = [];
      const lowerBound = [];
      
      labels.forEach((label, idx) => {
        const avgPrice = avgUnitPrices[idx];
        const count = counts[idx];
        const spread = Math.sqrt(count) * 800; // 估算标准差
        
        upperBound.push(avgPrice + spread);
        lowerBound.push(Math.max(0, avgPrice - spread));
      });

      config = {
        type: 'line',
        data: {
          labels: labels,
          datasets: [
            {
              label: '价格上限',
              data: upperBound,
              borderColor: 'rgba(255, 159, 64, 0.8)',
              backgroundColor: 'rgba(255, 159, 64, 0.1)',
              borderWidth: 2,
              fill: '+1',
              tension: 0.4,
              pointRadius: 0,
            },
            {
              label: '平均价格',
              data: avgUnitPrices,
              borderColor: 'rgba(121, 97, 255, 1)',
              backgroundColor: 'rgba(121, 97, 255, 0.3)',
              borderWidth: 3,
              fill: '+1',
              tension: 0.4,
              pointRadius: 2,
              pointHoverRadius: 4,
            },
            {
              label: '价格下限',
              data: lowerBound,
              borderColor: 'rgba(0, 213, 255, 0.8)',
              backgroundColor: 'rgba(0, 213, 255, 0.1)',
              borderWidth: 2,
              fill: false,
              tension: 0.4,
              pointRadius: 0,
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: {
            mode: 'index',
            intersect: false,
          },
          plugins: {
            title: {
              display: true,
              text: `${scope} 房价波动范围（面积图）`,
              color: 'rgba(234, 240, 255, 0.9)',
              font: { size: 16 }
            },
            legend: {
              labels: { color: 'rgba(234, 240, 255, 0.8)' }
            },
            tooltip: {
              callbacks: {
                label: function(context) {
                  return `${context.dataset.label}: ${Math.round(context.parsed.y).toLocaleString()} 元/㎡`;
                }
              }
            },
            filler: {
              propagate: false
            }
          },
          scales: {
            x: {
              ticks: { 
                color: 'rgba(234, 240, 255, 0.7)',
                maxRotation: 45,
                minRotation: 45
              },
              grid: { color: 'rgba(255, 255, 255, 0.1)' }
            },
            y: {
              title: {
                display: true,
                text: '单价 (元/㎡)',
                color: 'rgba(234, 240, 255, 0.8)'
              },
              ticks: { color: 'rgba(234, 240, 255, 0.7)' },
              grid: { color: 'rgba(255, 255, 255, 0.1)' }
            }
          }
        }
      };
    }

    state.chartInstance = new Chart(ctx, config);
  }

  // ===== 渲染统计表格 =====
  function renderStatisticsTable(data, city, bizcircle, startMonth, endMonth) {
    if (!els.statTbody || !els.statEmpty || !els.statContent) return;

    if (!data || data.length === 0) {
      els.statEmpty.style.display = "grid";
      els.statContent.style.display = "none";
      els.statEmpty.querySelector("p:last-child").textContent = "暂无统计数据";
      return;
    }

    // 保存当前数据
    state.currentData = { data, city, bizcircle, startMonth, endMonth };

    els.statEmpty.style.display = "none";
    els.statContent.style.display = "block";

    // 更新描述
    const scope = bizcircle ? `${cityName(city)} - ${bizcircle}` : cityName(city);
    if (els.statResultDesc) {
      els.statResultDesc.textContent = `${scope} · ${startMonth} 至 ${endMonth} 历史均价统计`;
    }

    // 渲染表格数据
    els.statTbody.innerHTML = data
      .map((item) => {
        const yearMonth = item.year_month || `${item.year}-${String(item.month).padStart(2, '0')}`;
        const avgUnit = fmtNum0(item.avg_unit_price_yuan_sqm);
        const avgTotal = fmtPrice(item.avg_total_price_wan);
        const count = fmtNum0(item.count);

        return `
        <tr>
          <td><strong>${yearMonth}</strong></td>
          <td class="num">${avgUnit}</td>
          <td class="num">${avgTotal}</td>
          <td class="num">${count}</td>
        </tr>
      `;
      })
      .join("");

    // 默认显示柱状图
    switchView('bar');
    toast(`已加载 ${scope} 的历史均价数据`);
  }

  // ===== 渲染对比数据 =====
  function renderCompareData(results, compareType, startMonth, endMonth) {
    if (!results || results.length === 0) {
      els.statEmpty.style.display = "grid";
      els.statContent.style.display = "none";
      return;
    }

    state.compareData = { results, compareType, startMonth, endMonth };
    state.currentData = null;

    els.statEmpty.style.display = "none";
    els.statContent.style.display = "block";

    const typeLabel = compareType === 'cities' ? '多城市对比' : '多商圈对比';
    if (els.statResultDesc) {
      els.statResultDesc.textContent = `${typeLabel} · ${startMonth} 至 ${endMonth} 历史均价对比`;
    }

    // 渲染对比表格
    renderCompareTable(results);

    // 默认显示对比柱状图
    switchCompareView('bar');
    toast(`已加载 ${results.length} 个地区的对比数据`);
  }

  // ===== 渲染对比表格 =====
  function renderCompareTable(results) {
    if (!els.statTbody) return;

    // 获取所有年月
    const allMonths = new Set();
    results.forEach(r => r.data.forEach(d => {
      const ym = d.year_month || `${d.year}-${String(d.month).padStart(2, '0')}`;
      allMonths.add(ym);
    }));
    const months = Array.from(allMonths).sort();

    // 构建表头
    let thead = '<tr><th>年月</th>';
    results.forEach(r => {
      thead += `<th colspan="2" style="text-align: center;">${r.label}</th>`;
    });
    thead += '</tr><tr><th></th>';
    results.forEach(() => {
      thead += '<th class="num">单价(元/㎡)</th><th class="num">总价(万)</th>';
    });
    thead += '</tr>';

    // 构建表体
    let tbody = '';
    months.forEach(ym => {
      tbody += `<tr><td><strong>${ym}</strong></td>`;
      results.forEach(r => {
        const monthData = r.data.find(d => {
          const dym = d.year_month || `${d.year}-${String(d.month).padStart(2, '0')}`;
          return dym === ym;
        });
        if (monthData) {
          tbody += `<td class="num">${fmtNum0(monthData.avg_unit_price_yuan_sqm)}</td>`;
          tbody += `<td class="num">${fmtPrice(monthData.avg_total_price_wan)}</td>`;
        } else {
          tbody += '<td class="num">-</td><td class="num">-</td>';
        }
      });
      tbody += '</tr>';
    });

    els.statTableWrap.querySelector('thead').innerHTML = thead;
    els.statTbody.innerHTML = tbody;
  }

  // ===== 渲染对比图表 =====
  function renderCompareChart(type, results) {
    if (!els.statChart || !results || results.length === 0) return;

    // 销毁旧图表
    if (state.chartInstance) {
      state.chartInstance.destroy();
    }

    const ctx = els.statChart.getContext('2d');

    // 获取所有年月
    const allMonths = new Set();
    results.forEach(r => r.data.forEach(d => {
      const ym = d.year_month || `${d.year}-${String(d.month).padStart(2, '0')}`;
      allMonths.add(ym);
    }));
    const labels = Array.from(allMonths).sort();

    // 颜色方案
    const colors = [
      { bg: 'rgba(121, 97, 255, 0.7)', border: 'rgba(121, 97, 255, 1)' },
      { bg: 'rgba(0, 213, 255, 0.7)', border: 'rgba(0, 213, 255, 1)' },
      { bg: 'rgba(255, 72, 180, 0.7)', border: 'rgba(255, 72, 180, 1)' },
      { bg: 'rgba(255, 159, 64, 0.7)', border: 'rgba(255, 159, 64, 1)' },
      { bg: 'rgba(75, 192, 192, 0.7)', border: 'rgba(75, 192, 192, 1)' },
      { bg: 'rgba(153, 102, 255, 0.7)', border: 'rgba(153, 102, 255, 1)' },
    ];

    let config = {};

    if (type === 'bar') {
      // 分组柱状图：对比单价
      const datasets = results.map((r, idx) => {
        const color = colors[idx % colors.length];
        const data = labels.map(ym => {
          const monthData = r.data.find(d => {
            const dym = d.year_month || `${d.year}-${String(d.month).padStart(2, '0')}`;
            return dym === ym;
          });
          return monthData ? monthData.avg_unit_price_yuan_sqm : null;
        });
        return {
          label: r.label,
          data: data,
          backgroundColor: color.bg,
          borderColor: color.border,
          borderWidth: 2,
        };
      });

      config = {
        type: 'bar',
        data: { labels: labels, datasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: true,
              text: '平均单价对比（柱状图）',
              color: 'rgba(234, 240, 255, 0.9)',
              font: { size: 16 }
            },
            legend: {
              labels: { color: 'rgba(234, 240, 255, 0.8)' }
            }
          },
          scales: {
            x: {
              ticks: { color: 'rgba(234, 240, 255, 0.7)' },
              grid: { color: 'rgba(255, 255, 255, 0.1)' }
            },
            y: {
              title: {
                display: true,
                text: '平均单价 (元/㎡)',
                color: 'rgba(234, 240, 255, 0.8)'
              },
              ticks: { color: 'rgba(234, 240, 255, 0.7)' },
              grid: { color: 'rgba(255, 255, 255, 0.1)' }
            }
          }
        }
      };
    } else if (type === 'line') {
      // 多折线图：对比趋势
      const datasets = results.map((r, idx) => {
        const color = colors[idx % colors.length];
        const data = labels.map(ym => {
          const monthData = r.data.find(d => {
            const dym = d.year_month || `${d.year}-${String(d.month).padStart(2, '0')}`;
            return dym === ym;
          });
          return monthData ? monthData.avg_unit_price_yuan_sqm : null;
        });
        return {
          label: r.label,
          data: data,
          borderColor: color.border,
          backgroundColor: color.bg.replace('0.7', '0.1'),
          borderWidth: 3,
          fill: false,
          tension: 0.4,
        };
      });

      config = {
        type: 'line',
        data: { labels: labels, datasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: true,
              text: '平均单价趋势对比（折线图）',
              color: 'rgba(234, 240, 255, 0.9)',
              font: { size: 16 }
            },
            legend: {
              labels: { color: 'rgba(234, 240, 255, 0.8)' }
            }
          },
          scales: {
            x: {
              ticks: { color: 'rgba(234, 240, 255, 0.7)' },
              grid: { color: 'rgba(255, 255, 255, 0.1)' }
            },
            y: {
              title: {
                display: true,
                text: '平均单价 (元/㎡)',
                color: 'rgba(234, 240, 255, 0.8)'
              },
              ticks: { color: 'rgba(234, 240, 255, 0.7)' },
              grid: { color: 'rgba(255, 255, 255, 0.1)' }
            }
          }
        }
      };
    } else if (type === 'combo') {
      // 组合图：总价对比
      const datasets = results.map((r, idx) => {
        const color = colors[idx % colors.length];
        const data = labels.map(ym => {
          const monthData = r.data.find(d => {
            const dym = d.year_month || `${d.year}-${String(d.month).padStart(2, '0')}`;
            return dym === ym;
          });
          return monthData ? monthData.avg_total_price_wan : null;
        });
        return {
          label: r.label,
          data: data,
          backgroundColor: color.bg,
          borderColor: color.border,
          borderWidth: 2,
        };
      });

      config = {
        type: 'bar',
        data: { labels: labels, datasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: true,
              text: '平均总价对比（柱状图）',
              color: 'rgba(234, 240, 255, 0.9)',
              font: { size: 16 }
            },
            legend: {
              labels: { color: 'rgba(234, 240, 255, 0.8)' }
            }
          },
          scales: {
            x: {
              ticks: { color: 'rgba(234, 240, 255, 0.7)' },
              grid: { color: 'rgba(255, 255, 255, 0.1)' }
            },
            y: {
              title: {
                display: true,
                text: '平均总价 (万元)',
                color: 'rgba(234, 240, 255, 0.8)'
              },
              ticks: { color: 'rgba(234, 240, 255, 0.7)' },
              grid: { color: 'rgba(255, 255, 255, 0.1)' }
            }
          }
        }
      };
    } else if (type === 'box') {
      // 面积图：对比各地区价格波动范围
      const datasets = [];
      
      results.forEach((r, idx) => {
        const color = colors[idx % colors.length];
        const avgData = [];
        const upperData = [];
        const lowerData = [];
        
        labels.forEach(ym => {
          const monthData = r.data.find(d => {
            const dym = d.year_month || `${d.year}-${String(d.month).padStart(2, '0')}`;
            return dym === ym;
          });
          
          if (monthData) {
            const avgPrice = monthData.avg_unit_price_yuan_sqm;
            const count = monthData.count;
            const spread = Math.sqrt(count) * 800;
            
            avgData.push(avgPrice);
            upperData.push(avgPrice + spread);
            lowerData.push(Math.max(0, avgPrice - spread));
          } else {
            avgData.push(null);
            upperData.push(null);
            lowerData.push(null);
          }
        });
        
        // 添加上限线（半透明填充到平均线）
        datasets.push({
          label: `${r.label} 上限`,
          data: upperData,
          borderColor: color.border,
          backgroundColor: color.bg.replace('0.7', '0.15'),
          borderWidth: 1,
          fill: '+1',
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 0,
        });
        
        // 添加平均线（填充到下限线）
        datasets.push({
          label: r.label,
          data: avgData,
          borderColor: color.border,
          backgroundColor: color.bg.replace('0.7', '0.3'),
          borderWidth: 2.5,
          fill: '+1',
          tension: 0.4,
          pointRadius: 2,
          pointHoverRadius: 4,
        });
        
        // 添加下限线（不填充）
        datasets.push({
          label: `${r.label} 下限`,
          data: lowerData,
          borderColor: color.border,
          backgroundColor: 'transparent',
          borderWidth: 1,
          fill: false,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 0,
        });
      });

      config = {
        type: 'line',
        data: { labels, datasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: {
            mode: 'index',
            intersect: false,
          },
          plugins: {
            title: {
              display: true,
              text: '各地区房价波动范围对比（面积图）',
              color: 'rgba(234, 240, 255, 0.9)',
              font: { size: 16 }
            },
            legend: {
              labels: { 
                color: 'rgba(234, 240, 255, 0.8)',
                filter: function(item) {
                  // 只显示平均线的图例，隐藏上下限
                  return !item.text.includes('上限') && !item.text.includes('下限');
                }
              }
            },
            tooltip: {
              callbacks: {
                label: function(context) {
                  if (context.dataset.label.includes('上限') || context.dataset.label.includes('下限')) {
                    return null;
                  }
                  return `${context.dataset.label}: ${Math.round(context.parsed.y).toLocaleString()} 元/㎡`;
                }
              }
            },
            filler: {
              propagate: false
            }
          },
          scales: {
            x: {
              ticks: { 
                color: 'rgba(234, 240, 255, 0.7)',
                maxRotation: 45,
                minRotation: 45
              },
              grid: { color: 'rgba(255, 255, 255, 0.1)' }
            },
            y: {
              title: {
                display: true,
                text: '平均单价 (元/㎡)',
                color: 'rgba(234, 240, 255, 0.8)'
              },
              ticks: { color: 'rgba(234, 240, 255, 0.7)' },
              grid: { color: 'rgba(255, 255, 255, 0.1)' }
            }
          }
        }
      };
    }

    state.chartInstance = new Chart(ctx, config);
  }

  // ===== 切换视图 =====
  function switchView(viewType) {
    if (!state.currentData) return;

    state.currentView = viewType;
    const { data, city, bizcircle } = state.currentData;

    // 更新按钮状态
    [els.btnViewBar, els.btnViewLine, els.btnViewBox, els.btnViewTable].forEach(btn => {
      if (btn) btn.classList.remove('primary');
    });

    if (viewType === 'table') {
      // 显示表格
      if (els.chartContainer) els.chartContainer.style.display = 'none';
      if (els.statTableWrap) els.statTableWrap.style.display = 'block';
      if (els.btnViewTable) els.btnViewTable.classList.add('primary');
    } else {
      // 显示图表
      if (els.chartContainer) els.chartContainer.style.display = 'block';
      if (els.statTableWrap) els.statTableWrap.style.display = 'none';
      
      renderChart(viewType, data, city, bizcircle);
      
      if (viewType === 'bar' && els.btnViewBar) els.btnViewBar.classList.add('primary');
      if (viewType === 'line' && els.btnViewLine) els.btnViewLine.classList.add('primary');
      if (viewType === 'box' && els.btnViewBox) els.btnViewBox.classList.add('primary');
    }
  }

  // ===== 切换对比视图 =====
  function switchCompareView(viewType) {
    if (!state.compareData) return;

    state.currentView = viewType;
    const { results } = state.compareData;

    // 更新按钮状态
    [els.btnViewBar, els.btnViewLine, els.btnViewCombo, els.btnViewTable].forEach(btn => {
      if (btn) btn.classList.remove('primary');
    });

    if (viewType === 'table') {
      // 显示表格
      if (els.chartContainer) els.chartContainer.style.display = 'none';
      if (els.statTableWrap) els.statTableWrap.style.display = 'block';
      if (els.btnViewTable) els.btnViewTable.classList.add('primary');
    } else {
      // 显示图表
      if (els.chartContainer) els.chartContainer.style.display = 'block';
      if (els.statTableWrap) els.statTableWrap.style.display = 'none';
      
      renderCompareChart(viewType, results);
      
      if (viewType === 'bar' && els.btnViewBar) els.btnViewBar.classList.add('primary');
      if (viewType === 'line' && els.btnViewLine) els.btnViewLine.classList.add('primary');
      if (viewType === 'combo' && els.btnViewCombo) els.btnViewCombo.classList.add('primary');
    }
  }

  // ===== 模式切换 =====
  function switchMode(mode) {
    state.mode = mode;

    if (mode === 'single') {
      // 单地区模式
      if (els.btnModeSingle) els.btnModeSingle.classList.add('primary');
      if (els.btnModeCompare) els.btnModeCompare.classList.remove('primary');
      if (els.formSingle) els.formSingle.style.display = 'grid';
      if (els.formCompare) els.formCompare.style.display = 'none';
      if (els.filterDesc) els.filterDesc.textContent = '选择城市和年份范围，可选择特定商圈进行统计';
      if (els.btnQueryText) els.btnQueryText.textContent = '查询历史均价';
    } else {
      // 对比模式
      if (els.btnModeSingle) els.btnModeSingle.classList.remove('primary');
      if (els.btnModeCompare) els.btnModeCompare.classList.add('primary');
      if (els.formSingle) els.formSingle.style.display = 'none';
      if (els.formCompare) els.formCompare.style.display = 'grid';
      if (els.filterDesc) els.filterDesc.textContent = '选择多个城市或商圈进行横向对比分析';
      if (els.btnQueryText) els.btnQueryText.textContent = '开始对比';

      // 填充对比模式的城市复选框列表
      if (els.compareCitiesCheckboxes && state.cities.length > 0) {
        els.compareCitiesCheckboxes.innerHTML = '';
        state.cities.forEach(code => {
          const label = document.createElement('label');
          label.style.cssText = 'display: flex; align-items: center; gap: 0.5rem; cursor: pointer; padding: 0.5rem; border-radius: 4px; transition: background 0.2s;';
          label.onmouseover = () => label.style.background = 'rgba(255,255,255,0.05)';
          label.onmouseout = () => label.style.background = 'transparent';
          
          const checkbox = document.createElement('input');
          checkbox.type = 'checkbox';
          checkbox.value = code;
          checkbox.className = 'compare-city-checkbox';
          checkbox.style.cssText = 'cursor: pointer;';
          
          const span = document.createElement('span');
          span.textContent = cityName(code);
          span.style.cssText = 'color: rgba(234,240,255,0.9); font-size: 0.9rem;';
          
          label.appendChild(checkbox);
          label.appendChild(span);
          els.compareCitiesCheckboxes.appendChild(label);
        });
      }

      if (els.compareCityBase && state.cities.length > 0) {
        els.compareCityBase.innerHTML = '<option value="">请选择城市</option>';
        state.cities.forEach(code => {
          const opt = document.createElement('option');
          opt.value = code;
          opt.textContent = cityName(code);
          els.compareCityBase.appendChild(opt);
        });
      }
    }

    // 重置结果
    resetFilters();
  }

  // ===== 重置 =====
  function resetFilters() {
    if (els.statCity) els.statCity.value = "";
    if (els.statBizcircle) {
      els.statBizcircle.innerHTML = '<option value="">全市整体</option>';
    }
    if (els.statStartYear) els.statStartYear.value = "2023";
    if (els.statStartMonth) els.statStartMonth.value = "01";
    if (els.statEndYear) els.statEndYear.value = "2025";
    if (els.statEndMonth) els.statEndMonth.value = "12";
    if (els.compareStartYear) els.compareStartYear.value = "2023";
    if (els.compareStartMonth) els.compareStartMonth.value = "01";
    if (els.compareEndYear) els.compareEndYear.value = "2025";
    if (els.compareEndMonth) els.compareEndMonth.value = "12";

    if (els.statEmpty) els.statEmpty.style.display = "grid";
    if (els.statContent) els.statContent.style.display = "none";

    // 销毁图表
    if (state.chartInstance) {
      state.chartInstance.destroy();
      state.chartInstance = null;
    }
    state.currentData = null;
    state.compareData = null;

    setMeta("请选择城市后查询");
    toast("已重置筛选条件");
  }

  // ===== 事件监听 =====
  els.statCity?.addEventListener("change", () => {
    const city = els.statCity.value;
    if (city) {
      loadBizcircles(city);
      if (els.navCity) els.navCity.value = city;
    }
  });

  els.navCity?.addEventListener("change", () => {
    if (els.statCity) els.statCity.value = els.navCity.value;
    const city = els.navCity.value;
    if (city) loadBizcircles(city);
  });

  els.btnStatQuery?.addEventListener("click", () => {
    queryHistoricalAvgPrice();
  });

  els.btnStatReset?.addEventListener("click", () => {
    resetFilters();
  });

  els.navRefresh?.addEventListener("click", () => {
    location.reload();
  });

  // 模式切换按钮
  els.btnModeSingle?.addEventListener("click", () => switchMode('single'));
  els.btnModeCompare?.addEventListener("click", () => switchMode('compare'));

  // 对比类型切换
  els.compareType?.addEventListener("change", () => {
    const type = els.compareType.value;
    if (type === 'cities') {
      if (els.compareCitiesSection) els.compareCitiesSection.style.display = 'block';
      if (els.compareBizcirclesSection) els.compareBizcirclesSection.style.display = 'none';
    } else {
      if (els.compareCitiesSection) els.compareCitiesSection.style.display = 'none';
      if (els.compareBizcirclesSection) els.compareBizcirclesSection.style.display = 'block';
    }
  });

  // 对比基准城市选择
  els.compareCityBase?.addEventListener("change", () => {
    const city = els.compareCityBase.value;
    if (city) {
      loadBizcircles(city, true);
    }
  });

  // 视图切换按钮
  els.btnViewBar?.addEventListener("click", () => {
    if (state.compareData) {
      switchCompareView('bar');
    } else {
      switchView('bar');
    }
  });
  els.btnViewLine?.addEventListener("click", () => {
    if (state.compareData) {
      switchCompareView('line');
    } else {
      switchView('line');
    }
  });
  els.btnViewBox?.addEventListener("click", () => {
    if (state.compareData) {
      switchCompareView('box');
    } else {
      switchView('box');
    }
  });
  els.btnViewTable?.addEventListener("click", () => {
    if (state.compareData) {
      switchCompareView('table');
    } else {
      switchView('table');
    }
  });

  // ===== 初始化 =====
  (async function init() {
    try {
      await loadHealthAndCities();
      setMeta("准备就绪");
    } catch (e) {
      if (els.badgeApi) els.badgeApi.textContent = "API：异常";
      toast(e.message);
    }
  })();
})();
