(() => {
    const ENTER_AFTER_MS = 2600;     // 与 loadBar 动画时长匹配
    const INDEX_URL = "/index.html"; // 主界面入口（你已有 index.html）

    const hint = document.getElementById("hint-text");
    const enterBtn = document.getElementById("enterBtn");

    // 可选：避免每次刷新都看 init（想每次都显示就删除这段）


    const steps = ["初始化中…", "加载数据源…", "构建趋势索引…", "准备进入…"];
    let i = 0;
    const t = setInterval(() => {
        i = (i + 1) % steps.length;
        hint.textContent = steps[i];
    }, 520);

    function go() {
        clearInterval(t);
        localStorage.setItem("hpqaq_seen_init", "1");
        window.location.href = INDEX_URL;
    }

    enterBtn.addEventListener("click", go);
    setTimeout(go, ENTER_AFTER_MS);
})();
