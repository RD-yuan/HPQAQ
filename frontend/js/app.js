(() => {
  const $ = (id) => document.getElementById(id);

  const els = {
    // navbar
    navbar: $("navbar"),
    navCity: $("nav-city"),
    navRefresh: $("nav-refresh"),
    navBurger: $("nav-burger"),
    navCenter: $("nav-center"),
    navOverlay: $("nav-overlay"),
    badgeApi: $("badge-api"),
    badgeCities: $("badge-cities"),

    // page regions (for modal a11y)
    main: $("main"),
    about: $("about"),

    // filters
    meta: $("meta"),
    chip: $("chip"),
    filtersForm: $("filters-form"),
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
    listState: $("list-state"),
    tableWrap: $("table-wrap"),
    tbody: $("tbody"),

    // trend
    sparkWrap: $("spark-wrap"),
    sparkEmpty: $("spark-empty"),
    spark: $("spark"),
    sparkTip: $("spark-tip"),
    sparkCursor: $("spark-cursor"),
    trendList: $("trend-list"),

    // news
    btnNewsRefresh: $("btn-news-refresh"),
    newsMeta: $("news-meta"),
    newsList: $("news-list"),
    newsEmpty: $("news-empty"),

    // ui
    toast: $("toast"),
    modal: $("modal"),
    modalBackdrop: $("modal-backdrop"),
    modalCard: $("modal-card"),
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

    // request controllers
    ctrlList: null,
    ctrlTrend: null,
    ctrlNews: null,

    // modal / nav
    modalOpen: false,
    lastFocus: null,
    navOpen: false,

    // spark hover
    sparkXY: [],
    sparkPoints: [],

    // news state
    newsLoading: false,
    newsCity: "",
    newsLastFetchedAt: 0,
  };

  const CITY_LABELS = {
    bj: "北京",
    sh: "上海",
    gz: "广州",
    sz: "深圳",
    beijing: "北京",
    shanghai: "上海",
    guangzhou: "广州",
    shenzhen: "深圳",
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

  const I18N = {
    hans: {
      "nav.query": "查询",
      "nav.list": "成交列表",
      "nav.trend": "价格趋势",
      "nav.statistics": "房价统计",
      "nav.about": "关于",
      "btn.refresh": "刷新",
      "btn.search": "查询",
      "btn.reset": "重置",
      "title.filters": "查询条件",
      "desc.filters": "选择城市后可按商圈/小区/户型精确筛选",
      "title.list": "成交列表",
      "desc.list": "点击任意行查看详情；“↗”打开详情链接",
      "title.trend": "价格趋势",
      "desc.trend": "按月聚合成交日期：均价（元/㎡）与样本数",
      "title.news": "房天下热榜",
      "desc.news": "自动抓取房天下「房产热榜」，点击标题跳转原文",
      "btn.news_refresh": "更新",
      "empty.news": "暂无热榜新闻",
      "news.meta": "来源：房天下 · {city} · {time}",
      "toast.news_fail": "新闻热榜加载失败",
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
      "list.loading": "正在加载列表…",
      "list.empty": "没有匹配记录，尝试放宽条件或更换城市。",
      "spark.tip": "{month} · 均价 {unit} {suffix} · 样本 {count}",
    },
    hant: {
      "nav.query": "查詢",
      "nav.list": "成交列表",
      "nav.trend": "價格趨勢",
      "nav.statistics": "房價統計",
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
      "title.news": "房天下热榜",
      "desc.news": "自動抓取房天下「房產熱榜」，點擊標題跳轉原文",
      "btn.news_refresh": "更新",
      "empty.news": "暫無熱榜新聞",
      "news.meta": "來源：房天下 · {city} · {time}",
      "toast.news_fail": "新聞熱榜載入失敗",
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
      "list.loading": "正在載入列表…",
      "list.empty": "沒有符合條件的紀錄，請放寬條件或更換城市。",
      "spark.tip": "{month} · 均價 {unit} {suffix} · 樣本 {count}",
    },
  };

  function t(key, vars = {}) {
    const dict = I18N[state.locale] || I18N.hans;
    let s = dict[key] || key;
    for (const [k, v] of Object.entries(vars)) s = s.replaceAll(`{${k}}`, String(v));
    return s;
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

  function applyLocaleByCity(cityKey) {
    const tw = isTaiwanCity(cityKey);
    state.locale = tw ? "hant" : "hans";
    state.currency = tw ? "TWD" : "CNY";
    state.localeTag = tw ? "zh-Hant-TW" : "zh-Hans-CN";

    document.documentElement.lang = tw ? "zh-Hant" : "zh-CN";
    document.body.classList.toggle("locale-hant", tw);
    document.body.classList.toggle("locale-hans", !tw);

    updateI18nDom();

    if (els.badgeApi && !els.badgeApi.textContent) els.badgeApi.textContent = t("badge.api_ok");
    if (els.badgeCities) {
      const names = (state.cities || []).map(cityName).join(", ");
      els.badgeCities.textContent = t("badge.cities", { names: names || "-" });
    }
    if (els.chip) els.chip.textContent = t("chip.connected");

    document.title = tw ? "HPQAQ · 房價看板" : "HPQAQ · 房价看板";
  }

  const nf0 = () => new Intl.NumberFormat(state.localeTag, { maximumFractionDigits: 0 });
  const nf2 = () => new Intl.NumberFormat(state.localeTag, { maximumFractionDigits: 2 });

  const fmt = (x) => (x === null || x === undefined || x === "" ? "-" : String(x));

  function fmtNum0(x) {
    if (x === null || x === undefined || x === "" || !Number.isFinite(Number(x))) return "-";
    return nf0().format(Number(x));
  }

  function fmtNum2(x) {
    if (x === null || x === undefined || x === "" || !Number.isFinite(Number(x))) return "-";
    return nf2().format(Number(x));
  }

  const fmtUnitPrice = (x) => fmtNum0(x);
  const fmtTotalWan = (x) => fmtNum2(x);

  function escapeHtml(s) {
    const str = String(s ?? "");
    return str
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
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
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && String(v).trim().length > 0) usp.set(k, String(v).trim());
    }
    return usp.toString();
  }

  async function apiGet(path, params = {}, { signal } = {}) {
    const url = `${path}${Object.keys(params).length ? `?${qs(params)}` : ""}`;
    const res = await fetch(url, { headers: { Accept: "application/json" }, signal });
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
    return await res.json();
  }

  function setMeta(text) {
    if (els.meta) els.meta.textContent = text;
  }

  function setListState(text) {
    if (!els.listState) return;
    els.listState.textContent = text || "";
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
        return `<tr aria-hidden="true">${tds}</tr>`;
      })
      .join("");
    if (els.tbody) els.tbody.innerHTML = html;
  }

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

    const arr = Array.isArray(items) ? items : [];
    if (!arr.length) {
      els.tbody.innerHTML = `<tr><td colspan="8" style="padding:16px;color:rgba(234,240,255,.70);">${escapeHtml(
        t("list.empty")
      )}</td></tr>`;
      setListState(t("list.empty"));
      return;
    }

    const rows = arr
      .map((r) => {
        const payload = encodeURIComponent(JSON.stringify(r));
        const hasLink = !!r.detail_url;

        const biz = fmt(r.bizcircle);
        const com = fmt(r.community);
        const lay = fmt(r.layout);
        const date = fmt(r.deal_date);

        const cell = (text, max = 280) => {
          const s = text === "-" ? "-" : String(text);
          const title = s === "-" ? "" : escapeHtml(s);
          return `<span class="cell-trunc" style="max-width:${max}px" title="${title}">${escapeHtml(s)}</span>`;
        };

        const linkBtn = hasLink
          ? `<button class="btn icon open-link-btn" data-open="1" type="button" title="${escapeHtml(
            state.locale === "hant" ? "開啟詳情連結" : "打开详情链接"
          )}" aria-label="${escapeHtml(state.locale === "hant" ? "開啟詳情連結" : "打开详情链接")}">↗</button>`
          : `<span style="color:rgba(234,240,255,.45)">-</span>`;

        return `
          <tr tabindex="0" data-json="${payload}">
            <td>${cell(biz, 180)}</td>
            <td>${cell(com, 320)}</td>
            <td>${cell(lay, 180)}</td>
            <td class="num">${escapeHtml(fmtNum2(r.area_sqm))}</td>
            <td class="num">${escapeHtml(fmtUnitPrice(r.unit_price_yuan_sqm))}</td>
            <td class="num">${escapeHtml(fmtTotalWan(r.total_price_wan))}</td>
            <td>${cell(date, 140)}</td>
            <td style="text-align:center">${linkBtn}</td>
          </tr>`;
      })
      .join("");

    els.tbody.innerHTML = rows;
    setListState("");
  }

  function getFocusableWithin(root) {
    if (!root) return [];
    const nodes = root.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    return Array.from(nodes).filter((el) => {
      if (el.hasAttribute("disabled")) return false;
      const style = window.getComputedStyle(el);
      return style.visibility !== "hidden" && style.display !== "none";
    });
  }

  const pageInertTargets = [els.navbar, els.main, els.about].filter(Boolean);
  function setPageInert(inert) {
    for (const el of pageInertTargets) {
      if (inert) {
        el.setAttribute("aria-hidden", "true");
        try {
          el.inert = true;
        } catch {
          /* ignore */
        }
      } else {
        el.removeAttribute("aria-hidden");
        try {
          el.inert = false;
        } catch {
          /* ignore */
        }
      }
    }
  }

  function closeModal({ restoreFocus = true } = {}) {
    if (!els.modal) return;
    state.modalOpen = false;

    els.modal.classList.add("hidden");
    els.modal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("modal-open");
    setPageInert(false);

    document.removeEventListener("keydown", onModalKeydown, true);

    if (restoreFocus && state.lastFocus && typeof state.lastFocus.focus === "function") {
      try {
        state.lastFocus.focus();
      } catch {
        // ignore
      }
    }
    state.lastFocus = null;
  }

  function onModalKeydown(e) {
    if (!state.modalOpen) return;

    if (e.key === "Escape") {
      e.preventDefault();
      closeModal();
      return;
    }

    if (e.key !== "Tab") return;

    const focusables = getFocusableWithin(els.modalCard);
    if (!focusables.length) {
      e.preventDefault();
      return;
    }

    const first = focusables[0];
    const last = focusables[focusables.length - 1];

    if (e.shiftKey) {
      if (document.activeElement === first || !els.modalCard.contains(document.activeElement)) {
        e.preventDefault();
        last.focus();
      }
    } else {
      if (document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
  }

  function openModal(obj, { focusFrom } = {}) {
    if (!els.modal || !els.modalJson || !els.modalCard) return;

    state.lastFocus = focusFrom || document.activeElement;

    const lines = [];
    for (const k of DETAIL_FIELDS) {
      const label = LABELS[k] ? LABELS[k]() : k;
      let v = obj?.[k];

      if (k === "unit_price_yuan_sqm") {
        v = fmtUnitPrice(v);
        lines.push(`${label}：${v} ${t("trend.unit_suffix")}`);
        continue;
      }
      if (k === "total_price_wan") {
        v = fmtTotalWan(v);
        lines.push(`${label}：${v} ${state.currency === "TWD" ? "萬 NT$" : "万"}`);
        continue;
      }
      if (k === "area_sqm") {
        v = fmtNum2(v);
        lines.push(`${label}：${v} ㎡`);
        continue;
      }

      lines.push(`${label}：${v === null || v === undefined || v === "" ? "-" : String(v)}`);
    }

    els.modalJson.textContent = lines.join("\n");

    setNavOpen(false);

    els.modal.classList.remove("hidden");
    els.modal.setAttribute("aria-hidden", "false");
    document.body.classList.add("modal-open");
    setPageInert(true);
    state.modalOpen = true;

    document.addEventListener("keydown", onModalKeydown, true);

    // focus into modal
    const toFocus = els.modalClose || els.modalCard;
    requestAnimationFrame(() => {
      try {
        toFocus.focus();
      } catch {
        // ignore
      }
    });
  }

  function setNavOpen(open) {
    state.navOpen = !!open;
    document.body.classList.toggle("nav-open", state.navOpen);
    if (els.navBurger) els.navBurger.setAttribute("aria-expanded", state.navOpen ? "true" : "false");
    if (els.navOverlay) els.navOverlay.setAttribute("aria-hidden", state.navOpen ? "false" : "true");

    if (state.navOpen) {
      // Move focus into menu on small screens for accessibility
      const isMobileMenu = window.innerWidth <= 1200;
      if (isMobileMenu) {
        requestAnimationFrame(() => {
          const firstLink = els.navCenter?.querySelector("a");
          if (firstLink && typeof firstLink.focus === "function") firstLink.focus();
        });
      }
    }
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

    const optionsHtml = state.cities
      .map((c) => `<option value="${escapeHtml(c)}">${escapeHtml(cityName(c))}</option>`)
      .join("");
    if (els.fCity) els.fCity.innerHTML = optionsHtml || `<option value="">（无数据）</option>`;
    if (els.navCity) els.navCity.innerHTML = optionsHtml || `<option value="">（无）</option>`;

    const first = state.cities[0] || "";
    if (els.fCity && !els.fCity.value) els.fCity.value = first;
    if (els.navCity && !els.navCity.value) els.navCity.value = els.fCity?.value || first;

    applyLocaleByCity(els.fCity?.value);

    if (els.badgeApi) els.badgeApi.textContent = t("badge.api_ok");
    if (els.badgeCities) {
      const names = state.cities.map(cityName).join(", ");
      els.badgeCities.textContent = t("badge.cities", { names: names || "-" });
    }
  }

  function clearSpark() {
    if (els.spark) els.spark.innerHTML = "";
    state.sparkXY = [];
    state.sparkPoints = [];
  }

  function sortTrendPoints(points) {
    if (!Array.isArray(points)) return [];
    return points
      .slice()
      .filter((p) => p && p.month)
      .sort((a, b) => String(a.month).localeCompare(String(b.month)));
  }

  function filterTrendPoints(points, cityKey) {
    const limit = isTaiwanCity(cityKey) ? 36 : 12;
    const ps = sortTrendPoints(points);
    return ps.length <= limit ? ps : ps.slice(ps.length - limit);
  }

  function updateTrendDesc(cityKey, pointsFiltered) {
    const el = document.querySelector("#trend .card-desc");
    if (!el) return;
    const span = Math.max(0, (pointsFiltered || []).length);
    const suffix = state.locale === "hant" ? ` · 近${span}個月` : ` · 近${span}个月`;
    el.textContent = `${t("desc.trend")}${suffix}`;
  }

  function smoothPath(xy) {
    if (!xy || xy.length < 2) return "";
    let d = `M ${xy[0].x.toFixed(1)} ${xy[0].y.toFixed(1)}`;
    for (let i = 0; i < xy.length - 1; i++) {
      const p0 = xy[i - 1] || xy[i];
      const p1 = xy[i];
      const p2 = xy[i + 1];
      const p3 = xy[i + 2] || p2;

      const c1x = p1.x + (p2.x - p0.x) / 6;
      const c1y = p1.y + (p2.y - p0.y) / 6;
      const c2x = p2.x - (p3.x - p1.x) / 6;
      const c2y = p2.y - (p3.y - p1.y) / 6;

      d += ` C ${c1x.toFixed(1)} ${c1y.toFixed(1)}, ${c2x.toFixed(1)} ${c2y.toFixed(1)}, ${p2.x.toFixed(
        1
      )} ${p2.y.toFixed(1)}`;
    }
    return d;
  }

  function renderSpark(points) {
    if (!els.spark || !els.sparkEmpty) return;
    els.spark.innerHTML = "";
    state.sparkXY = [];
    state.sparkPoints = [];

    if (!points || points.length < 2) {
      els.sparkEmpty.style.display = "grid";
      if (els.sparkTip) els.sparkTip.classList.remove("show");
      if (els.sparkCursor) els.sparkCursor.style.opacity = "0";
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

    const w = 600,
      h = 220;
    const padX = 18,
      padY = 18;
    const innerW = w - padX * 2;
    const innerH = h - padY * 2;

    let minV = Math.min(...values);
    let maxV = Math.max(...values);
    const span = Math.max(1, maxV - minV);
    minV = minV - span * 0.1;
    maxV = maxV + span * 0.1;

    const toX = (i) => padX + (i * innerW) / (points.length - 1);
    const toY = (v) => h - padY - ((v - minV) * innerH) / Math.max(1e-6, maxV - minV);

    const xy = points.map((p, i) => {
      const v = Number(p.avg_unit_price_yuan_sqm);
      const vv = Number.isFinite(v) ? v : values[0];
      return { x: toX(i), y: toY(vv), v: vv, month: p.month, count: p.count ?? 0 };
    });

    state.sparkXY = xy;
    state.sparkPoints = points;

    const dLine = smoothPath(xy);
    const dFill = `${dLine} L ${xy[xy.length - 1].x.toFixed(1)} ${(h - padY).toFixed(
      1
    )} L ${xy[0].x.toFixed(1)} ${(h - padY).toFixed(1)} Z`;

    const ticks = [];
    ticks.push({ i: 0, label: xy[0].month });
    if (xy.length > 12) {
      const mid = Math.floor((xy.length - 1) / 2);
      ticks.push({ i: mid, label: xy[mid].month });
    }
    ticks.push({ i: xy.length - 1, label: xy[xy.length - 1].month });

    const gridLines = Array.from({ length: 4 })
      .map((_, i) => {
        const y = padY + (i * innerH) / 3;
        return `<line x1="${padX}" y1="${y.toFixed(1)}" x2="${(w - padX).toFixed(
          1
        )}" y2="${y.toFixed(1)}" stroke="rgba(255,255,255,.10)" stroke-width="1"/>`;
      })
      .join("");

    const yMaxLabel = escapeHtml(fmtNum0(maxV));
    const yMinLabel = escapeHtml(fmtNum0(minV));

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

    ${gridLines}

    <text x="${w - padX}" y="${padY + 10}" text-anchor="end" font-size="12" fill="rgba(234,240,255,.65)">${yMaxLabel}</text>
    <text x="${w - padX}" y="${h - padY}" text-anchor="end" font-size="12" fill="rgba(234,240,255,.45)">${yMinLabel}</text>

    <path d="${dFill}" fill="url(#gFill)"></path>
    <path d="${dLine}" fill="none" stroke="url(#gLine)" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"></path>

    ${xy
        .map(
          (p) =>
            `<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="3.2" fill="rgba(234,240,255,.92)" opacity=".9"><title>${escapeHtml(
              `${p.month} · ${fmtUnitPrice(p.v)} ${t("trend.unit_suffix")}`
            )}</title></circle>`
        )
        .join("")}

    ${ticks
        .map((tk) => {
          const x = toX(tk.i);
          return `<text x="${x.toFixed(1)}" y="${(h - 4).toFixed(
            1
          )}" text-anchor="middle" font-size="12" fill="rgba(234,240,255,.55)">${escapeHtml(tk.label)}</text>`;
        })
        .join("")}
  `;
  }

  function renderTrendList(points, cityKey) {
    if (!els.trendList) return;
    if (!points || !points.length) {
      els.trendList.innerHTML = "";
      return;
    }

    const n = isTaiwanCity(cityKey) ? 12 : 8;

    els.trendList.innerHTML = points
      .slice()
      .reverse()
      .slice(0, n)
      .map((p) => {
        const avgTotal = fmtTotalWan(p.avg_total_price_wan);
        const avgUnit = fmtUnitPrice(p.avg_unit_price_yuan_sqm);
        const unitSuffix = t("trend.unit_suffix");

        return `
        <li>
          <div>
            <div><b>${escapeHtml(p.month)}</b> · <span style="color:rgba(234,240,255,.68)">${escapeHtml(
          t("trend.samples")
        )}</span> ${escapeHtml(String(p.count ?? 0))}</div>
            <div style="color:rgba(234,240,255,.68)">${escapeHtml(t("trend.avg_total", { v: avgTotal }))}</div>
          </div>
          <div style="text-align:right">
            <div><b>${escapeHtml(avgUnit)}</b></div>
            <div style="color:rgba(234,240,255,.68)">${escapeHtml(unitSuffix)}</div>
          </div>
        </li>`;
      })
      .join("");
  }

  function updateSparkHover(clientX) {
    if (!els.sparkWrap || !els.sparkTip || !els.sparkCursor) return;
    const xy = state.sparkXY;
    if (!xy || xy.length < 2) return;

    const rect = els.sparkWrap.getBoundingClientRect();
    const x = Math.max(0, Math.min(rect.width, clientX - rect.left));
    const idx = Math.max(0, Math.min(xy.length - 1, Math.round((x / rect.width) * (xy.length - 1))));
    const p = xy[idx];

    const suffix = t("trend.unit_suffix");
    const tipText = t("spark.tip", {
      month: p.month,
      unit: fmtUnitPrice(p.v),
      suffix,
      count: p.count ?? 0,
    });

    els.sparkTip.textContent = tipText;
    els.sparkTip.classList.add("show");

    const leftPx = Math.round((idx / (xy.length - 1)) * rect.width);
    els.sparkCursor.style.left = `${leftPx}px`;
    els.sparkCursor.style.opacity = "1";

    // tooltip position (keep within bounds)
    const pad = 14;
    const tipRect = els.sparkTip.getBoundingClientRect();
    const preferLeft = leftPx + pad;
    const maxLeft = rect.width - tipRect.width - pad;
    const finalLeft = Math.max(pad, Math.min(maxLeft, preferLeft));

    els.sparkTip.style.left = `${finalLeft}px`;
  }

  function bindSparkHover() {
    if (!els.sparkWrap) return;

    // bind once
    if (els.sparkWrap.dataset.hoverBound === "1") return;
    els.sparkWrap.dataset.hoverBound = "1";

    const onMove = (ev) => {
      if (!state.sparkXY || state.sparkXY.length < 2) return;
      const x = ev.touches?.[0]?.clientX ?? ev.clientX;
      if (!Number.isFinite(x)) return;
      updateSparkHover(x);
    };

    const onLeave = () => {
      if (els.sparkTip) els.sparkTip.classList.remove("show");
      if (els.sparkCursor) els.sparkCursor.style.opacity = "0";
    };

    els.sparkWrap.addEventListener("mousemove", onMove);
    els.sparkWrap.addEventListener("touchmove", onMove, { passive: true });
    els.sparkWrap.addEventListener("mouseleave", onLeave);
    els.sparkWrap.addEventListener("touchend", onLeave);
  }

  // ===== news =====
  function fmtLocalTime(iso) {
    if (!iso) return "-";
    try {
      const d = new Date(iso);
      if (!Number.isFinite(d.getTime())) return String(iso);
      return d.toLocaleString(state.localeTag, { hour12: false });
    } catch {
      return String(iso);
    }
  }

  function setNewsMeta(cityKey, isoTime, { sourceUrl = "" } = {}) {
    if (!els.newsMeta) return;
    els.newsMeta.textContent = t("news.meta", {
      city: cityName(cityKey),
      time: fmtLocalTime(isoTime),
    });
    els.newsMeta.title = sourceUrl || "";
  }

  function renderNewsSkeleton(n = 6) {
    if (!els.newsList) return;
    if (els.newsEmpty) els.newsEmpty.style.display = "none";

    els.newsList.innerHTML = Array.from({ length: n })
      .map(
        (_, i) => `
        <li class="news-item" aria-hidden="true">
          <div class="news-rank">${i + 1}</div>
          <div style="flex:1;min-width:0">
            <div class="skeleton" style="height:14px;width:92%"></div>
            <div class="skeleton" style="height:12px;width:58%;margin-top:8px"></div>
          </div>
        </li>`
      )
      .join("");
  }

  function renderNews(items, cityKey, fetchedAt, sourceUrl) {
    if (!els.newsList) return;

    const arr = Array.isArray(items) ? items : [];
    if (!arr.length) {
      els.newsList.innerHTML = "";
      if (els.newsEmpty) els.newsEmpty.style.display = "grid";
      setNewsMeta(cityKey, fetchedAt, { sourceUrl });
      return;
    }

    if (els.newsEmpty) els.newsEmpty.style.display = "none";

    els.newsList.innerHTML = arr
      .map((x) => {
        const rank = x.rank ?? "-";
        const url = x.url || "";
        const title = x.title || "-";
        const sub = x.sub || "";

        return `
          <li class="news-item">
            <div class="news-rank">${escapeHtml(rank)}</div>
            <div style="flex:1;min-width:0">
              <a class="news-title" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(
          title
        )}</a>
              ${sub ? `<div class="news-sub">${escapeHtml(sub)}</div>` : ""}
            </div>
          </li>`;
      })
      .join("");

    setNewsMeta(cityKey, fetchedAt, { sourceUrl });
  }

  async function loadNews(cityKey, { force = false } = {}) {
    const city = String(cityKey || "").trim().toLowerCase();
    if (!city || !els.newsList) return;

    const now = Date.now();
    const fresh = now - (state.newsLastFetchedAt || 0) < 5 * 60 * 1000;
    if (!force && city === state.newsCity && fresh) return;

    if (state.ctrlNews) state.ctrlNews.abort();
    state.ctrlNews = new AbortController();

    state.newsLoading = true;
    if (els.btnNewsRefresh) els.btnNewsRefresh.disabled = true;
    renderNewsSkeleton(6);
    setNewsMeta(city, new Date().toISOString());

    try {
      const data = await apiGet("/api/fang_news", { city, limit: 10 }, { signal: state.ctrlNews.signal });
      state.newsCity = city;
      state.newsLastFetchedAt = Date.now();
      renderNews(data.items || [], city, data.fetched_at, data.source_url);
    } catch (e) {
      state.newsCity = city;
      state.newsLastFetchedAt = Date.now();
      renderNews([], city, new Date().toISOString(), "");
      if (e?.name !== "AbortError") toast(`${t("toast.news_fail")}：${e.message}`);
    } finally {
      state.newsLoading = false;
      if (els.btnNewsRefresh) els.btnNewsRefresh.disabled = false;
    }
  }

  async function loadListingsAndTrend() {
    const q = getQuery();
    if (!q.city) {
      toast(t("toast.need_city"));
      return;
    }

    applyLocaleByCity(q.city);
    if (els.navCity && els.navCity.value !== q.city) els.navCity.value = q.city;

    // cancel previous
    if (state.ctrlList) state.ctrlList.abort();
    if (state.ctrlTrend) state.ctrlTrend.abort();
    state.ctrlList = new AbortController();
    state.ctrlTrend = new AbortController();

    state.loading = true;
    if (els.btnSearch) els.btnSearch.disabled = true;
    updatePager();

    renderSkeleton(Math.min(state.pageSize, 12));
    setMeta(t("meta.loading"));
    setListState(t("list.loading"));

    try {
      const data = await apiGet("/api/listings", q, { signal: state.ctrlList.signal });
      const items = data.items || [];
      state.total = data.total || 0;
      state.maxPage = Math.max(1, Math.ceil(state.total / state.pageSize));
      renderTable(items);
      setMeta(t("meta.done", { n: state.total }));

      if (items.length && els.tableWrap) {
        // 翻页后将滚动容器回到顶部，防止“看不到新页内容”
        els.tableWrap.scrollTop = 0;
      }
    } catch (e) {
      if (e?.name === "AbortError") return;

      if (els.tbody) {
        els.tbody.innerHTML = `<tr><td colspan="8" style="padding:16px;color:#ffb3c7;">${escapeHtml(
          t("meta.fail")
        )}：${escapeHtml(e.message)}</td></tr>`;
      }
      setMeta(t("meta.fail"));
      setListState(`${t("meta.fail")}：${e.message}`);
      toast(e.message);
    } finally {
      state.loading = false;
      if (els.btnSearch) els.btnSearch.disabled = false;
      updatePager();
    }

    // trend
    try {
      const tdata = await apiGet(
        "/api/price_trend",
        {
          city: q.city,
          region: q.region,
          bizcircle: q.bizcircle,
          community: q.community,
          layout: q.layout,
        },
        { signal: state.ctrlTrend.signal }
      );

      const pointsAll = tdata.points || [];
      const points = filterTrendPoints(pointsAll, q.city);
      updateTrendDesc(q.city, points);
      renderSpark(points);
      renderTrendList(points, q.city);
      bindSparkHover();
    } catch (e) {
      if (e?.name === "AbortError") return;
      updateTrendDesc(q.city, []);
      clearSpark();
      renderTrendList([], q.city);
    }

    // news (节流在 loadNews 内)
    loadNews(q.city).catch(() => void 0);
  }

  // ===== 事件绑定 =====
  function bindEvents() {
    // filters: click search
    els.btnSearch?.addEventListener("click", () => {
      state.page = 1;
      loadListingsAndTrend();
    });

    // Enter 快捷查询（输入框内）
    els.filtersForm?.addEventListener("keydown", (e) => {
      if (e.key !== "Enter") return;
      const tag = (e.target?.tagName || "").toUpperCase();
      if (tag === "SELECT") return;
      if (e.isComposing) return;
      e.preventDefault();
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
      if (els.fRegion) els.fRegion.focus();
      loadListingsAndTrend();
    });

    els.btnNewsRefresh?.addEventListener("click", () => {
      loadNews(els.fCity?.value, { force: true });
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

    // table: click row / open link
    const handleRowOpen = (tr, { openLink = false } = {}) => {
      if (!tr || !tr.dataset.json) return;

      let obj;
      try {
        obj = JSON.parse(decodeURIComponent(tr.dataset.json));
      } catch {
        toast(t("toast.parse_fail"));
        return;
      }

      if (openLink) {
        const url = obj?.detail_url;
        if (url) window.open(url, "_blank", "noopener,noreferrer");
        else toast(t("toast.no_link"));
        return;
      }

      openModal(obj, { focusFrom: tr });
    };

    els.tbody?.addEventListener("click", (ev) => {
      const btn = ev.target.closest("[data-open='1']");
      const tr = ev.target.closest("tr");
      if (!tr) return;

      if (btn) {
        ev.preventDefault();
        ev.stopPropagation();
        handleRowOpen(tr, { openLink: true });
        return;
      }

      handleRowOpen(tr, { openLink: false });
    });

    // keyboard open (only when focus is on the row itself, not inner buttons/links)
    els.tbody?.addEventListener("keydown", (ev) => {
      const tag = (ev.target?.tagName || "").toUpperCase();
      if (tag === "BUTTON" || tag === "A" || tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA") return;
      if (ev.target?.closest?.("[data-open='1']")) return;

      const tr = ev.target.closest("tr");
      if (!tr) return;

      if (ev.key === "Enter" || ev.key === " ") {
        ev.preventDefault();
        handleRowOpen(tr, { openLink: false });
      }
    });

    // modal close
    els.modalClose?.addEventListener("click", () => closeModal());
    els.modalBackdrop?.addEventListener("click", () => closeModal());

    // navbar city switch
    els.navCity?.addEventListener("change", () => {
      if (els.fCity) els.fCity.value = els.navCity.value;
      state.page = 1;
      loadListingsAndTrend();
      setNavOpen(false);
    });

    // navbar refresh
    els.navRefresh?.addEventListener("click", () => {
      state.page = 1;
      loadListingsAndTrend();
      loadNews(els.navCity?.value || els.fCity?.value, { force: true });
      setNavOpen(false);
    });

    // burger
    els.navBurger?.addEventListener("click", (e) => {
      e.stopPropagation();
      setNavOpen(!state.navOpen);
    });

    // overlay click
    els.navOverlay?.addEventListener("click", () => {
      setNavOpen(false);
    });

    // click nav link closes
    els.navCenter?.addEventListener("click", (e) => {
      const a = e.target.closest("a");
      if (!a) return;
      setNavOpen(false);
    });

    // click outside navbar closes (desktop / fallback)
    document.addEventListener("click", (e) => {
      if (!state.navOpen) return;
      const insideNavbar = els.navbar && els.navbar.contains(e.target);
      if (!insideNavbar) setNavOpen(false);
    });

    window.addEventListener("resize", () => {
      if (window.innerWidth > 1200) setNavOpen(false);
    });

    // filter city -> sync nav
    els.fCity?.addEventListener("change", () => {
      if (els.navCity) els.navCity.value = els.fCity.value;
      state.page = 1;
      loadListingsAndTrend();
    });

    // Esc: close menu if open (modal 自己处理)
    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !state.modalOpen && state.navOpen) setNavOpen(false);
    });
  }

  // ===== 初始化 =====
  (async function init() {
    renderSkeleton(10);
    setListState(t("list.loading"));
    bindEvents();

    try {
      await loadHealthAndCities();
      setMeta(t("meta.ready"));
      if (els.fCity?.value) await loadListingsAndTrend();
    } catch (e) {
      if (els.badgeApi) els.badgeApi.textContent = t("badge.api_bad");
      toast(e.message);
      setListState(`${t("meta.fail")}：${e.message}`);
    } finally {
      updatePager();
    }
  })();
})();
