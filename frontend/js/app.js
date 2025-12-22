(() => {
  const $ = (id) => document.getElementById(id);

  const els = {
    // navbar
    navCity: $("nav-city"),
    navRefresh: $("nav-refresh"),
    navBurger: $("nav-burger"),
    navCenter: $("nav-center"),
    badgeApi: $("badge-api"),
    badgeCities: $("badge-cities"),

    // filters
    meta: $("meta"),
    chip: $("chip"),
    fCity: $("f-city"),
    fRegion: $("f-region"),
    fBizcircle: $("f-bizcircle"),
    fCommunity: $("f-community"),
    fLayout: $("f-layout"),
    btnSearch: $("btn-search"),
    btnReset: $("btn-reset"),

    // list
    btnPrev: $("btn-prev"),
    btnNext: $("btn-next"),
    pageSize: $("page-size"),
    pagerText: $("pager-text"),
    tbody: $("tbody"),

    // trend
    sparkEmpty: $("spark-empty"),
    spark: $("spark"),
    trendList: $("trend-list"),

    // ui
    toast: $("toast"),
    modal: $("modal"),
    modalBackdrop: $("modal-backdrop"),
    modalClose: $("modal-close"),
    modalJson: $("modal-json"),
  };

  const state = {
    page: 1,
    pageSize: parseInt(els.pageSize?.value || "20", 10) || 20,
    total: 0,
    maxPage: 1,
    loading: false,
    cities: [],
    locale: "hans", // hans / hant
    currency: "CNY", // CNY / TWD
    localeTag: "zh-Hans-CN",
  };

  // ===== 城市显示名（下拉显示中文）=====
  const CITY_LABELS = {
    bj: "北京",
    sh: "上海",
    gz: "广州",
    sz: "深圳",
    tianjin: "天津",
    taibei: "台北",
    xinbei: "新北",
  };
  const TW_CITIES = new Set(["taibei", "xinbei"]);

  function cityName(key) {
    if (!key) return "-";
    const k = String(key).toLowerCase();
    return CITY_LABELS[k] || k;
  }

  function isTaiwanCity(cityKey) {
    const k = String(cityKey || "").toLowerCase();
    return TW_CITIES.has(k);
  }

  // ===== i18n 文案（简体 / 繁体）=====
  const I18N = {
    hans: {
      "nav.query": "查询",
      "nav.list": "成交列表",
      "nav.trend": "价格趋势",
      "nav.about": "关于",

      "btn.refresh": "刷新",
      "btn.search": "查询",
      "btn.reset": "重置",

      "title.filters": "查询条件",
      "desc.filters": "选择城市后可按商圈/小区/户型精确筛选",
      "title.list": "成交列表",
      "desc.list": "点击任意行查看中文详情；“↗”打开详情链接",
      "title.trend": "价格趋势",
      "desc.trend": "按月聚合成交日期：均价（元/㎡）与样本数",

      "label.city": "城市",
      "label.region": "区域",
      "label.bizcircle": "商圈",
      "label.community": "小区",
      "label.layout": "户型",

      "ph.region": "（可选）例如：浦东 / 海淀",
      "ph.bizcircle": "（可选）例如：北蔡 / 中关村",
      "ph.community": "（可选）例如：由由四村",
      "ph.layout": "（可选）例如：2室1厅",

      "th.bizcircle": "商圈",
      "th.community": "小区",
      "th.layout": "户型",
      "th.area": "面积(㎡)",
      "th.unit": "单价(元/㎡)",
      "th.total": "总价(万)",
      "th.dealdate": "成交日期",
      "th.detail": "详情",

      "chip.connected": "数据接口已连接",
      "meta.ready": "准备就绪",
      "empty.trend": "暂无趋势数据",
      "about.text": "房产成交数据查询与趋势分析 · 数据读取自 data/ 目录 JSON",
      "modal.title": "记录详情",

      // 运行时用的提示
      "toast.need_city": "请先选择城市（并确保 data/ 下存在 crawl_history_*.json）",
      "toast.reset": "已重置筛选条件",
      "toast.parse_fail": "解析记录失败",
      "toast.no_link": "该记录没有详情链接",
      "meta.loading": "加载中…",
      "meta.done": "完成：共 {n} 条",
      "meta.fail": "加载失败",
      "badge.api_ok": "API：OK",
      "badge.api_bad": "API：异常",
      "badge.cities": "城市：{names}",
      "pager": "第 {p} / {m} 页",
      "trend.avg_total": "均总价（万）：{v}",
      "trend.samples": "样本",
      "trend.unit_suffix": "元/㎡",
    },

    hant: {
      "nav.query": "查詢",
      "nav.list": "成交列表",
      "nav.trend": "價格趨勢",
      "nav.about": "關於",

      "btn.refresh": "重新整理",
      "btn.search": "查詢",
      "btn.reset": "重設",

      "title.filters": "查詢條件",
      "desc.filters": "選擇城市後可按商圈/小區/戶型精準篩選",
      "title.list": "成交列表",
      "desc.list": "點擊任意列查看詳情；「↗」開啟詳情連結",
      "title.trend": "價格趨勢",
      "desc.trend": "按月彙總成交日期：均價（NT$/㎡）與樣本數",

      "label.city": "城市",
      "label.region": "區域",
      "label.bizcircle": "商圈",
      "label.community": "小區",
      "label.layout": "戶型",

      "ph.region": "（選填）例如：內湖 / 信義",
      "ph.bizcircle": "（選填）例如：石牌 / 中山",
      "ph.community": "（選填）例如：××社區",
      "ph.layout": "（選填）例如：2房1廳",

      "th.bizcircle": "商圈",
      "th.community": "小區",
      "th.layout": "戶型",
      "th.area": "面積(㎡)",
      "th.unit": "單價(NT$/㎡)",
      "th.total": "總價(萬 NT$)",
      "th.dealdate": "成交日期",
      "th.detail": "詳情",

      "chip.connected": "資料介面已連線",
      "meta.ready": "準備就緒",
      "empty.trend": "暫無趨勢資料",
      "about.text": "房產成交資料查詢與趨勢分析 · 資料讀取自 data/ 目錄 JSON",
      "modal.title": "記錄詳情",

      "toast.need_city": "請先選擇城市（並確認 data/ 下存在 crawl_history_*.json）",
      "toast.reset": "已重設篩選條件",
      "toast.parse_fail": "解析記錄失敗",
      "toast.no_link": "此記錄沒有詳情連結",
      "meta.loading": "載入中…",
      "meta.done": "完成：共 {n} 筆",
      "meta.fail": "載入失敗",
      "badge.api_ok": "API：OK",
      "badge.api_bad": "API：異常",
      "badge.cities": "城市：{names}",
      "pager": "第 {p} / {m} 頁",
      "trend.avg_total": "均總價（萬 NT$）：{v}",
      "trend.samples": "樣本",
      "trend.unit_suffix": "NT$/㎡",
    },
  };

  function t(key, vars = {}) {
    const dict = I18N[state.locale] || I18N.hans;
    let s = dict[key] || key;
    Object.entries(vars).forEach(([k, v]) => {
      s = s.replaceAll(`{${k}}`, String(v));
    });
    return s;
  }

  function applyLocaleByCity(cityKey) {
    const tw = isTaiwanCity(cityKey);

    state.locale = tw ? "hant" : "hans";
    state.currency = tw ? "TWD" : "CNY";
    state.localeTag = tw ? "zh-Hant-TW" : "zh-Hans-CN";

    document.documentElement.lang = tw ? "zh-Hant" : "zh-CN";
    document.body.classList.toggle("locale-hant", tw);
    document.body.classList.toggle("locale-hans", !tw);

    // 更新页面上的静态文本（data-i18n / placeholder）
    updateI18nDom();

    // badge 文案更新
    if (els.badgeApi) els.badgeApi.textContent = t("badge.api_ok");
    if (els.badgeCities) {
      const names = (state.cities || []).map(cityName).join(", ");
      els.badgeCities.textContent = t("badge.cities", { names: names || "-" });
    }

    // chip 友好文案
    if (els.chip) els.chip.textContent = t("chip.connected");

    // title（可选）
    document.title = tw ? "HPQAQ · 房價看板" : "HPQAQ · 房价看板";
  }

  function updateI18nDom() {
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (key) el.textContent = t(key);
    });

    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      const key = el.getAttribute("data-i18n-placeholder");
      if (key) el.setAttribute("placeholder", t(key));
    });
  }

  // ===== 数字与货币格式化 =====
  const nf0 = () => new Intl.NumberFormat(state.localeTag, { maximumFractionDigits: 0 });
  const nf2 = () => new Intl.NumberFormat(state.localeTag, { maximumFractionDigits: 2 });

  function fmt(x) {
    return x === null || x === undefined || x === "" ? "-" : String(x);
  }
  function fmtNum0(x) {
    if (x === null || x === undefined || x === "" || !Number.isFinite(Number(x))) return "-";
    return nf0().format(Number(x));
  }
  function fmtNum2(x) {
    if (x === null || x === undefined || x === "" || !Number.isFinite(Number(x))) return "-";
    return nf2().format(Number(x));
  }

  // 单价显示：CNY => 元/㎡；TWD => NT$/㎡（数值本身不加币符号，靠表头说明）
  function fmtUnitPrice(x) {
    return fmtNum0(x);
  }

  // 总价：字段仍叫 total_price_wan（万单位）
  // CNY：总价(万)；TWD：总价(万 NT$)
  function fmtTotalWan(x) {
    return fmtNum2(x);
  }

  function toast(msg) {
    if (!els.toast) return;
    els.toast.textContent = msg;
    els.toast.classList.remove("show");
    void els.toast.offsetWidth;
    els.toast.classList.add("show");
  }

  function qs(params) {
    const usp = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && String(v).trim().length > 0) {
        usp.set(k, String(v).trim());
      }
    });
    return usp.toString();
  }

  async function apiGet(path, params = {}) {
    const url = `${path}${Object.keys(params).length ? `?${qs(params)}` : ""}`;
    const res = await fetch(url, { headers: { Accept: "application/json" } });
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
    return await res.json();
  }

  function setMeta(text) {
    if (els.meta) els.meta.textContent = text;
  }

  function updatePager() {
    if (els.pagerText) els.pagerText.textContent = t("pager", { p: state.page, m: state.maxPage });
    if (els.btnPrev) els.btnPrev.disabled = state.loading || state.page <= 1;
    if (els.btnNext) els.btnNext.disabled = state.loading || state.page >= state.maxPage;
  }

  function renderSkeleton(n = 10) {
    const cols = 8;
    const html = Array.from({ length: n })
      .map(() => {
        const tds = Array.from({ length: cols }).map(() => `<td><div class="skeleton"></div></td>`).join("");
        return `<tr>${tds}</tr>`;
      })
      .join("");
    if (els.tbody) els.tbody.innerHTML = html;
  }

  // ===== 隐藏 house_id / region；其余中文展示 =====
  const LABELS = {
    bizcircle: () => (state.locale === "hant" ? "商圈" : "商圈"),
    community: () => (state.locale === "hant" ? "小區" : "小区"),
    layout: () => (state.locale === "hant" ? "戶型" : "户型"),
    area_sqm: () => (state.locale === "hant" ? "面積(㎡)" : "面积(㎡)"),
    unit_price_yuan_sqm: () => (state.locale === "hant" ? "單價" : "单价"),
    total_price_wan: () => (state.locale === "hant" ? "總價" : "总价"),
    orientation: () => (state.locale === "hant" ? "朝向" : "朝向"),
    building_year: () => (state.locale === "hant" ? "建成年份" : "建成年份"),
    floor: () => (state.locale === "hant" ? "樓層" : "楼层"),
    deal_date: () => (state.locale === "hant" ? "成交日期" : "成交日期"),
    crawl_time: () => (state.locale === "hant" ? "抓取時間" : "抓取时间"),
    detail_url: () => (state.locale === "hant" ? "詳情連結" : "详情链接"),
  };
  const HIDDEN_KEYS = new Set(["house_id", "region"]);
  const DETAIL_FIELDS = [
    "community",
    "bizcircle",
    "layout",
    "area_sqm",
    "unit_price_yuan_sqm",
    "total_price_wan",
    "orientation",
    "building_year",
    "floor",
    "deal_date",
    "crawl_time",
    "detail_url",
  ];

  function renderTable(items) {
    if (!els.tbody) return;

    if (!items || !items.length) {
      els.tbody.innerHTML =
        `<tr><td colspan="8" style="padding:16px;color:rgba(234,240,255,.65);">${state.locale === "hant" ? "暫無資料" : "暂无数据"}</td></tr>`;
      return;
    }

    els.tbody.innerHTML = items
      .map((r) => {
        const payload = encodeURIComponent(JSON.stringify(r));
        const hasLink = !!r.detail_url;
        const linkBtn = hasLink
          ? `<button class="btn icon" data-open="1" title="${state.locale === "hant" ? "開啟詳情連結" : "打开详情链接"}">↗</button>`
          : `<span style="color:rgba(234,240,255,.45)">-</span>`;

        return `
          <tr data-json="${payload}">
            <td>${fmt(r.bizcircle)}</td>
            <td>${fmt(r.community)}</td>
            <td>${fmt(r.layout)}</td>
            <td class="num">${fmtNum2(r.area_sqm)}</td>
            <td class="num">${fmtUnitPrice(r.unit_price_yuan_sqm)}</td>
            <td class="num">${fmtTotalWan(r.total_price_wan)}</td>
            <td>${fmt(r.deal_date)}</td>
            <td>${linkBtn}</td>
          </tr>`;
      })
      .join("");
  }

  function closeModal() {
    if (!els.modal) return;
    els.modal.classList.add("hidden");
    els.modal.setAttribute("aria-hidden", "true");
  }

  function openModal(obj) {
    if (!els.modal || !els.modalJson) return;

    const lines = [];
    for (const k of DETAIL_FIELDS) {
      if (HIDDEN_KEYS.has(k)) continue;

      const label = (LABELS[k] ? LABELS[k]() : k);
      let v = obj?.[k];

      if (k === "unit_price_yuan_sqm") {
        // 单价
        v = fmtUnitPrice(v);
        lines.push(`${label}：${v} ${t("trend.unit_suffix")}`);
        continue;
      }

      if (k === "total_price_wan") {
        // 总价（万）
        v = fmtTotalWan(v);
        lines.push(`${label}：${v} ${state.currency === "TWD" ? "萬 NT$" : "万"}`);
        continue;
      }

      if (k === "area_sqm") {
        v = fmtNum2(v);
        lines.push(`${label}：${v} ㎡`);
        continue;
      }

      if (k === "detail_url") {
        lines.push(`${label}：${v ? String(v) : "-"}`);
        continue;
      }

      lines.push(`${label}：${v === null || v === undefined || v === "" ? "-" : String(v)}`);
    }

    els.modalJson.textContent = lines.join("\n");
    els.modal.classList.remove("hidden");
    els.modal.setAttribute("aria-hidden", "false");
  }

  function getQuery() {
    return {
      city: els.fCity?.value,
      region: els.fRegion?.value,
      bizcircle: els.fBizcircle?.value,
      community: els.fCommunity?.value,
      layout: els.fLayout?.value,
      page: state.page,
      page_size: state.pageSize,
    };
  }

  async function loadHealthAndCities() {
    const h = await apiGet("/api/health");
    state.cities = h.cities || [];

    // 先填充 options（显示中文，value 保持 key）
    const optionsHtml = state.cities
      .map((c) => `<option value="${c}">${cityName(c)}</option>`)
      .join("");

    if (els.fCity) els.fCity.innerHTML = optionsHtml || `<option value="">（无数据）</option>`;
    if (els.navCity) els.navCity.innerHTML = optionsHtml || `<option value="">（无）</option>`;

    const first = state.cities[0] || "";
    if (els.fCity && !els.fCity.value) els.fCity.value = first;
    if (els.navCity && !els.navCity.value) els.navCity.value = els.fCity?.value || first;

    // 根据当前城市应用语言/货币
    applyLocaleByCity(els.fCity?.value);

    if (els.badgeApi) els.badgeApi.textContent = t("badge.api_ok");
    if (els.badgeCities) {
      const names = state.cities.map(cityName).join(", ");
      els.badgeCities.textContent = t("badge.cities", { names: names || "-" });
    }
  }

  async function loadListingsAndTrend() {
    const q = getQuery();
    if (!q.city) {
      toast(t("toast.need_city"));
      return;
    }

    // 切换城市时：立即应用繁中/台币（你要的效果）
    applyLocaleByCity(q.city);

    if (els.navCity && els.navCity.value !== q.city) els.navCity.value = q.city;

    state.loading = true;
    updatePager();
    renderSkeleton(Math.min(state.pageSize, 12));
    setMeta(t("meta.loading"));

    try {
      const data = await apiGet("/api/listings", q);

      const items = data.items || [];
      state.total = data.total || 0;
      state.maxPage = Math.max(1, Math.ceil(state.total / state.pageSize));

      renderTable(items);
      setMeta(t("meta.done", { n: state.total }));
    } catch (e) {
      if (els.tbody) {
        els.tbody.innerHTML =
          `<tr><td colspan="8" style="padding:16px;color:#ffb3c7;">${t("meta.fail")}：${e.message}</td></tr>`;
      }
      setMeta(t("meta.fail"));
      toast(e.message);
    } finally {
      state.loading = false;
      updatePager();
    }

    // 趋势（不阻塞列表）
    try {
      const tdata = await apiGet("/api/price_trend", {
        city: q.city,
        region: q.region,
        bizcircle: q.bizcircle,
        community: q.community,
        layout: q.layout,
      });
      const points = tdata.points || [];
      renderSpark(points);
      renderTrendList(points);
    } catch {
      renderSpark([]);
      renderTrendList([]);
    }
  }

  function clearSpark() {
    if (els.spark) els.spark.innerHTML = "";
  }

  function renderSpark(points) {
    if (!els.spark || !els.sparkEmpty) return;
    clearSpark();

    if (!points || points.length < 2) {
      els.sparkEmpty.style.display = "grid";
      return;
    }

    const values = points
      .map((p) => Number(p.avg_unit_price_yuan_sqm))
      .filter((v) => Number.isFinite(v));

    if (values.length < 2) {
      els.sparkEmpty.style.display = "grid";
      return;
    }

    els.sparkEmpty.style.display = "none";

    const w = 600, h = 220, padX = 18, padY = 18;
    const minV = Math.min(...values), maxV = Math.max(...values);
    const span = Math.max(1, maxV - minV);

    const toX = (i) => padX + (i * (w - padX * 2)) / (points.length - 1);
    const toY = (v) => (h - padY) - ((v - minV) * (h - padY * 2)) / span;

    const xy = points.map((p, i) => {
      const v = Number(p.avg_unit_price_yuan_sqm);
      return { x: toX(i), y: toY(Number.isFinite(v) ? v : minV) };
    });

    const d = xy.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(" ");
    const dFill = `${d} L ${xy[xy.length - 1].x.toFixed(1)} ${(h - padY).toFixed(1)} L ${xy[0].x.toFixed(1)} ${(h - padY).toFixed(1)} Z`;

    els.spark.innerHTML = `
      <defs>
        <linearGradient id="gLine" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stop-color="rgba(121,97,255,.95)"/>
          <stop offset="50%" stop-color="rgba(0,213,255,.95)"/>
          <stop offset="100%" stop-color="rgba(255,72,180,.9)"/>
        </linearGradient>
        <linearGradient id="gFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="rgba(0,213,255,.22)"/>
          <stop offset="100%" stop-color="rgba(0,213,255,0)"/>
        </linearGradient>
      </defs>
      <path d="${dFill}" fill="url(#gFill)"></path>
      <path d="${d}" fill="none" stroke="url(#gLine)" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"></path>
      ${xy.map(p => `<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="3.4" fill="rgba(234,240,255,.92)" opacity=".9"></circle>`).join("")}
    `;
  }

  function renderTrendList(points) {
    if (!els.trendList) return;
    if (!points || !points.length) {
      els.trendList.innerHTML = "";
      return;
    }

    els.trendList.innerHTML = points
      .slice()
      .reverse()
      .slice(0, 8)
      .map((p) => {
        const avgTotal = fmtTotalWan(p.avg_total_price_wan);
        const avgUnit = fmtUnitPrice(p.avg_unit_price_yuan_sqm);
        const unitSuffix = t("trend.unit_suffix");

        return `
          <li>
            <div>
              <div><b>${p.month}</b> · <span style="color:rgba(234,240,255,.68)">${t("trend.samples")}</span> ${p.count}</div>
              <div style="color:rgba(234,240,255,.68)">${t("trend.avg_total", { v: avgTotal })}</div>
            </div>
            <div style="text-align:right">
              <div><b>${avgUnit}</b></div>
              <div style="color:rgba(234,240,255,.68)">${unitSuffix}</div>
            </div>
          </li>
        `;
      })
      .join("");
  }

  // ===== 事件绑定 =====
  els.btnSearch?.addEventListener("click", () => {
    state.page = 1;
    loadListingsAndTrend();
  });

  els.btnReset?.addEventListener("click", () => {
    if (els.fRegion) els.fRegion.value = "";
    if (els.fBizcircle) els.fBizcircle.value = "";
    if (els.fCommunity) els.fCommunity.value = "";
    if (els.fLayout) els.fLayout.value = "";
    state.page = 1;
    toast(t("toast.reset"));
    loadListingsAndTrend();
  });

  els.btnPrev?.addEventListener("click", () => {
    if (state.page <= 1) return;
    state.page -= 1;
    loadListingsAndTrend();
  });

  els.btnNext?.addEventListener("click", () => {
    if (state.page >= state.maxPage) return;
    state.page += 1;
    loadListingsAndTrend();
  });

  els.pageSize?.addEventListener("change", () => {
    state.pageSize = parseInt(els.pageSize.value, 10) || 20;
    state.page = 1;
    loadListingsAndTrend();
  });

  // 行点击：默认打开详情；点“↗”打开链接
  els.tbody?.addEventListener("click", (ev) => {
    const btn = ev.target.closest("[data-open='1']");
    const tr = ev.target.closest("tr");
    if (!tr || !tr.dataset.json) return;

    let obj;
    try {
      obj = JSON.parse(decodeURIComponent(tr.dataset.json));
    } catch {
      toast(t("toast.parse_fail"));
      return;
    }

    if (btn) {
      ev.preventDefault();
      ev.stopPropagation();
      const url = obj?.detail_url;
      if (url) window.open(url, "_blank", "noopener,noreferrer");
      else toast(t("toast.no_link"));
      return;
    }

    openModal(obj);
  });

  els.modalClose?.addEventListener("click", closeModal);
  els.modalBackdrop?.addEventListener("click", closeModal);
  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModal();
  });

  // navbar：城市切换/刷新/移动端菜单
  els.navCity?.addEventListener("change", () => {
    if (els.fCity) els.fCity.value = els.navCity.value;
    state.page = 1;
    loadListingsAndTrend();
  });

  els.navRefresh?.addEventListener("click", () => {
    state.page = 1;
    loadListingsAndTrend();
  });

  els.navBurger?.addEventListener("click", () => {
    document.body.classList.toggle("nav-open");
  });

  // 点击导航链接后关闭移动菜单
  els.navCenter?.addEventListener("click", (e) => {
    const a = e.target.closest("a");
    if (!a) return;
    document.body.classList.remove("nav-open");
  });

  // 切换筛选城市时也同步 navbar + 触发切换繁中/台币
  els.fCity?.addEventListener("change", () => {
    if (els.navCity) els.navCity.value = els.fCity.value;
    state.page = 1;
    loadListingsAndTrend();
  });

  // ===== 初始化 =====
  (async function init() {
    renderSkeleton(10);
    try {
      await loadHealthAndCities();
      setMeta(t("meta.ready"));
      if (els.fCity?.value) await loadListingsAndTrend();
    } catch (e) {
      if (els.badgeApi) els.badgeApi.textContent = t("badge.api_bad");
      toast(e.message);
    } finally {
      updatePager();
    }
  })();
})();
