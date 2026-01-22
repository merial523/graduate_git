/**
 * EngageUp 共通JavaScriptプログラム
 */

// ==========================================================
// 1. コアシステム機能
// ==========================================================

function toggleSidebar() {
  const layout = document.getElementById("adminLayout");
  const icon = document.getElementById("toggleIcon");
  if (!layout) return;

  const isCollapsed = layout.classList.toggle("sidebar-collapsed");
  if (icon) {
    icon.innerText = isCollapsed ? "chevron_right" : "chevron_left";
  }
  localStorage.setItem("sidebarStatus", isCollapsed ? "collapsed" : "expanded");
}

function setTheme(themeName) {
  const currentMode = document.body.classList.contains("mode-dark")
    ? "mode-dark"
    : "mode-light";
  document.body.className = `${themeName} ${currentMode}`;
  localStorage.setItem("selectedTheme", themeName);
}

function setMode(modeName) {
  const currentTheme =
    Array.from(document.body.classList).find((c) => c.startsWith("theme-")) ||
    "theme-green";
  document.body.className = `${currentTheme} ${modeName}`;
  localStorage.setItem("selectedMode", modeName);

  document
    .querySelectorAll(".mode-btn")
    .forEach((btn) => btn.classList.remove("active"));
  const targetBtn = document.getElementById(`btn-${modeName.split("-")[1]}`);
  if (targetBtn) targetBtn.classList.add("active");
}

function setFontSize(size) {
  document.documentElement.style.fontSize = size + "%";
  const valLabel = document.getElementById("font-size-val");
  if (valLabel) valLabel.innerText = size + "%";
  localStorage.setItem("selectedFontSize", size);
}

function updateCurrentDate() {
  const dateSpan = document.getElementById("current-date");
  if (dateSpan) {
    const now = new Date();
    dateSpan.textContent = `${now.getFullYear()}.${String(now.getMonth() + 1).padStart(2, "0")}.${String(now.getDate()).padStart(2, "0")}`;
  }
}

// ==========================================================
// 2. 画面初期化 ＆ フォーム演出
// ==========================================================

document.addEventListener("DOMContentLoaded", function () {
  const layout = document.getElementById("adminLayout");
  const icon = document.getElementById("toggleIcon");

  // --- 設定の復元 ---
  const savedTheme = localStorage.getItem("selectedTheme") || "theme-green";
  const savedMode = localStorage.getItem("selectedMode") || "mode-light";
  const savedFontSize = localStorage.getItem("selectedFontSize") || "100";
  const savedSidebar = localStorage.getItem("sidebarStatus");

  setTheme(savedTheme);
  setMode(savedMode);
  setFontSize(savedFontSize);
  updateCurrentDate();

  const sizeRange = document.getElementById("fontSizeRange");
  if (sizeRange) sizeRange.value = savedFontSize;

  if (layout && savedSidebar === "collapsed") {
    layout.classList.add("sidebar-collapsed");
    if (icon) icon.innerText = "chevron_right";
  }

  // --- モーダルの準備 ---
  const statusModalEl = document.getElementById("statusModal");
  const alertModalEl = document.getElementById("alertModal");
  const statusModal = statusModalEl ? new bootstrap.Modal(statusModalEl) : null;
  const alertModal = alertModalEl ? new bootstrap.Modal(alertModalEl) : null;

  /**
   * フォーム送信演出の共通ロジック
   * @param {HTMLElement} trigger - クリックされるボタン要素
   * @param {string} formId - 送信するフォームのID
   * @param {function} validationFn - 送信前のチェック関数
   */
  const executeFormAction = (trigger, formId, validationFn) => {
    const form = document.getElementById(formId);
    if (!trigger || !form) return;

    trigger.addEventListener("click", function () {
      if (validationFn && !validationFn()) return;

      if (statusModal) {
        const msg = trigger.dataset.msg;
        const loadingText = document.getElementById("loading-text");
        if (msg && loadingText) loadingText.innerText = msg;

        const actionInput = document.getElementById("bulk-action-input");
        if (actionInput && trigger.dataset.action) {
          actionInput.value = trigger.dataset.action;
        }

        statusModal.show();
        setTimeout(() => {
          document.getElementById("modal-loading").style.display = "none";
          document.getElementById("modal-success").style.display = "block";
          setTimeout(() => form.submit(), 800);
        }, 1200);
      } else {
        form.submit();
      }
    });
  };

  // --- 個別画面の設定 ---

  // 1. ユーザー一覧画面（削除・復元ボタン）
  document.querySelectorAll(".action-trigger").forEach((btn) => {
    executeFormAction(btn, "user-bulk-form", () => {
      const checkedCount = document.querySelectorAll(
        ".row-checkbox:checked",
      ).length;
      if (checkedCount === 0) {
        if (alertModal) {
          document.getElementById("alert-modal-msg").innerText =
            "対象を選択してください。";
          alertModal.show();
        } else {
          alert("対象を選択してください。");
        }
        return false;
      }
      return true;
    });
  });

  // 2. システム定数更新
  const constantBtn = document.getElementById("save-trigger");
  if (constantBtn) executeFormAction(constantBtn, "constant-update-form");

  // 3. ランク変更画面
  const rankBtn = document.getElementById("submit-trigger");
  if (rankBtn) {
    executeFormAction(rankBtn, "rank-update-form", () => {
      const checkedCount = document.querySelectorAll(
        ".row-checkbox:checked",
      ).length;
      const rankSelected = document.querySelector('input[name="rank"]:checked');
      if (checkedCount === 0 || !rankSelected) {
        alert("対象ユーザーと新しいランクを選択してください。");
        return false;
      }
      return true;
    });
  }

  // 4. アカウント作成画面
  const userCreateBtn = document.getElementById("submit-btn");
  if (userCreateBtn) executeFormAction(userCreateBtn, "create-user-form");

  // --- 特定コンポーネントの処理 ---

  // 行選択
  const rows = document.querySelectorAll(".user-row");
  rows.forEach((row) => {
    row.addEventListener("click", function (e) {
      if (
        this.classList.contains("is-self") ||
        e.target.type === "checkbox" ||
        e.target.tagName === "A"
      )
        return;
      const checkbox = this.querySelector(".row-checkbox");
      if (checkbox) {
        checkbox.checked = !checkbox.checked;
        this.classList.toggle("table-selected", checkbox.checked);
        const countDisplay = document.getElementById("selected-count-display");
        if (countDisplay)
          countDisplay.innerText = document.querySelectorAll(
            ".row-checkbox:checked",
          ).length;
      }
    });
  });

  // パスワード表示切り替え
  const togglePassword = document.querySelector("#togglePassword");
  const passwordInput = document.querySelector('input[type="password"]');
  if (togglePassword && passwordInput) {
    togglePassword.addEventListener("click", function () {
      const type =
        passwordInput.getAttribute("type") === "password" ? "text" : "password";
      passwordInput.setAttribute("type", type);
      this.innerText = type === "password" ? "visibility_off" : "visibility";
      passwordInput.focus();
    });
  }

  // 画像プレビュー
  const iconInput = document.querySelector('input[type="file"]');
  if (iconInput) {
    iconInput.addEventListener("change", function (e) {
      const file = e.target.files[0];
      const previewImg = document.getElementById("img-preview");
      if (file && previewImg) {
        const reader = new FileReader();
        reader.onload = (event) => {
          previewImg.src = event.target.result;
        };
        reader.readAsDataURL(file);
      }
    });
  }
});

// --- チラつき防止 ---
(function () {
  if (localStorage.getItem("sidebarStatus") === "collapsed") {
    document.documentElement.classList.add("sidebar-collapsed-init"); // CSS側で初期状態を制御する場合
  }
})();
