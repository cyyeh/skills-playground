#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$REPO_ROOT/skills"
MARKETPLACE_JSON="$REPO_ROOT/marketplace.json"

usage() {
  cat <<EOF
Usage: $0 <command> <skill-group> [args]

Commands:
  build   <skill-group>                 Validate and generate marketplace.json
  bump    <skill-group> <major|minor|patch>  Bump version
  release <skill-group>                 Tag and push release

Skill groups:
EOF
  for dir in "$SKILLS_DIR"/*/; do
    if [ -f "$dir/version.json" ]; then
      echo "  $(basename "$dir")"
    fi
  done
  exit 1
}

# --- Helpers ---

get_version_file() {
  local group="$1"
  local vfile="$SKILLS_DIR/$group/version.json"
  if [ ! -f "$vfile" ]; then
    echo "Error: $vfile not found" >&2
    exit 1
  fi
  echo "$vfile"
}

get_version() {
  local vfile
  vfile="$(get_version_file "$1")"
  jq -r '.version' "$vfile"
}

get_field() {
  local vfile
  vfile="$(get_version_file "$1")"
  jq -r ".$2" "$vfile"
}

# --- Build ---

cmd_build() {
  local group="$1"
  local group_dir="$SKILLS_DIR/$group"
  local errors=0

  echo "Building $group..."

  # Validate version.json exists
  local vfile
  vfile="$(get_version_file "$group")"
  echo "  version.json: $(get_version "$group")"

  # Validate every subdirectory that isn't examples/ has a SKILL.md
  local skills=()
  for subdir in "$group_dir"/*/; do
    local dirname
    dirname="$(basename "$subdir")"
    if [ "$dirname" = "examples" ]; then
      continue
    fi
    if [ ! -f "$subdir/SKILL.md" ]; then
      echo "  ERROR: $subdir is missing SKILL.md" >&2
      errors=$((errors + 1))
    else
      echo "  skill: $dirname OK"
      skills+=("./skills/$group/$dirname")
    fi
  done

  if [ ${#skills[@]} -eq 0 ]; then
    echo "  ERROR: no skills found in $group_dir" >&2
    exit 1
  fi

  if [ $errors -gt 0 ]; then
    echo "Build failed with $errors error(s)" >&2
    exit 1
  fi

  # Generate marketplace.json
  generate_marketplace
  echo "  marketplace.json updated"
  echo "Build OK"
}

generate_marketplace() {
  local plugins="[]"

  for group_dir in "$SKILLS_DIR"/*/; do
    local group
    group="$(basename "$group_dir")"
    local vfile="$group_dir/version.json"
    if [ ! -f "$vfile" ]; then
      continue
    fi

    local name description version
    name="$(jq -r '.name' "$vfile")"
    description="$(jq -r '.description' "$vfile")"
    version="$(jq -r '.version' "$vfile")"

    # Collect skill paths (subdirs with SKILL.md, excluding examples/)
    local skill_paths="[]"
    for subdir in "$group_dir"/*/; do
      local dirname
      dirname="$(basename "$subdir")"
      if [ "$dirname" = "examples" ]; then
        continue
      fi
      if [ -f "$subdir/SKILL.md" ]; then
        skill_paths=$(echo "$skill_paths" | jq --arg p "./skills/$group/$dirname" '. + [$p]')
      fi
    done

    local plugin
    plugin=$(jq -n \
      --arg name "$name" \
      --arg desc "$description" \
      --arg ver "$version" \
      --arg src "./skills/$group/" \
      --argjson skills "$skill_paths" \
      '{name: $name, description: $desc, version: $ver, source: $src, strict: false, skills: $skills}')

    plugins=$(echo "$plugins" | jq --argjson p "$plugin" '. + [$p]')
  done

  jq -n \
    --argjson plugins "$plugins" \
    '{
      name: "skills-playground",
      owner: { name: "cyyeh" },
      metadata: { description: "Custom skills for Claude Code and Codex" },
      plugins: $plugins
    }' > "$MARKETPLACE_JSON"
}

# --- Main ---

if [ $# -lt 2 ]; then
  usage
fi

COMMAND="$1"
GROUP="$2"
shift 2

case "$COMMAND" in
  build)
    cmd_build "$GROUP"
    ;;
  bump|release)
    echo "Error: '$COMMAND' not yet implemented" >&2
    exit 1
    ;;
  *)
    usage
    ;;
esac
