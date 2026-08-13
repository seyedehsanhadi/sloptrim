#!/usr/bin/env bash
# Smoke tests for the plugin hook layer: synthetic hook payloads in, output shape and flag-file state checked.
set -u
topath() { if command -v cygpath >/dev/null 2>&1; then cygpath -m "$1"; else echo "$1"; fi; }
REPO="$(topath "$(cd "$(dirname "$0")/.." && pwd)")"
export CLAUDE_CONFIG_DIR="$(topath "$(mktemp -d)")"
export CLAUDE_PLUGIN_ROOT="$REPO"
FLAG="$CLAUDE_CONFIG_DIR/.sloptrim-active"
PASS=0
FAIL=0

check() {
  if [ "$2" -eq 0 ]; then PASS=$((PASS+1)); echo "PASS  $1"; else FAIL=$((FAIL+1)); echo "FAIL  $1"; fi
}

out="$(echo '{}' | node "$REPO/hooks/sloptrim-activate.js")"
echo "$out" | grep -q "SLOPTRIM ACTIVE - level: full"; check "activate emits full contract by default" $?
echo "$out" | grep -q "PROSE DELIVERABLES ONLY"; check "contract scopes to prose deliverables" $?
echo "$out" | grep -q "detect.py"; check "full contract includes detect.py step" $?
[ "$(cat "$FLAG")" = "full" ]; check "activate persists flag" $?

echo off > "$FLAG"
out="$(echo '{}' | node "$REPO/hooks/sloptrim-activate.js")"
[ -z "$out" ]; check "activate silent when off" $?

echo lite > "$FLAG"
out="$(echo '{}' | node "$REPO/hooks/sloptrim-activate.js")"
echo "$out" | grep -q "level: lite"; check "activate respects lite" $?
! echo "$out" | grep -q "detect.py"; check "lite contract has no detector step" $?

out="$(echo '{"prompt":"/sloptrim strict"}' | node "$REPO/hooks/sloptrim-tracker.js")"
echo "$out" | grep -q '"decision":"block"'; check "tracker blocks mode command" $?
[ "$(cat "$FLAG")" = "strict" ]; check "tracker writes strict flag" $?

out="$(echo '{"prompt":"hello there"}' | node "$REPO/hooks/sloptrim-tracker.js")"
echo "$out" | grep -q "SLOPTRIM ACTIVE (strict)"; check "tracker emits per-turn reminder" $?
echo "$out" | grep -q "UserPromptSubmit"; check "reminder uses hookSpecificOutput" $?
out="$(echo '{"prompt":"refactor the auth module and write me a haiku"}' | node "$REPO/hooks/sloptrim-tracker.js")"
! echo "$out" | grep -q '"decision":"block"'; check "tracker never blocks an ordinary prompt" $?

echo '{"prompt":"/sloptrim off"}' | node "$REPO/hooks/sloptrim-tracker.js" > /dev/null
out="$(echo '{"prompt":"hello"}' | node "$REPO/hooks/sloptrim-tracker.js")"
[ -z "$out" ]; check "tracker silent when off" $?

echo full > "$FLAG"
SLOP="$CLAUDE_CONFIG_DIR/slop.md"
cat > "$SLOP" <<'EOF'
Great question! In today's fast-paced world, our comprehensive guide serves as a testament to the transformative power of leveraging cutting-edge solutions. It's not just about tools; it's about unlocking unprecedented value. It is worth noting that experts argue this journey is just beginning, paving the way for a brighter future. In conclusion, the future looks bright. I hope this helps!
EOF
out="$(printf '{"tool_name":"Write","tool_input":{"file_path":"%s"}}' "$SLOP" | node "$REPO/hooks/sloptrim-guard.js")"
echo "$out" | grep -qE "sloptrim: slop.md reads .*\(score [0-9]"; check "guard nudges on slop file" $?
echo "$out" | grep -q "PostToolUse"; check "guard uses hookSpecificOutput" $?

CLEAN="$CLAUDE_CONFIG_DIR/clean.md"
cat > "$CLEAN" <<'EOF'
The parser reads one token at a time. If it sees an opening brace it pushes a new scope onto the stack. Closing braces pop it. Errors bubble up as exceptions, which the caller catches and reports with a line number. Most failures in practice come from unterminated strings.
EOF
out="$(printf '{"tool_name":"Write","tool_input":{"file_path":"%s"}}' "$CLEAN" | node "$REPO/hooks/sloptrim-guard.js")"
[ -z "$out" ]; check "guard silent on clean file" $?

out="$(printf '{"tool_name":"Write","tool_input":{"file_path":"%s"}}' "$REPO/scripts/detect.py" | node "$REPO/hooks/sloptrim-guard.js")"
[ -z "$out" ]; check "guard ignores .py files" $?

echo lite > "$FLAG"
out="$(printf '{"tool_name":"Write","tool_input":{"file_path":"%s"}}' "$SLOP" | node "$REPO/hooks/sloptrim-guard.js")"
[ -z "$out" ]; check "guard disabled in lite mode" $?

echo full > "$FLAG"
a="$(echo '{}' | node "$REPO/hooks/sloptrim-activate.js")"
b="$(echo '{}' | node "$REPO/hooks/sloptrim-activate.js")"
[ "$a" = "$b" ]; check "contract byte-stable across sessions" $?

echo full > "$FLAG"
SLOPTX="In today's fast-paced world, leveraging robust synergy to foster transformative outcomes as a valuable asset."
covered=1
for e in md markdown txt text rst tex org adoc; do
  f="$CLAUDE_CONFIG_DIR/deliv.$e"; printf '%s\n' "$SLOPTX" > "$f"
  out="$(printf '{"tool_name":"Write","tool_input":{"file_path":"%s"}}' "$f" | node "$REPO/hooks/sloptrim-guard.js")"
  echo "$out" | grep -q "(score " || covered=0
done
[ "$covered" -eq 1 ]; check "guard scores all prose deliverable formats" $?
silent=1
for e in docx pdf py js json; do
  f="$CLAUDE_CONFIG_DIR/deliv.$e"; printf '%s\n' "$SLOPTX" > "$f"
  out="$(printf '{"tool_name":"Write","tool_input":{"file_path":"%s"}}' "$f" | node "$REPO/hooks/sloptrim-guard.js")"
  [ -n "$out" ] && silent=0
done
[ "$silent" -eq 1 ]; check "guard silent on binary (.docx/.pdf) and code" $?

echo full > "$FLAG"
out="$(echo '{"prompt":"/sloptrim show"}' | node "$REPO/hooks/sloptrim-tracker.js")"
echo "$out" | grep -q "prose delivered this session"; check "show lists scored deliverables" $?
echo "$out" | grep -q "reads "; check "show uses plain-language verdict" $?
echo "$out" | grep -q "binary"; check "show surfaces binary (.docx) deliverables" $?

before="$(cat "$CLAUDE_CONFIG_DIR/.sloptrim-ledger.json")"
printf '{"tool_input":{"file_path":"%s"}}' "$CLAUDE_CONFIG_DIR/node_modules/pkg/readme.docx" | node "$REPO/hooks/sloptrim-guard.js" >/dev/null
[ "$(cat "$CLAUDE_CONFIG_DIR/.sloptrim-ledger.json")" = "$before" ]; check "guard does not log binaries under machine paths" $?

printf '{"session_id":"sess-a","tool_input":{"file_path":"%s"}}' "$SLOP" | node "$REPO/hooks/sloptrim-guard.js" >/dev/null
out="$(echo '{"session_id":"sess-a","prompt":"/sloptrim show"}' | node "$REPO/hooks/sloptrim-tracker.js")"
echo "$out" | grep -q "slop.md"; check "show reads its own session's ledger" $?
out="$(echo '{"session_id":"sess-b","prompt":"/sloptrim show"}' | node "$REPO/hooks/sloptrim-tracker.js")"
echo "$out" | grep -q "nothing scored yet"; check "another session sees an empty ledger" $?
echo '{"source":"startup"}' | node "$REPO/hooks/sloptrim-activate.js" >/dev/null
out="$(echo '{"session_id":"sess-a","prompt":"/sloptrim show"}' | node "$REPO/hooks/sloptrim-tracker.js")"
echo "$out" | grep -q "slop.md"; check "another window's startup does not wipe a live ledger" $?
OLD="$CLAUDE_CONFIG_DIR/.sloptrim-ledger-stale.json"; echo '[]' > "$OLD"
touch -d "8 days ago" "$OLD" 2>/dev/null || touch -t "$(date -d '8 days ago' +%Y%m%d%H%M 2>/dev/null || echo 202601010000)" "$OLD"
echo '{"source":"startup"}' | node "$REPO/hooks/sloptrim-activate.js" >/dev/null
[ ! -f "$OLD" ]; check "startup sweeps week-old ledger files" $?

echo full > "$FLAG"
out="$(echo '{"prompt":"/sloptrim"}' | node "$REPO/hooks/sloptrim-tracker.js")"
echo "$out" | grep -q "Level now: full"; check "bare /sloptrim shows menu with live level" $?
echo "$out" | grep -q "doctor"; check "bare menu lists every command" $?

echo full > "$FLAG"
out="$(echo '{"prompt":"/sloptrim:sloptrim strict"}' | node "$REPO/hooks/sloptrim-tracker.js")"
echo "$out" | grep -q "level set to strict"; check "namespaced /sloptrim:sloptrim <arg> routes like the plain form" $?
[ "$(cat "$FLAG")" = "strict" ]; check "namespaced form writes the flag" $?
out="$(echo '{"prompt":"/sloptrim:sloptrim"}' | node "$REPO/hooks/sloptrim-tracker.js")"
echo "$out" | grep -q "Level now:"; check "namespaced bare /sloptrim:sloptrim shows the menu" $?

out="$(echo '{"prompt":"/sloptrim help"}' | node "$REPO/hooks/sloptrim-tracker.js")"
echo "$out" | grep -q "check <file>"; check "help card lists commands" $?
out="$(printf '{"prompt":"/sloptrim check %s"}' "$SLOP" | node "$REPO/hooks/sloptrim-tracker.js")"
echo "$out" | grep -qE "reads .*score [0-9]+/100"; check "check scores a file without rewriting" $?
echo "$out" | grep -q "report only"; check "check declares itself report-only" $?
out="$(echo '{"prompt":"/sloptrim check no_such_file.md"}' | node "$REPO/hooks/sloptrim-tracker.js")"
echo "$out" | grep -q "cannot read"; check "check fails cleanly on a missing file" $?
INITDIR="$CLAUDE_CONFIG_DIR/initrepo"; mkdir -p "$INITDIR"
out="$(cd "$INITDIR" && echo '{"prompt":"/sloptrim init"}' | node "$REPO/hooks/sloptrim-tracker.js")"
grep -q "sloptrim-contract" "$INITDIR/AGENTS.md"; check "init writes the contract into AGENTS.md" $?
out="$(cd "$INITDIR" && echo '{"prompt":"/sloptrim init"}' | node "$REPO/hooks/sloptrim-tracker.js")"
echo "$out" | grep -q "already present"; check "init is idempotent" $?

echo full > "$FLAG"
TRANSCRIPT="$CLAUDE_CONFIG_DIR/fake-session.jsonl"
cat > "$TRANSCRIPT" <<'EOF'
{"type":"assistant","message":{"usage":{"output_tokens":120,"cache_read_input_tokens":900},"content":[{"type":"text","text":"The parser reads one token at a time. If it sees an opening brace it pushes a new scope onto the stack, and closing braces pop it right back off again."}]}}
{"type":"assistant","message":{"usage":{"output_tokens":80,"cache_read_input_tokens":400},"content":[{"type":"text","text":"Errors bubble up as exceptions, which the caller catches and reports with a line number so the failure is easy to trace back to its source line."}]}}
EOF
out="$(printf '{"prompt":"/sloptrim stats","transcript_path":"%s"}' "$TRANSCRIPT" | node "$REPO/hooks/sloptrim-tracker.js")"
echo "$out" | grep -q "assistant turns: 2"; check "stats counts assistant turns from the transcript" $?
echo "$out" | grep -q "output tokens: 200"; check "stats sums real output_tokens" $?
echo "$out" | grep -q "cache-read input tokens: 1,300"; check "stats sums real cache-read tokens" $?
echo "$out" | grep -q "ai_tell_score"; check "stats scores the session's own prose" $?
out="$(echo '{"prompt":"/sloptrim stats","transcript_path":"'"$CLAUDE_CONFIG_DIR"'/no_such.jsonl"}' | node "$REPO/hooks/sloptrim-tracker.js")"
echo "$out" | grep -q "no session"; check "stats fails cleanly on a missing transcript" $?

FRESH="$(topath "$(mktemp -d)")"
out="$(CLAUDE_CONFIG_DIR="$FRESH" node "$REPO/hooks/sloptrim-activate.js" </dev/null)"
echo "$out" | grep -q "SLOPTRIM ACTIVE - level: full"; check "fresh install: contract on by default, no setup" $?
out="$(echo '{"prompt":"/sloptrim doctor"}' | CLAUDE_CONFIG_DIR="$FRESH" node "$REPO/hooks/sloptrim-tracker.js")"
echo "$out" | grep -q "python runs the detector"; check "fresh install: doctor reports detector health" $?
echo "$out" | grep -q "All good"; check "fresh install: doctor gives the all-clear" $?

crashed=0
for hook in activate tracker guard stats; do
  for payload in 'null' '[1,2,3]' 'not json' '{"prompt":42}' '{"tool_input":null}' '{"transcript_path":123}' ''; do
    printf '%s' "$payload" | node "$REPO/hooks/sloptrim-$hook.js" >/dev/null 2>&1
    [ $? -ne 0 ] && crashed=1
  done
done
[ "$crashed" -eq 0 ]; check "no hook exits nonzero on malformed input" $?

echo
echo "hook tests: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
