#!/usr/bin/env node

// Simple local helper: runs the Python scanner and writes JSON outputs.
// Usage:
//   npm run scan
//   node scripts/run-scan.js

const { spawnSync } = require('node:child_process');
const path = require('node:path');

const repoRoot = path.resolve(__dirname, '..');
const workdir = path.join(repoRoot, 'market_ai_kit');

const python = process.env.PYTHON || 'python';
const config = process.env.SCAN_CONFIG || 'config.yaml';

const result = spawnSync(
  python,
  ['-m', 'scanner.run', '--config', config],
  { cwd: workdir, stdio: 'inherit' }
);

process.exit(result.status ?? 1);
