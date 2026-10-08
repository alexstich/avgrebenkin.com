#!/usr/bin/env bash
# Один раз, со своей машины: готовит сервер и секреты для .github/workflows/deploy.yml.
#
#   HOST=<адрес сервера> bash .github/setup-deploy.sh
#
# Необязательные переменные:
#   U=admin                       пользователь на сервере
#   R=alexstich/avgrebenkin.com   репозиторий на GitHub
#   DOMAIN=avgrebenkin.com        по нему ищется корень сайта в конфиге nginx
#   ROOT=/var/www/...             корень сайта, если искать не надо
#
# Нужны ssh, ssh-copy-id и gh (gh auth login) на этой машине.
set -euo pipefail

HOST=${HOST:?укажи сервер: HOST=<адрес> bash .github/setup-deploy.sh}
U=${U:-admin}
R=${R:-alexstich/avgrebenkin.com}
DOMAIN=${DOMAIN:-avgrebenkin.com}
KEY=~/.ssh/avgrebenkin_ci

# 1. Отдельный ключ только для CI: его можно отозвать, не трогая свой.
[ -f "$KEY" ] || ssh-keygen -t ed25519 -N '' -C 'github-actions deploy avgrebenkin.com' -f "$KEY"
ssh-copy-id -i "$KEY.pub" "$U@$HOST"

# 2. Корень сайта — из блока server в конфиге nginx, где server_name содержит домен.
#    Конфиги nginx обычно читаются без sudo.
if [ -z "${ROOT:-}" ]; then
  ROOT=$(ssh "$U@$HOST" "cat /etc/nginx/nginx.conf /etc/nginx/conf.d/*.conf /etc/nginx/sites-enabled/* 2>/dev/null" |
    awk -v d="$DOMAIN" '
      /^[ \t]*server[ \t]*\{/ { if (hit && root) { print root; exit } hit=0; root="" }
      /^[ \t]*server_name/    { for (i=2; i<=NF; i++) { n=$i; sub(/;$/, "", n); if (n==d || n=="www." d) hit=1 } }
      /^[ \t]*root[ \t]/      { if (!root) { root=$2; sub(/;$/, "", root) } }
      END                     { if (hit && root) print root }' | head -n1)
fi
if [ -z "$ROOT" ]; then
  echo "Не нашёл корень сайта $DOMAIN в конфиге nginx. Запусти ещё раз с ROOT=/путь/к/сайту." >&2
  exit 1
fi
read -r -p "Корень сайта на сервере: $ROOT — верно? [y/N] " ok
[ "$ok" = y ] || [ "$ok" = Y ] || { echo "Запусти ещё раз с ROOT=/путь/к/сайту."; exit 1; }

# 3. На сервере должен быть rsync, а у пользователя — право писать в корень сайта.
ssh "$U@$HOST" "command -v rsync >/dev/null" || {
  echo "На сервере нет rsync. Поставь: ssh -t $U@$HOST 'sudo apt-get install -y rsync'" >&2
  exit 1
}
if ! ssh "$U@$HOST" "test -w '$ROOT'"; then
  read -r -p "$U не может писать в $ROOT. Сделать $U владельцем каталога (sudo chown -R)? [y/N] " ok
  [ "$ok" = y ] || [ "$ok" = Y ] || { echo "Без права записи выкладка не заработает."; exit 1; }
  ssh -t "$U@$HOST" "sudo chown -R '$U': '$ROOT' && sudo chmod -R a+rX '$ROOT'"
fi

# 4. Проверка тем же ключом, что получит CI: зайти и записать пробный файл.
ssh -i "$KEY" -o IdentitiesOnly=yes "$U@$HOST" "f='$ROOT/.deploy-check' && touch \"\$f\" && rm \"\$f\"" &&
  echo "Ключ CI заходит на сервер и пишет в $ROOT."

# 5. Секреты репозитория.
gh secret set DEPLOY_HOST -R "$R" -b "$HOST"
gh secret set DEPLOY_USER -R "$R" -b "$U"
gh secret set DEPLOY_PATH -R "$R" -b "$ROOT"
gh secret set DEPLOY_SSH_KEY -R "$R" < "$KEY"
ssh-keyscan -t ed25519 "$HOST" 2>/dev/null | gh secret set DEPLOY_KNOWN_HOSTS -R "$R"

echo
echo "Готово. Первая выкладка: gh workflow run deploy.yml -R $R && gh run watch -R $R"
