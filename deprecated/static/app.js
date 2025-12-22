(() => {
    const $ = (id) => document.getElementById(id);

    const els = {
        badgeStatus: $("badge-status"),
        badgeCount: $("badge-count"),
        chipTip: $("chip-tip"),
        metaInfo: $("meta-info"),

        fRegion: $("f-region"),
        fBizcircle: $("f-bizcircle"),
        fCommunity: $("f-community"),
        fLayout: $("f-layout"),

        btnSearch: $("btn-search"),
        btnReset: $("btn-reset"),
        btnPrev: $("btn-prev"),
        btnNext: $("btn-next"),
        pageSize: $("page-size"),
        pagerText: $("pager-text"),

        tbody: $("tbody"),

        trendArea: $("trend-area"),
        trendEmpty: $("trend-empty"),
        spark: $("spark"),
        trendList: $("trend-list"),

        toast: $("toast"),

        modal: $("modal"),
        modalBackdrop: $("modal-backdrop"),
        modalClose: $("modal-close"),
        modalJson: $("modal-json"),
    };

    const state = {
        page: 1,
        pageSize: parseInt(els.pageSize.value, 10) || 20,
        total: 0,
        maxPage: 1,
        loading: false,
        filters: { region: "", bizcircle: "", community: "", layout: "" },
    };

    function toast(msg) {
        els.toast.textContent = msg;
        els.toast.classList.remove("show");
        // 触发 reflow 以重启动画
        void els.toast.offsetWidth;
        els.toast.classList.add("show");
    }

    function setMeta(text) {
        els.metaInfo.textContent = text;
    }

    function qs(params) {
        const usp = new URLSearchParams();
        Object.entries(params).forEach(([k, v]) => {
            if (v !== undefined && v !== null && String(v).trim().length > 0) usp.set(k, String(v).trim());
        });
        return usp.toString();
    }

    async function apiGet(path, params = {}) {
        const url = `${path}${Object.keys(params).length ? `?${qs(params)}` : ""}`;
        const res = await fetch(url, { headers: { "Accept": "application/json" } });
        if (!res.ok) {
            const t = await res.text();
            throw new Error(`HTTP ${res.status}: ${t}`);
        }
        return await res.json();
    }

    function renderSkeleton(rows = 10) {
        const cols = 9;
        const html = Array.from({ length: rows }).map(() => {
            const tds = Array.from({ length: cols }).map(() => `<td><div class="skeleton"></div></td>`).join("");
            return `<tr>${tds}</tr>`;
        }).join("");
        els.tbody.innerHTML = html;
    }

    function fmt(x) {
        if (x === null || x === undefined) return "-";
        return String(x);
    }

    function renderTable(items) {
        if (!items || !items.length) {
            els.tbody.innerHTML = `<tr><td colspan="9" style="padding:16px;color:rgba(234,240,255,.65);">暂无数据（请调整筛选条件）</td></tr>`;
            return;
        }

        els.tbody.innerHTML = items.map((r) => {
            const data = encodeURIComponent(JSON.stringify(r));
            return `
        <tr data-json="${data}">
          <td>${fmt(r.house_id)}</td>
          <td>${fmt(r.region)}</td>
          <td>${fmt(r.bizcircle)}</td>
          <td>${fmt(r.community)}</td>
          <td>${fmt(r.layout)}</td>
          <td class="num">${fmt(r.area_sqm)}</td>
          <td class="num">${fmt(r.unit_price_yuan_sqm)}</td>
          <td class="num">${fmt(r.total_price_wan)}</td>
          <td>${fmt(r.deal_date)}</td>
        </tr>
      `;
        }).join("");
    }

    function updatePager() {
        els.pagerText.textContent = `第 ${state.page} / ${state.maxPage} 页`;
        els.btnPrev.disabled = state.loading || state.page <= 1;
        els.btnNext.disabled = state.loading || state.page >= state.maxPage;
    }

    function getFiltersFromUI() {
        state.filters.region = els.fRegion.value.trim();
        state.filters.bizcircle = els.fBizcircle.value.trim();
        state.filters.community = els.fCommunity.value.trim();
        state.filters.layout = els.fLayout.value.trim();
    }

    async function loadHealth() {
        try {
            const h = await apiGet("/api/health");
            if (h && h.ok) {
                els.badgeStatus.textContent = "API：OK";
                const count = h.boot && typeof h.boot.count !== "undefined" ? h.boot.count : "—";
                els.badgeCount.textContent = `记录：${count}`;
            } else {
                els.badgeStatus.textContent = "API：异常";
            }
        } catch (e) {
            els.badgeStatus.textContent = "API：不可用";
            toast(`健康检查失败：${e.message}`);
        }
    }

    async function loadListings() {
        state.loading = true;
        updatePager();
        renderSkeleton(Math.min(state.pageSize, 12));
        setMeta("正在加载列表…");

        try {
            const data = await apiGet("/api/listings", {
                ...state.filters,
                page: state.page,
                page_size: state.pageSize,
            });

            const items = data.items || [];
            state.total = data.total || 0;
            state.page = data.page || state.page;
            state.pageSize = data.page_size || state.pageSize;
            state.maxPage = Math.max(1, Math.ceil(state.total / state.pageSize));

            renderTable(items);
            setMeta(`加载完成：共 ${state.total} 条`);
        } catch (e) {
            els.tbody.innerHTML = `<tr><td colspan="9" style="padding:16px;color:#ffb3c7;">加载失败：${e.message}</td></tr>`;
            setMeta("加载失败");
            toast(`列表加载失败：${e.message}`);
        } finally {
            state.loading = false;
            updatePager();
        }
    }

    function clearSpark() {
        els.spark.innerHTML = "";
    }

    function renderSparkline(points) {
        clearSpark();
        if (!points || points.length < 2) return;

        const values = points.map(p => Number(p.avg_unit_price_yuan_sqm)).filter(v => Number.isFinite(v));
        if (values.length < 2) return;

        const w = 600, h = 220;
        const padX = 18, padY = 18;

        const minV = Math.min(...values);
        const maxV = Math.max(...values);
        const span = Math.max(1, maxV - minV);

        const toX = (i) => padX + (i * (w - padX * 2)) / (points.length - 1);
        const toY = (v) => (h - padY) - ((v - minV) * (h - padY * 2)) / span;

        const xy = points.map((p, i) => {
            const v = Number(p.avg_unit_price_yuan_sqm);
            return { x: toX(i), y: toY(Number.isFinite(v) ? v : minV) };
        });

        // defs（渐变）
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
    `;

        // 网格线
        const grid = Array.from({ length: 4 }).map((_, i) => {
            const y = padY + ((h - padY * 2) * i) / 3;
            return `<line x1="0" y1="${y}" x2="${w}" y2="${y}" stroke="rgba(255,255,255,.06)" />`;
        }).join("");
        els.spark.insertAdjacentHTML("beforeend", grid);

        // path
        const d = xy.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(" ");
        const dFill = `${d} L ${xy[xy.length - 1].x.toFixed(1)} ${(h - padY).toFixed(1)} L ${xy[0].x.toFixed(1)} ${(h - padY).toFixed(1)} Z`;

        els.spark.insertAdjacentHTML("beforeend", `
      <path d="${dFill}" fill="url(#gFill)"></path>
      <path d="${d}" fill="none" stroke="url(#gLine)" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"></path>
    `);

        // 点
        const dots = xy.map((p) =>
            `<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="3.4" fill="rgba(234,240,255,.92)" opacity=".9"></circle>`
        ).join("");
        els.spark.insertAdjacentHTML("beforeend", dots);
    }

    function renderTrendList(points) {
        if (!points || !points.length) {
            els.trendList.innerHTML = "";
            return;
        }
        els.trendList.innerHTML = points.slice().reverse().slice(0, 8).map(p => {
            return `
        <li>
          <div>
            <div><b>${p.month}</b> <span class="kv">样本</span> ${p.count}</div>
            <div class="kv">均总价（万）: ${fmt(p.avg_total_price_wan)}</div>
          </div>
          <div style="text-align:right">
            <div><b>${fmt(p.avg_unit_price_yuan_sqm)}</b></div>
            <div class="kv">元/㎡</div>
          </div>
        </li>
      `;
        }).join("");
    }

    async function loadTrend() {
        try {
            const data = await apiGet("/api/price_trend", { ...state.filters });
            const points = data.points || [];
            if (!points.length) {
                els.trendEmpty.style.display = "grid";
                clearSpark();
                renderTrendList([]);
                return;
            }
            els.trendEmpty.style.display = "none";
            renderSparkline(points);
            renderTrendList(points);
        } catch (e) {
            els.trendEmpty.style.display = "grid";
            clearSpark();
            renderTrendList([]);
        }
    }

    function openModal(obj) {
        els.modalJson.textContent = JSON.stringify(obj, null, 2);
        els.modal.classList.remove("hidden");
        els.modal.setAttribute("aria-hidden", "false");
    }

    function closeModal() {
        els.modal.classList.add("hidden");
        els.modal.setAttribute("aria-hidden", "true");
    }

    // 事件绑定
    els.btnSearch.addEventListener("click", async () => {
        getFiltersFromUI();
        state.page = 1;
        await loadListings();
        await loadTrend();
    });

    els.btnReset.addEventListener("click", async () => {
        els.fRegion.value = "";
        els.fBizcircle.value = "";
        els.fCommunity.value = "";
        els.fLayout.value = "";
        getFiltersFromUI();
        state.page = 1;
        toast("已重置筛选条件");
        await loadListings();
        await loadTrend();
    });

    els.btnPrev.addEventListener("click", async () => {
        if (state.page <= 1) return;
        state.page -= 1;
        await loadListings();
    });

    els.btnNext.addEventListener("click", async () => {
        if (state.page >= state.maxPage) return;
        state.page += 1;
        await loadListings();
    });

    els.pageSize.addEventListener("change", async () => {
        state.pageSize = parseInt(els.pageSize.value, 10) || 20;
        state.page = 1;
        toast(`每页 ${state.pageSize} 条`);
        await loadListings();
    });

    els.tbody.addEventListener("click", (ev) => {
        const tr = ev.target.closest("tr");
        if (!tr || !tr.dataset.json) return;
        try {
            const obj = JSON.parse(decodeURIComponent(tr.dataset.json));
            openModal(obj);
        } catch {
            toast("解析该行 JSON 失败");
        }
    });

    els.modalClose.addEventListener("click", closeModal);
    els.modalBackdrop.addEventListener("click", closeModal);
    window.addEventListener("keydown", (e) => {
        if (e.key === "Escape") closeModal();
    });

    // 初始化
    (async function init() {
        els.chipTip.textContent = "同源访问：/api/listings & /api/price_trend";
        renderSkeleton(10);
        await loadHealth();
        getFiltersFromUI();
        await loadListings();
        await loadTrend();
        toast("页面已就绪（点击表格行查看详情）");
    })();
})();
