#!/bin/bash
# =====================================================
#  update_from_upstream.sh
#  Private reponu upstream (orijinal repo) ile senkronize eder.
# =====================================================

set -e  # Hata olursa scripti durdur
set -o pipefail

# 🔧 Ayarlar
UPSTREAM_NAME="upstream"
BRANCH_NAME="main"

# ✅ 1. Remote'ları kontrol et
echo "🔍 Remote'lar kontrol ediliyor..."
if ! git remote | grep -q "$UPSTREAM_NAME"; then
  echo "⚠️  'upstream' remote tanımlı değil."
  echo "ℹ️  Eklemek için:"
  echo "    git remote add upstream https://github.com/tuncagurkan/raspberrypi-baby-monitor-marsel.git"
  exit 1
fi

# ✅ 2. Güncellemeleri fetch et
echo "⬇️  Upstream'den son değişiklikler çekiliyor..."
git fetch "$UPSTREAM_NAME"

# ✅ 3. Main branch'e geç
echo "🔁 '$BRANCH_NAME' branch'ine geçiliyor..."
git checkout "$BRANCH_NAME"

# ✅ 4. Güncellemeleri merge et
echo "🔗 Upstream değişiklikleri merge ediliyor..."
git merge "$UPSTREAM_NAME/$BRANCH_NAME" --no-edit

# ✅ 5. Private repoya push et
echo "🚀 Değişiklikler origin'e push ediliyor..."
git push origin "$BRANCH_NAME"

echo "✅ Güncelleme tamamlandı!"
