#!/usr/bin/env node
// SubagentStart hook: gives a spawned agent the same contract the session has.
//
// SessionStart context reaches the parent thread only. Without this hook, an
// agent that delegates a document to a subagent gets prose written with no
// contract at all, and the only thing standing between that prose and the user
// is the file guard, which fires after the fact and only when the subagent
// happens to save through Write or Edit.
//
// The measured version of that gap: six documents drafted by subagents scored
// the same whether the tool was switched on or off, because the contract was
// never in their context either way.
//
// SubagentStart drops raw stdout. The context has to be returned in the
// hookSpecificOutput form or it is silently discarded, which looks exactly like
// a working hook.
'use strict';
process.on('uncaughtException', () => process.exit(0));
process.on('unhandledRejection', () => process.exit(0));

const { readMode, contract, LEVELS } = require('./sloptrim-lib');

const mode = readMode();
if (mode === 'off' || !LEVELS.includes(mode)) process.exit(0);

try {
  process.stdout.write(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'SubagentStart',
      additionalContext: contract(mode),
    },
  }));
} catch (e) {
  // A stdout failure at hook exit must not surface as a hook failure.
}
process.exit(0);
