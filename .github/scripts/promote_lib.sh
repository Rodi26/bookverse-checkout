#!/usr/bin/env bash

# Helper library for AppTrust promotion workflows (inventory-aligned, header-safe)

# Print basic HTTP request info
print_request_info() {
  local method="$1"; local url="$2"; local body="${3:-}"
  echo "---- HTTP Request ----"
  echo "Method: ${method}"
  echo "URL: ${url}"
  echo "Headers: Authorization: Bearer ***REDACTED***, Accept: application/json"
  if [[ "$method" == "POST" && -n "$body" ]]; then
    echo "Body: ${body}"
  fi
  echo "---------------------"
}

# Translate a display stage name (e.g., DEV) to API stage identifier
api_stage_for() {
  local s="${1:-}"
  if [[ "$s" == "PROD" ]]; then
    echo "PROD"
  elif [[ "$s" == "${PROJECT_KEY:-}-"* ]]; then
    echo "$s"
  else
    echo "${PROJECT_KEY:-}-$s"
  fi
}

# Resolve the exact API stage identifier for a given display name, preserving
# the original case/prefix as returned by the lifecycle API when available.
# Falls back to api_stage_for() if no mapping is present.
resolve_api_stage_for_display() {
  local display_name="${1:-}"
  local var_name="STAGE_${display_name}_ORIG"
  local mapped_value
  # Expand indirection only if set
  mapped_value="${!var_name}"
  if [[ -n "$mapped_value" ]]; then
    echo "$mapped_value"
  else
    api_stage_for "$display_name"
  fi
}

# Normalize lifecycle stage names for display (strip project prefix)
display_stage_for() {
  local s="${1:-}"
  if [[ "$s" == "PROD" || "$s" == "${PROJECT_KEY:-}-PROD" ]]; then
    echo "PROD"
  elif [[ "$s" == "${PROJECT_KEY:-}-"* ]]; then
    echo "${s#${PROJECT_KEY:-}-}"
  else
    echo "$s"
  fi
}

_http_get_json() {
  local url="$1"; local out_file="$2"; local code
  print_request_info "GET" "$url"
  code=$(curl -sS -L -o "$out_file" -w "%{http_code}" \
    -H "Authorization: Bearer ${APPTRUST_ACCESS_TOKEN:-}" -H "Accept: application/json" "$url" 2>/dev/null || echo 000)
  echo "$code"
}

_http_post_json() {
  local url="$1"; local body_json="$2"; local out_file="$3"; local code
  print_request_info "POST" "$url" "$body_json"
  code=$(curl -sS -L -o "$out_file" -w "%{http_code}" -X POST \
    -H "Authorization: Bearer ${APPTRUST_ACCESS_TOKEN:-}" -H "Accept: application/json" -H "Content-Type: application/json" \
    -d "$body_json" "$url" 2>/dev/null || echo 000)
  echo "$code"
}

# Fetch and export CURRENT_STAGE and RELEASE_STATUS from the version content endpoint
fetch_summary() {
  local body
  body=$(mktemp)
  local code
  code=$(curl -sS -L -o "$body" -w "%{http_code}" \
    "${JFROG_URL}/apptrust/api/v1/applications/${APPLICATION_KEY}/versions/${APP_VERSION}/content" \
    -H "Authorization: Bearer ${APPTRUST_ACCESS_TOKEN}" \
    -H "Accept: application/json" || echo 000)
  if [[ "$code" -ge 200 && "$code" -lt 300 ]]; then
    CURRENT_STAGE=$(jq -r '.current_stage // empty' "$body" 2>/dev/null || echo "")
    RELEASE_STATUS=$(jq -r '.release_status // empty' "$body" 2>/dev/null || echo "")
  else
    echo "❌ Failed to fetch version summary (HTTP $code)" >&2
    print_request_info "GET" "${JFROG_URL}/apptrust/api/v1/applications/${APPLICATION_KEY}/versions/${APP_VERSION}/content"
    cat "$body" || true
    rm -f "$body"
    return 1
  fi
  rm -f "$body"
  if [[ -n "${GITHUB_ENV:-}" ]]; then
    echo "CURRENT_STAGE=${CURRENT_STAGE:-}" >> "$GITHUB_ENV"
    echo "RELEASE_STATUS=${RELEASE_STATUS:-}" >> "$GITHUB_ENV"
  fi
  echo "🔎 Current stage: $(display_stage_for "${CURRENT_STAGE:-UNASSIGNED}") (release_status=${RELEASE_STATUS:-unknown})"
}

apptrust_post() {
  local path="${1:-}"; local data="${2:-}"; local out_file="${3:-}"
  local status
  status=$(curl -sS -L -o "$out_file" -w "%{http_code}" -X POST \
    "${JFROG_URL}${path}" \
    -H "Authorization: Bearer ${APPTRUST_ACCESS_TOKEN}" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" \
    -d "$data")
  echo "$status"
}

promote_to_stage() {
  local target_stage_display="${1:-}"
  local resp_body http_status
  resp_body=$(mktemp)
  local api_stage
  api_stage=$(resolve_api_stage_for_display "$target_stage_display")
  echo "🚀 Promoting to ${target_stage_display} via AppTrust"
  http_status=$(apptrust_post \
    "/apptrust/api/v1/applications/${APPLICATION_KEY}/versions/${APP_VERSION}/promote?async=false" \
    "{\"target_stage\": \"${api_stage}\", \"promotion_type\": \"move\"}" \
    "$resp_body")
  echo "HTTP $http_status"; cat "$resp_body" || true; echo
  rm -f "$resp_body"
  if [[ "$http_status" -lt 200 || "$http_status" -ge 300 ]]; then
    echo "❌ Promotion to ${target_stage_display} failed (HTTP $http_status)" >&2
    print_request_info "POST" "${JFROG_URL}/apptrust/api/v1/applications/${APPLICATION_KEY}/versions/${APP_VERSION}/promote?async=false" "{\"target_stage\": \"${api_stage}\", \"promotion_type\": \"move\"}"
    return 1
  fi
  PROMOTED_STAGES="${PROMOTED_STAGES:-}${PROMOTED_STAGES:+ }${target_stage_display}"
  echo "PROMOTED_STAGES=${PROMOTED_STAGES}" >> "${GITHUB_ENV:-/dev/null}"
  fetch_summary
}

# Release to final stage (PROD) with included repository keys inferred for checkout
release_version() {
  local resp_body http_status
  resp_body=$(mktemp)
  echo "🚀 Releasing to ${FINAL_STAGE} via AppTrust Release API"
  local payload
  if [[ -n "${RELEASE_INCLUDED_REPO_KEYS:-}" ]]; then
    payload=$(printf '{"promotion_type":"move","included_repository_keys":%s}' "${RELEASE_INCLUDED_REPO_KEYS}")
  else
    local service_name
    service_name="${APPLICATION_KEY#${PROJECT_KEY}-}"
    local repo_docker repo_generic
    repo_docker="${PROJECT_KEY}-${service_name}-internal-docker-release-local"
    repo_generic="${PROJECT_KEY}-${service_name}-internal-generic-release-local"
    payload=$(printf '{"promotion_type":"move","included_repository_keys":["%s","%s"]}' "$repo_docker" "$repo_generic")
  fi
  http_status=$(curl -sS -L -o "$resp_body" -w "%{http_code}" -X POST \
    "${JFROG_URL}/apptrust/api/v1/applications/${APPLICATION_KEY}/versions/${APP_VERSION}/release?async=false" \
    -H "Authorization: Bearer ${APPTRUST_ACCESS_TOKEN}" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" \
    -d "$payload")
  echo "HTTP $http_status"; cat "$resp_body" || true; echo
  if [[ "$http_status" -lt 200 || "$http_status" -ge 300 ]]; then
    echo "❌ Release to ${FINAL_STAGE} failed (HTTP $http_status)" >&2
    print_request_info "POST" "${JFROG_URL}/apptrust/api/v1/applications/${APPLICATION_KEY}/versions/${APP_VERSION}/release?async=false" "$payload"
    rm -f "$resp_body"
    return 1
  fi
  rm -f "$resp_body"
  DID_RELEASE=true
  echo "DID_RELEASE=${DID_RELEASE}" >> "${GITHUB_ENV:-/dev/null}"
  PROMOTED_STAGES="${PROMOTED_STAGES:-}${PROMOTED_STAGES:+ }${FINAL_STAGE}"
  echo "PROMOTED_STAGES=${PROMOTED_STAGES}" >> "${GITHUB_ENV:-/dev/null}"
  fetch_summary
}

emit_json() {
  local out_file="${1:-}"; shift
  local content="$*"
  printf "%b\n" "$content" > "$out_file"
}

evd_create() {
  local predicate_file="${1:-}"; local predicate_type="${2:-}"; local markdown_file="${3:-}"
  local md_args=()
  if [[ -n "$markdown_file" ]]; then md_args+=(--markdown "$markdown_file"); fi
  jf evd create-evidence \
    --predicate "$predicate_file" \
    "${md_args[@]}" \
    --predicate-type "$predicate_type" \
    --release-bundle "$APPLICATION_KEY" \
    --release-bundle-version "$APP_VERSION" \
    --project "${PROJECT_KEY:-}" \
    --provider-id github-actions \
    --key "${EVIDENCE_PRIVATE_KEY:-}" \
    --key-alias "${EVIDENCE_KEY_ALIAS:-${EVIDENCE_KEY_ALIAS_VAR:-}}" || true
}

attach_evidence_qa() {
  local now_ts scan_id med coll pass
  now_ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  scan_id=$(cat /proc/sys/kernel/random/uuid)
  med=$((2 + RANDOM % 5))
  emit_json dast-qa.json "{\n    \"environment\": \"QA\",\n    \"scanId\": \"${scan_id}\",\n    \"status\": \"PASSED\",\n    \"findings\": { \"critical\": 0, \"high\": 0, \"medium\": ${med} },\n    \"attachStage\": \"QA\", \"gateForPromotionTo\": \"STAGING\",\n    \"timestamp\": \"${now_ts}\"\n  }"
  printf "# dast-scan\n" > dast-scan.md
  evd_create dast-qa.json "https://invicti.com/evidence/dast/v3" dast-scan.md
  coll=$(cat /proc/sys/kernel/random/uuid)
  pass=$((100 + RANDOM % 31))
  emit_json postman-qa.json "{\n    \"environment\": \"QA\",\n    \"collectionId\": \"${coll}\",\n    \"status\": \"PASSED\",\n    \"assertionsPassed\": ${pass},\n    \"assertionsFailed\": 0,\n    \"attachStage\": \"QA\", \"gateForPromotionTo\": \"STAGING\",\n    \"timestamp\": \"${now_ts}\"\n  }"
  printf "# api-tests\n" > api-tests.md
  evd_create postman-qa.json "https://postman.com/evidence/collection/v2.2" api-tests.md
}

attach_evidence_staging() {
  :
}

attach_evidence_prod() {
  local now_ts rev short
  now_ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  rev="${GITHUB_SHA:-${GITHUB_SHA:-}}"; short=${rev:0:8}
  emit_json argocd-prod.json "{ \"tool\": \"ArgoCD\", \"status\": \"Synced\", \"revision\": \"${short}\", \"deployedAt\": \"${now_ts}\", \"attachStage\": \"PROD\" }"
  printf "# argocd-deploy\n" > argocd-deploy.md
  evd_create argocd-prod.json "https://argo.cd/ev/deploy/v1" argocd-deploy.md
}

attach_evidence_for() {
  local stage_name="${1:-}"
  case "$stage_name" in
    UNASSIGNED)
      echo "ℹ️ No evidence for UNASSIGNED" ;;
    DEV)
      echo "ℹ️ No evidence configured for DEV in demo" ;;
    QA)
      attach_evidence_qa ;;
    STAGING)
      attach_evidence_staging ;;
    PROD)
      attach_evidence_prod ;;
    *)
      echo "ℹ️ No evidence rule for stage '$stage_name'" ;;
  esac
}

# Compute the next stage and perform a single transition
advance_one_step() {
  local allow_release="${ALLOW_RELEASE:-false}"
  IFS=' ' read -r -a STAGES <<< "${STAGES_STR:-}"
  local current_index=-1
  local display_current
  display_current=$(display_stage_for "${CURRENT_STAGE:-}")
  if [[ -z "${CURRENT_STAGE:-}" || "${display_current}" == "UNASSIGNED" ]]; then
    current_index=-1
  else
    local i; for i in "${!STAGES[@]}"; do
      if [[ "${STAGES[$i]}" == "${display_current}" ]]; then current_index=$i; break; fi
    done
  fi
  local target_index=-1
  local j; for j in "${!STAGES[@]}"; do if [[ "${STAGES[$j]}" == "${TARGET_NAME}" ]]; then target_index=$j; break; fi; done
  if [[ "$target_index" -lt 0 ]]; then echo "❌ Target stage '${TARGET_NAME}' not found in lifecycle. Available: ${STAGES[*]}" >&2; return 1; fi
  if [[ "$current_index" -ge "$target_index" ]]; then echo "ℹ️ Current stage (${CURRENT_STAGE:-UNASSIGNED}) is at or beyond target (${TARGET_NAME}). Nothing to promote."; return 0; fi
  local next_index=$((current_index+1))
  if [[ "$next_index" -gt "$target_index" ]]; then echo "ℹ️ Next stage would exceed target (${TARGET_NAME}). Nothing to promote."; return 0; fi
  local next_stage_display="${STAGES[$next_index]}"
  if [[ "$next_stage_display" == "$FINAL_STAGE" ]]; then
    if [[ "$allow_release" == "true" ]]; then
      release_version || return 1
      attach_evidence_prod || true
    else
      echo "⏭️ Skipping release step (deferred to dedicated step)"
    fi
  else
    promote_to_stage "$next_stage_display" || return 1
    attach_evidence_for "$next_stage_display" || true
  fi
}

