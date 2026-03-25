#!/bin/sh
set -e
KIBANA_URL="${KIBANA_URL:-http://kibana:5601}"
DIR="$(dirname "$0")"

echo "Waiting for Kibana at ${KIBANA_URL}..."
i=0
while [ "$i" -lt 90 ]; do
  if curl -sf "${KIBANA_URL}/api/status" >/dev/null 2>&1; then
    echo "Kibana is up."
    break
  fi
  i=$((i + 1))
  sleep 2
done
if ! curl -sf "${KIBANA_URL}/api/status" >/dev/null 2>&1; then
  echo "Kibana did not become ready in time." >&2
  exit 1
fi

sleep 3

post_so() {
  type="$1"
  id="$2"
  file="$3"
  code="$(curl -sS -o /tmp/kibana_resp.txt -w "%{http_code}" -X POST \
    "${KIBANA_URL}/api/saved_objects/${type}/${id}?overwrite=true" \
    -H "kbn-xsrf: true" \
    -H "Content-Type: application/json" \
    --data-binary "@${file}")"
  if [ "$code" != "200" ] && [ "$code" != "409" ]; then
    echo "POST ${type}/${id} failed: HTTP ${code}" >&2
    cat /tmp/kibana_resp.txt >&2
    exit 1
  fi
}

post_so "index-pattern" "positions-dataview" "${DIR}/saved_objects/01-index-pattern.json"
post_so "visualization" "positions-histogram" "${DIR}/saved_objects/02-visualization-histogram.json"
post_so "search" "positions-saved-search" "${DIR}/saved_objects/03-saved-search.json"
post_so "dashboard" "positions-dashboard" "${DIR}/saved_objects/04-dashboard.json"

echo "Kibana saved objects imported (Positions — overview)."
