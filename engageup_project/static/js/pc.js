// --- サイドバー開閉の切り替えと状態保存 ---
function toggleSidebar() {
  const layout = document.getElementById("adminLayout");
  const icon = document.getElementById("toggleIcon");
  if (!layout) return;

  // クラスの付け外し
  const isCollapsed = layout.classList.toggle("sidebar-collapsed");

  // アイコンの向きを更新
  if (icon) {
    icon.innerText = isCollapsed ? "chevron_right" : "chevron_left";
  }

  // 状態をブラウザに保存
  localStorage.setItem("sidebarStatus", isCollapsed ? "collapsed" : "expanded");
}

// 画面が描画される前にクラスを付与してチラつきを防ぐ
if (localStorage.getItem("sidebarStatus") === "collapsed") {
  document.getElementById("adminLayout").classList.add("sidebar-collapsed");
}

// --- テーマ切り替え (Color) ---
function setTheme(themeName) {
  const currentMode = document.body.classList.contains("mode-dark")
    ? "mode-dark"
    : "mode-light";
  document.body.className = `${themeName} ${currentMode}`;
  localStorage.setItem("selectedTheme", themeName);
}

// --- モード切り替え (Light/Dark) ---
function setMode(modeName) {
  const currentTheme =
    Array.from(document.body.classList).find((c) => c.startsWith("theme-")) ||
    "theme-green";
  document.body.className = `${currentTheme} ${modeName}`;
  localStorage.setItem("selectedMode", modeName);

  // ボタンの見た目更新 (Customizeメニュー内のボタン)
  document
    .querySelectorAll(".mode-btn")
    .forEach((btn) => btn.classList.remove("active"));
  const targetBtn = document.getElementById(`btn-${modeName.split("-")[1]}`);
  if (targetBtn) targetBtn.classList.add("active");
}

// --- フォントサイズ調節 ---
function setFontSize(size) {
  document.documentElement.style.fontSize = size + "%";
  const valLabel = document.getElementById("font-size-val");
  if (valLabel) valLabel.innerText = size + "%";
  localStorage.setItem("selectedFontSize", size);
}

// --- 今日の日付表示更新 ---
function updateCurrentDate() {
  const dateSpan = document.getElementById("current-date");
  if (dateSpan) {
    const now = new Date();
    dateSpan.textContent = `${now.getFullYear()}.${String(now.getMonth() + 1).padStart(2, "0")}.${String(now.getDate()).padStart(2, "0")}`;
  }
}

// --- ページ読み込み時の初期設定 (一括) ---
document.addEventListener("DOMContentLoaded", () => {
  const layout = document.getElementById("adminLayout");
  const icon = document.getElementById("toggleIcon");

  // 1. 日付の更新
  updateCurrentDate();

  // 2. localStorage から以前の設定を読み込む (なければデフォルト)
  const savedTheme = localStorage.getItem("selectedTheme") || "theme-green";
  const savedMode = localStorage.getItem("selectedMode") || "mode-light";
  const savedFontSize = localStorage.getItem("selectedFontSize") || "100";
  const savedSidebar = localStorage.getItem("sidebarStatus");

  // 3. 設定の適用
  setTheme(savedTheme);
  setMode(savedMode);
  setFontSize(savedFontSize);

  // 設定メニューのスライダー位置を復元
  const sizeRange = document.getElementById("fontSizeRange");
  if (sizeRange) sizeRange.value = savedFontSize;

  // 4. サイドバー状態の復元
  if (layout) {
    if (savedSidebar === "collapsed") {
      layout.classList.add("sidebar-collapsed");
      if (icon) icon.innerText = "chevron_right";
    } else {
      layout.classList.remove("sidebar-collapsed");
      if (icon) icon.innerText = "chevron_left";
    }
  }
});

document.addEventListener("DOMContentLoaded", function () {
  const rows = document.querySelectorAll(".user-row");
  const bulkForm = document.getElementById("user-bulk-form");
  const actionInput = document.getElementById("bulk-action-input");

  // モーダルの初期化
  const statusModalEl = document.getElementById("statusModal");
  const alertModalEl = document.getElementById("alertModal");
  const statusModal = statusModalEl ? new bootstrap.Modal(statusModalEl) : null;
  const alertModal = alertModalEl ? new bootstrap.Modal(alertModalEl) : null;

  const loadingText = document.getElementById("loading-text");
  const alertModalMsg = document.getElementById("alert-modal-msg");

  // 行選択機能
  rows.forEach((row) => {
    row.addEventListener("click", function (e) {
      if (e.target.type === "checkbox" || e.target.tagName === "A") return;
      const checkbox = this.querySelector(".row-checkbox");
      if (checkbox && !checkbox.disabled) {
        checkbox.checked = !checkbox.checked;
        checkbox.checked
          ? this.classList.add("table-selected")
          : this.classList.remove("table-selected");
      }
    });
  });

  // ボタンのクリックイベント（削除・復元）
  document.querySelectorAll(".action-trigger").forEach((btn) => {
    btn.addEventListener("click", function () {
      const action = this.dataset.action;
      const msg = this.dataset.msg;
      const checkedCount = document.querySelectorAll(
        ".row-checkbox:checked",
      ).length;

      if (checkedCount === 0) {
        if (alertModal) {
          alertModalMsg.innerText =
            "操作するユーザーを一人以上選択してください。";
          alertModal.show();
        }
        return;
      }

      if (statusModal) {
        loadingText.innerText = msg;
        actionInput.value = action;
        statusModal.show();

        setTimeout(() => {
          document.getElementById("modal-loading").style.display = "none";
          document.getElementById("modal-success").style.display = "block";
          setTimeout(() => {
            bulkForm.submit();
          }, 800);
        }, 1200);
      }
    });
  });

  // チェックボックス直接操作のハイライト
  document.querySelectorAll(".row-checkbox").forEach((cb) => {
    cb.addEventListener("change", function () {
      const row = this.closest("tr");
      this.checked
        ? row.classList.add("table-selected")
        : row.classList.remove("table-selected");
    });
  });
});

// サイドバー開閉の切り替えと状態保存
function toggleSidebar() {
  const layout = document.getElementById("adminLayout");
  const icon = document.getElementById("toggleIcon");
  if (!layout) return;

  // クラスの付け外し
  const isCollapsed = layout.classList.toggle("sidebar-collapsed");

  // アイコンの向きを更新
  if (icon) {
    icon.innerText = isCollapsed ? "chevron_right" : "chevron_left";
  }

  // 状態をブラウザに保存
  localStorage.setItem("sidebarStatus", isCollapsed ? "collapsed" : "expanded");
}

// --- テーマ切り替え (Color) ---
function setTheme(themeName) {
  const currentMode = document.body.classList.contains("mode-dark")
    ? "mode-dark"
    : "mode-light";
  document.body.className = `${themeName} ${currentMode}`;
  localStorage.setItem("selectedTheme", themeName);
}

// --- モード切り替え (Light/Dark) ---
function setMode(modeName) {
  const currentTheme =
    Array.from(document.body.classList).find((c) => c.startsWith("theme-")) ||
    "theme-green";
  document.body.className = `${currentTheme} ${modeName}`;
  localStorage.setItem("selectedMode", modeName);

  // ボタンの見た目更新 (Customizeメニュー内のボタン)
  document
    .querySelectorAll(".mode-btn")
    .forEach((btn) => btn.classList.remove("active"));
  const targetBtn = document.getElementById(`btn-${modeName.split("-")[1]}`);
  if (targetBtn) targetBtn.classList.add("active");
}

// --- フォントサイズ調節 ---
function setFontSize(size) {
  document.documentElement.style.fontSize = size + "%";
  const valLabel = document.getElementById("font-size-val");
  if (valLabel) valLabel.innerText = size + "%";
  localStorage.setItem("selectedFontSize", size);
}

// --- 今日の日付表示更新 ---
function updateCurrentDate() {
  const dateSpan = document.getElementById("current-date");
  if (dateSpan) {
    const now = new Date();
    dateSpan.textContent = `${now.getFullYear()}.${String(now.getMonth() + 1).padStart(2, "0")}.${String(now.getDate()).padStart(2, "0")}`;
  }
}

// --- ページ読み込み時の初期設定 (一括) ---
document.addEventListener("DOMContentLoaded", () => {
  const layout = document.getElementById("adminLayout");
  const icon = document.getElementById("toggleIcon");

  // 1. 日付の更新
  updateCurrentDate();

  // 2. localStorage から以前の設定を読み込む (なければデフォルト)
  const savedTheme = localStorage.getItem("selectedTheme") || "theme-green";
  const savedMode = localStorage.getItem("selectedMode") || "mode-light";
  const savedFontSize = localStorage.getItem("selectedFontSize") || "100";
  const savedSidebar = localStorage.getItem("sidebarStatus");

  // 3. 設定の適用
  setTheme(savedTheme);
  setMode(savedMode);
  setFontSize(savedFontSize);

  // 設定メニューのスライダー位置を復元
  const sizeRange = document.getElementById("fontSizeRange");
  if (sizeRange) sizeRange.value = savedFontSize;

  // 4. サイドバー状態の復元
  if (layout) {
    if (savedSidebar === "collapsed") {
      layout.classList.add("sidebar-collapsed");
      if (icon) icon.innerText = "chevron_right";
    } else {
      layout.classList.remove("sidebar-collapsed");
      if (icon) icon.innerText = "chevron_left";
    }
  }
});

document.addEventListener("DOMContentLoaded", function () {
  const saveBtn = document.getElementById("save-trigger");
  const form = document.getElementById("constant-update-form");
  const statusModal = new bootstrap.Modal(
    document.getElementById("statusModal"),
  );

  saveBtn.addEventListener("click", function () {
    // モーダル表示
    statusModal.show();

    // 1秒間の演出のあとに送信
    setTimeout(() => {
      document.getElementById("modal-loading").style.display = "none";
      document.getElementById("modal-success").style.display = "block";

      setTimeout(() => {
        form.submit(); // ここで実際に保存が走ります
      }, 800);
    }, 1200);
  });
});
