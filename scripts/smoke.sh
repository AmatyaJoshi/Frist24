#!/usr/bin/env sh
# Smoke test against a running API (default http://localhost:8000). Exercises every endpoint group.
# Usage: scripts/smoke.sh [API_URL]     (needs curl + python3)
set -eu
API="${1:-http://localhost:8000}"
PY="${PYTHON:-python3}"
j() { $PY -c "import sys,json; d=json.load(sys.stdin); print(eval(sys.argv[1]))" "$1"; }

echo "# health";        curl -sf "$API/health" | j "d['status']"
echo "# products";      PID=$(curl -sf "$API/products" | j "d[0]['id']"); echo "  first product: $PID"
echo "# components";    curl -sf "$API/products/$PID/components?limit=3" | j "len(d)"
echo "# sync";          curl -sf -X POST "$API/sync" -H 'X-Actor: smoke' | j "d.get('incidents',{}).get('opened','?')" ; curl -sf "$API/sync/status" | j "len(d)"
echo "# incidents";     IID=$(curl -sf "$API/incidents" | j "d[0]['id']"); curl -sf "$API/incidents" | j "[(i['sku'],i['cve_id'],i['next_stage']) for i in d]"
echo "# detail";        curl -sf "$API/incidents/$IID" | j "(d['cve_id'], len(d['components']), len(d['timeline']))"
echo "# template draft";RID=$(curl -sf -X POST "$API/incidents/$IID/reports/template?stage=early_warning&language=en" -H 'X-Actor: smoke' | j "d['id']"); echo "  report $RID"
echo "# get report";    curl -sf "$API/reports/$RID" | j "d['status']"
echo "# edit FACT (expect 422)"; curl -s -o /dev/null -w '  %{http_code}\n' -X PATCH "$API/reports/$RID" -H 'Content-Type: application/json' -d '{"content":{"vulnerability_id":"CVE-1999-0001"}}'
echo "# edit TEXT";     curl -sf -X PATCH "$API/reports/$RID" -H 'Content-Type: application/json' -H 'X-Actor: smoke' -d '{"content":{"member_states_affected":"DE, AT"},"note":"smoke"}' | j "d['content']['member_states_affected']"
echo "# reject";        curl -sf -X POST "$API/reports/$RID/reject" -H 'Content-Type: application/json' -d '{"note":"smoke reject"}' | j "d['status']"
echo "# approve new";   RID2=$(curl -sf -X POST "$API/incidents/$IID/reports/template?stage=early_warning&language=de" | j "d['id']"); curl -sf -X POST "$API/reports/$RID2/approve" -H 'Content-Type: application/json' -H 'X-Actor: smoke' -d '{"note":"ok"}' | j "d['status']"
echo "# audit";         curl -sf "$API/audit?limit=3" | j "(d['total'], [i['action'] for i in d['items']])"
echo "# verify";        curl -sf "$API/audit/verify" | j "(d['ok'], d['rows'])"
echo "# openapi";       curl -sf "$API/openapi.json" | j "len(d['paths'])"
echo "SMOKE OK"
