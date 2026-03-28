# Release Script Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a `release.sh` script and CI workflow for building, versioning, and releasing skills to Claude Code and Codex marketplaces.

**Architecture:** A single bash script with three subcommands (build, bump, release) reads per-skill-group `version.json` files and generates a repo-root `marketplace.json` for Claude Code. A GitHub Actions workflow creates releases on tag push.

**Tech Stack:** Bash, jq (JSON manipulation), GitHub Actions

---

### Task 1: Create version.json files for each skill group

**Files:**
- Create: `skills/paper-to-course/version.json`
- Create: `skills/system-explorer/version.json`

- [ ] **Step 1: Create paper-to-course version.json**

```json
{
  "name": "paper-to-course",
  "version": "0.1.0",
  "description": "Turn research papers into interactive HTML courses"
}
```

- [ ] **Step 2: Create system-explorer version.json**

```json
{
  "name": "system-explorer",
  "version": "0.1.0",
  "description": "Explore and learn about software systems"
}
```

- [ ] **Step 3: Verify both files are valid JSON**

Run: `jq . skills/paper-to-course/version.json && jq . skills/system-explorer/version.json`
Expected: Both print formatted JSON without errors.

- [ ] **Step 4: Commit**

```bash
git add skills/paper-to-course/version.json skills/system-explorer/version.json
git commit -m "feat: add version.json for each skill group"
```

---

### Task 2: Create release.sh with `build` subcommand

**Files:**
- Create: `release.sh`

- [ ] **Step 1: Create release.sh with argument parsing and build command**

```bash
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
```

- [ ] **Step 2: Make executable**

Run: `chmod +x release.sh`

- [ ] **Step 3: Test build command with paper-to-course**

Run: `./release.sh build paper-to-course`
Expected output:
```
Building paper-to-course...
  version.json: 0.1.0
  skill: paper-to-course OK
  marketplace.json updated
Build OK
```

- [ ] **Step 4: Test build command with system-explorer**

Run: `./release.sh build system-explorer`
Expected output:
```
Building system-explorer...
  version.json: 0.1.0
  skill: system-analyzer OK
  skill: system-explorer OK
  skill: system-finder OK
  skill: system-to-course OK
  marketplace.json updated
Build OK
```

- [ ] **Step 5: Verify marketplace.json was generated correctly**

Run: `jq . marketplace.json`
Expected: Valid JSON with two plugins, each listing their skills, versions at 0.1.0.

- [ ] **Step 6: Commit**

```bash
git add release.sh
git commit -m "feat: add release.sh with build subcommand"
```

---

### Task 3: Add `bump` subcommand

**Files:**
- Modify: `release.sh`

- [ ] **Step 1: Add cmd_bump function to release.sh**

Add after the `cmd_build` function, before `# --- Main ---`:

```bash
# --- Bump ---

cmd_bump() {
  local group="$1"
  local level="$2"
  local vfile
  vfile="$(get_version_file "$group")"
  local current
  current="$(get_version "$group")"

  # Parse semver
  local major minor patch
  IFS='.' read -r major minor patch <<< "$current"

  case "$level" in
    major)
      major=$((major + 1))
      minor=0
      patch=0
      ;;
    minor)
      minor=$((minor + 1))
      patch=0
      ;;
    patch)
      patch=$((patch + 1))
      ;;
    *)
      echo "Error: level must be major, minor, or patch" >&2
      exit 1
      ;;
  esac

  local new_version="$major.$minor.$patch"

  # Update version.json
  local tmp
  tmp=$(mktemp)
  jq --arg v "$new_version" '.version = $v' "$vfile" > "$tmp" && mv "$tmp" "$vfile"

  echo "Bumped $group: $current -> $new_version"

  # Regenerate marketplace.json
  generate_marketplace
  echo "marketplace.json updated"

  # Commit
  git add "$vfile" "$MARKETPLACE_JSON"
  git commit -m "chore($group): bump version to $new_version"
}
```

- [ ] **Step 2: Update the case statement to wire up bump**

Replace the `bump|release)` case with:

```bash
  bump)
    if [ $# -lt 1 ]; then
      echo "Error: bump requires a level (major, minor, patch)" >&2
      exit 1
    fi
    cmd_bump "$GROUP" "$1"
    ;;
  release)
    echo "Error: 'release' not yet implemented" >&2
    exit 1
    ;;
```

- [ ] **Step 3: Test bump patch**

Run: `./release.sh bump paper-to-course patch`
Expected:
```
Bumped paper-to-course: 0.1.0 -> 0.1.1
marketplace.json updated
```

- [ ] **Step 4: Verify version.json was updated**

Run: `jq .version skills/paper-to-course/version.json`
Expected: `"0.1.1"`

- [ ] **Step 5: Verify marketplace.json has the new version**

Run: `jq '.plugins[] | select(.name=="paper-to-course") | .version' marketplace.json`
Expected: `"0.1.1"`

- [ ] **Step 6: Verify a commit was created**

Run: `git log --oneline -1`
Expected: `chore(paper-to-course): bump version to 0.1.1`

- [ ] **Step 7: Reset the bump for now (we want to stay at 0.1.0)**

Run: `git reset --hard HEAD~1`

- [ ] **Step 8: Commit release.sh with bump subcommand**

```bash
git add release.sh
git commit -m "feat: add bump subcommand to release.sh"
```

---

### Task 4: Add `release` subcommand

**Files:**
- Modify: `release.sh`

- [ ] **Step 1: Add cmd_release function to release.sh**

Add after `cmd_bump`, before `# --- Main ---`:

```bash
# --- Release ---

cmd_release() {
  local group="$1"

  # Validate first
  cmd_build "$group"

  local version
  version="$(get_version "$group")"
  local tag="$group/v$version"

  # Check tag doesn't already exist
  if git rev-parse "$tag" >/dev/null 2>&1; then
    echo "Error: tag $tag already exists" >&2
    exit 1
  fi

  # Create and push tag
  git tag "$tag"
  echo ""
  echo "Created tag: $tag"
  echo ""
  echo "To publish this release, push the tag:"
  echo "  git push origin $tag"
  echo ""
  echo "This will trigger the CI workflow to create a GitHub Release."
}
```

- [ ] **Step 2: Update the case statement to wire up release**

Replace the `release)` case with:

```bash
  release)
    cmd_release "$GROUP"
    ;;
```

- [ ] **Step 3: Test release command**

Run: `./release.sh release paper-to-course`
Expected:
```
Building paper-to-course...
  version.json: 0.1.0
  skill: paper-to-course OK
  marketplace.json updated
Build OK

Created tag: paper-to-course/v0.1.0

To publish this release, push the tag:
  git push origin paper-to-course/v0.1.0

This will trigger the CI workflow to create a GitHub Release.
```

- [ ] **Step 4: Verify the tag was created**

Run: `git tag -l 'paper-to-course/*'`
Expected: `paper-to-course/v0.1.0`

- [ ] **Step 5: Delete the test tag (we don't want to release yet)**

Run: `git tag -d paper-to-course/v0.1.0`

- [ ] **Step 6: Commit**

```bash
git add release.sh
git commit -m "feat: add release subcommand to release.sh"
```

---

### Task 5: Create GitHub Actions release workflow

**Files:**
- Create: `.github/workflows/release.yml`

- [ ] **Step 1: Create the workflow file**

```yaml
name: Create Release

on:
  push:
    tags:
      - '*/v*'

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Parse tag
        id: parse
        run: |
          TAG="${GITHUB_REF#refs/tags/}"
          GROUP="${TAG%%/v*}"
          VERSION="${TAG#*/v}"
          echo "tag=$TAG" >> "$GITHUB_OUTPUT"
          echo "group=$GROUP" >> "$GITHUB_OUTPUT"
          echo "version=$VERSION" >> "$GITHUB_OUTPUT"
          echo "Releasing $GROUP v$VERSION"

      - name: Install jq
        run: sudo apt-get install -y jq

      - name: Validate build
        run: ./release.sh build "${{ steps.parse.outputs.group }}"

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          tag_name: ${{ steps.parse.outputs.tag }}
          name: "${{ steps.parse.outputs.group }} v${{ steps.parse.outputs.version }}"
          generate_release_notes: true
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "feat: add GitHub Actions release workflow"
```

---

### Task 6: Generate initial marketplace.json and final verification

**Files:**
- Create: `marketplace.json` (generated by build)

- [ ] **Step 1: Run build for both skill groups to generate marketplace.json**

Run: `./release.sh build paper-to-course && ./release.sh build system-explorer`
Expected: Both succeed, marketplace.json exists at repo root.

- [ ] **Step 2: Verify marketplace.json content**

Run: `jq . marketplace.json`
Expected: JSON with two plugins (paper-to-course and system-explorer), both at version 0.1.0, with correct skill paths.

- [ ] **Step 3: Test full cycle — bump and release (dry run)**

Run:
```bash
./release.sh bump paper-to-course patch
./release.sh release paper-to-course
```
Expected: Bumps to 0.1.1, creates tag `paper-to-course/v0.1.1`.

- [ ] **Step 4: Clean up test artifacts**

Run:
```bash
git tag -d paper-to-course/v0.1.1
git reset --hard HEAD~1
```

- [ ] **Step 5: Commit the generated marketplace.json**

```bash
git add marketplace.json
git commit -m "feat: add generated marketplace.json for plugin discovery"
```

- [ ] **Step 6: Verify everything is clean**

Run: `git status`
Expected: Clean working tree, no untracked files.
