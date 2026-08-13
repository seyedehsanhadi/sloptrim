#!/usr/bin/env node
// SessionStart hook: emits the prose contract for the active mode.
'use strict';
process.on('uncaughtException', () => process.exit(0));
process.on('unhandledRejection', () => process.exit(0));
const { readMode, writeMode, contract, LEVELS, sweepLedgers } = require('./sloptrim-lib');

sweepLedgers();

const mode = readMode();
if (mode === 'off') process.exit(0);
if (LEVELS.includes(mode)) writeMode(mode);
process.stdout.write(contract(mode));
process.exit(0);
