/**
 * EngageUp 共通JavaScriptプログラム
 *
 * 1. コアシステム機能（サイドバー・テーマ・フォント）
 * 2. 画面初期化処理
 * 3. フォーム演出・バリデーション（モーダル連動）
 * 4. 特定コンポーネント（パスワード表示・画像プレビュー）
 */

// ==========================================================
// 1. コアシステム機能
// ==========================================================

/**
 * サイドバーの開閉切り替えと状態保存
 */
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

/**
 * カラーテーマの切り替え
 */
function setTheme(themeName) {
  const currentMode = document.body.classList.contains("mode-dark")
    ? "mode-dark"
    : "mode-light";
  document.body.className = `${themeName} ${currentMode}`;
  localStorage.setItem("selectedTheme", themeName);
}

/**
 * ライト/ダークモードの切り替え
 */
function setMode(modeName) {
  const currentTheme =
    Array.from(document.body.classList).find((c) => c.startsWith("theme-")) ||
    "theme-green";
  document.body.className = `${currentTheme} ${modeName}`;
  localStorage.setItem("selectedMode", modeName);

  // カスタマイズメニュー内のボタンの状態を更新
  document
    .querySelectorAll(".mode-btn")
    .forEach((btn) => btn.classList.remove("active"));
  const targetBtn = document.getElementById(`btn-${modeName.split("-")[1]}`);
  if (targetBtn) targetBtn.classList.add("active");
}

/**
 * フォントサイズの調節
 */
function setFontSize(size) {
  document.documentElement.style.fontSize = size + "%";
  const valLabel = document.getElementById("font-size-val");
  if (valLabel) valLabel.innerText = size + "%";
  localStorage.setItem("selectedFontSize", size);
}

/**
 * 今日の日付表示を更新 (YYYY.MM.DD)
 */
function updateCurrentDate() {
  const dateSpan = document.getElementById("current-date");
  if (dateSpan) {
    const now = new Date();
    dateSpan.textContent = `${now.getFullYear()}.${String(now.getMonth() + 1).padStart(2, "0")}.${String(now.getDate()).padStart(2, "0")}`;
  }
}

// ==========================================================
// 2. 画面初期化処理 (DOMContentLoaded)
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

  // スライダーの位置を復元
  const sizeRange = document.getElementById("fontSizeRange");
  if (sizeRange) sizeRange.value = savedFontSize;

  // サイドバー状態の復元
  if (layout && savedSidebar === "collapsed") {
    layout.classList.add("sidebar-collapsed");
    if (icon) icon.innerText = "chevron_right";
  }

  // ==========================================================
  // 3. フォーム演出・リスト操作
  // ==========================================================

  // モーダルの準備
  const statusModalEl = document.getElementById("statusModal");
  const alertModalEl = document.getElementById("alertModal");
  const statusModal = statusModalEl ? new bootstrap.Modal(statusModalEl) : null;
  const alertModal = alertModalEl ? new bootstrap.Modal(alertModalEl) : null;

  /**
   * テーブル行クリックでのチェックボックス選択
   */
  const rows = document.querySelectorAll(".user-row");
  rows.forEach((row) => {
    row.addEventListener("click", function (e) {
      // 自分のアカウント(is-self)やチェックボックス自体、リンクへのクリックは除外
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
        // 選択人数表示があれば更新
        const countDisplay = document.getElementById("selected-count-display");
        if (countDisplay) {
          countDisplay.innerText = document.querySelectorAll(
            ".row-checkbox:checked",
          ).length;
        }
      }
    });
  });

  /**
   * 共通：ボタン押下後のローディング演出
   * 対象：一括削除/復元、定数更新、ランク更新、ユーザー作成
   */
  const setupFormSubmission = (triggerId, formId, validationFn) => {
    const trigger = document.getElementById(triggerId);
    const form = document.getElementById(formId);
    if (!trigger || !form) return;

    trigger.addEventListener("click", function () {
      // バリデーションチェックが必要な場合
      if (validationFn && !validationFn()) return;

      if (statusModal) {
        // 削除・復元などの場合はdata属性からメッセージを取得
        const msg = trigger.dataset.msg;
        const loadingText = document.getElementById("loading-text");
        if (msg && loadingText) loadingText.innerText = msg;

        // 削除・復元アクションのhidden値をセット
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

  // 1. ユーザー一覧画面（削除・復元）
  document.querySelectorAll(".action-trigger").forEach((btn) => {
    setupFormSubmission(btn.id, "user-bulk-form", () => {
      const checkedCount = document.querySelectorAll(
        ".row-checkbox:checked",
      ).length;
      if (checkedCount === 0) {
        if (alertModal) {
          document.getElementById("alert-modal-msg").innerText =
            "操作するユーザーを選択してください。";
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
  setupFormSubmission("save-trigger", "constant-update-form");

  // 3. ランク変更画面
  setupFormSubmission("submit-trigger", "rank-update-form", () => {
    const checkedCount = document.querySelectorAll(
      ".row-checkbox:checked",
    ).length;
    const rankSelected = document.querySelector('input[name="rank"]:checked');
    if (checkedCount === 0 || !rankSelected) {
      alert("対象ユーザーと変更後のランクを選択してください。");
      return false;
    }
    return true;
  });

  // 4. アカウント作成画面
  setupFormSubmission("submit-btn", "create-user-form");

  // ==========================================================
  // 4. 特定コンポーネント機能
  // ==========================================================

  /**
   * パスワードの表示/非表示切り替え
   */
  const togglePassword = document.querySelector("#togglePassword");
  const passwordInput = document.querySelector('input[type="password"]');
  if (togglePassword && passwordInput) {
    togglePassword.addEventListener("click", function () {
      const isPassword = passwordInput.getAttribute("type") === "password";
      passwordInput.setAttribute("type", isPassword ? "text" : "password");
      this.innerText = isPassword ? "visibility" : "visibility_off";
      passwordInput.focus();
    });
  }

  /**
   * ファイルアップロード時の画像プレビュー
   */
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

// --- チラつき防止 (DOM構築直後に実行) ---
(function () {
  if (localStorage.getItem("sidebarStatus") === "collapsed") {
    const layout = document.getElementById("adminLayout");
    if (layout) layout.classList.add("sidebar-collapsed");
  }
})();
