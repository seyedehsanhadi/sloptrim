'use strict';
const cp = require('child_process');
const assert = require('assert');
const real = cp.execFileSync;
let tried = [];

function stub(behaviour) {
  tried = [];
  cp.execFileSync = (exe, args, opts) => {
    tried.push(exe);
    const b = behaviour[exe];
    if (b === 'ok') return '{"_metrics":{"ai_tell_score":0}}';
    const e = new Error(exe + ' failed');
    if (b === 'timeout') { e.code = 'ETIMEDOUT'; }
    else if (b === 'missing') { e.code = 'ENOENT'; }
    else { e.status = 9009; e.stderr = ''; e.stdout = ''; }
    throw e;
  };
  delete require.cache[require.resolve('../hooks/sloptrim-lib')];
  return require('../hooks/sloptrim-lib');
}

// The Windows Store alias: `python` exists, starts, and exits non-zero. `py` works.
let lib = stub({ python: 'exit', python3: 'exit', py: 'ok' });
let r = lib.runDetectResult('x', {}, []);
assert.deepStrictEqual(tried, ['python', 'python3', 'py'], 'must try every name');
assert.strictEqual(r.ok, true, 'a failing first interpreter must not kill the run');

// Not installed at all: still walks the list, still reports a real failure.
lib = stub({ python: 'missing', python3: 'missing', py: 'missing' });
r = lib.runDetectResult('x', {}, []);
assert.deepStrictEqual(tried, ['python', 'python3', 'py']);
assert.strictEqual(r.ok, false);

// A timeout is the one failure that stops: retrying costs the whole budget again.
lib = stub({ python: 'timeout', python3: 'ok', py: 'ok' });
r = lib.runDetectResult('x', {}, []);
assert.deepStrictEqual(tried, ['python'], 'a timeout must not be retried');
assert.strictEqual(r.ok, false);

// Only the launcher that actually ran is remembered as the failure.
lib = stub({ python: 'missing', python3: 'exit', py: 'missing' });
r = lib.runDetectResult('x', {}, []);
assert.strictEqual(r.ok, false);
assert.notStrictEqual(r.detail, 'ENOENT', 'a missing launcher is not a detector fault');

cp.execFileSync = real;
console.log('interpreter fallback: 4 cases pass');
