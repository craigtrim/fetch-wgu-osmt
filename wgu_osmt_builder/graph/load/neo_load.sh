#!/usr/bin/env bash
# neo_load.sh — load constraints, nodes, and relationships into Neo4j Aura
# Prints clean progress and delegates final stats rendering to ../build/stats.py
set -euo pipefail

# ---------------- colors + icons ----------------
RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; YELLOW=$'\033[0;33m'
BLUE=$'\033[0;34m'; CYAN=$'\033[0;36m'; BOLD=$'\033[1m'; NC=$'\033[0m'
ok="${GREEN}✅${NC}"; info="${CYAN}ℹ️${NC}"; ask="${YELLOW}❓${NC}"
brick="🧱"; link="🔗"; puzzle="🧩"

color() { printf "%s%s%s" "${1}" "${2}" "${NC}"; }

# ---------------- locate self and inputs ----------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOAD_DIR="$SCRIPT_DIR"
BUILD_DIR="$(cd "$SCRIPT_DIR/../build" && pwd)"
STATS="$BUILD_DIR/stats.py"

# ---------------- cypher-shell check ----------------
if ! command -v cypher-shell >/dev/null 2>&1; then
  echo "${RED}error:${NC} cypher-shell not found. Install with: ${BOLD}brew install neo4j${NC}" >&2
  exit 1
fi

# ---------------- python/poetry selection ----------------
PYTHON_CMD="python3"
if command -v poetry >/dev/null 2>&1; then
  PYTHON_CMD="poetry run python3"
fi

# ---------------- required env ----------------
: "${wgu_osmt_skills_builder_uri:?missing neo4j URI env var}"
: "${wgu_osmt_skills_builder_db:?missing neo4j DB name env var}"
: "${wgu_osmt_skills_builder_user:?missing neo4j user env var}"

read -r -s -p "$(color "$BLUE" "🔐  Neo4j password for ${wgu_osmt_skills_builder_user}: ")" NEO_PW
echo
export NEO_PW

# ---------------- file checks ----------------
need_file() {
  local p="$1"
  [[ -f "$p" ]] || { echo "${RED}error:${NC} required file not found: ${p}" >&2; exit 1; }
}
need_file "$LOAD_DIR/constraints.cypher"
need_file "$LOAD_DIR/load_nodes.cypher"
need_file "$LOAD_DIR/load_rels.cypher"
need_file "$STATS"

echo -e "${info}  Using:"
printf "  %-10s = %s\n" "LOAD_DIR"  "$LOAD_DIR"
printf "  %-10s = %s\n" "BUILD_DIR" "$BUILD_DIR"
printf "  %-10s = %s\n" "URI"       "$wgu_osmt_skills_builder_uri"
printf "  %-10s = %s\n" "DB"        "$wgu_osmt_skills_builder_db"
printf "  %-10s = %s\n\n" "PY"       "$PYTHON_CMD"

confirm() {
  read -r -p "$1 " ans
  case "${ans:-N}" in y|Y) return 0 ;; *) return 1 ;; esac
}

run_cypher_file() {
  local file="$1"
  cypher-shell \
    -a "$wgu_osmt_skills_builder_uri" \
    -u "$wgu_osmt_skills_builder_user" \
    -p "$NEO_PW" \
    -d "$wgu_osmt_skills_builder_db" \
    -f "$file" \
    --format=plain \
    --wrap=false \
    --fail-fast >/dev/null
}

# ---------------- step 1: constraints ----------------
if confirm "${ask}  Apply constraints and indexes? [y/N]:"; then
  echo -e "${info}  ${puzzle} Constraints ..."
  run_cypher_file "$LOAD_DIR/constraints.cypher"
  echo -e "${ok} ${puzzle} Constraints complete"
else
  echo -e "${YELLOW}↷ Skipped constraints${NC}"
fi
echo

# ---------------- step 2: nodes ----------------
if confirm "${ask}  Load nodes CSVs? [y/N]:"; then
  echo -e "${info}  ${brick} Nodes ..."
  run_cypher_file "$LOAD_DIR/load_nodes.cypher"
  echo -e "${ok} ${brick} Nodes complete"
else
  echo -e "${YELLOW}↷ Skipped nodes${NC}"
fi
echo

# ---------------- step 3: relationships ----------------
if confirm "${ask}  Load relationship CSVs? [y/N]:"; then
  echo -e "${info}  ${link} Relationships ..."
  run_cypher_file "$LOAD_DIR/load_rels.cypher"
  echo -e "${ok} ${link} Relationships complete"
else
  echo -e "${YELLOW}↷ Skipped relationships${NC}"
fi
echo

# ---------------- stats (Python pretty tables via tabulate) ----------------
echo -e "${info}  Computing graph stats ..."
eval "$PYTHON_CMD \"$STATS\""

echo -e "\n${ok} All done"
