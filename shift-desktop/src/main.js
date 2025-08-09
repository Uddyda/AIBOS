// topdir/src/main.js
const { app, BrowserWindow, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

let serverProc = null;
let win = null;

// ---- GPU由来クラッシュ切り分け（必要時に有効化）----
// app.disableHardwareAcceleration();

function log(...args) {
  try {
    const p = path.join(app.getPath('userData'), 'main.log');
    fs.appendFileSync(p, `[${new Date().toISOString()}] ${args.join(' ')}\n`);
  } catch {}
  console.log(...args);
}

function createWindow() {
  const isProd = app.isPackaged;
  log('[main] createWindow called. isProd=', isProd);

  win = new BrowserWindow({
    width: 1200,
    height: 800,
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  win.on('ready-to-show', () => {
    log('[main] BrowserWindow ready-to-show');
    win.show();
  });

  if (!isProd) {
    log('[main] loadURL dev server');
    win.loadURL('http://localhost:5173').catch(err => {
      log('[main] loadURL error', err?.stack || err);
    });
  } else {
    const htmlPath = path.join(app.getAppPath(), 'dist', 'index.html');
    if (!fs.existsSync(htmlPath)) {
      log('[main] dist/index.html NOT FOUND:', htmlPath);
      dialog.showErrorBox(
        '起動に失敗しました',
        'アプリのUIファイル（dist/index.html）が見つかりません。vite build が実行されているか確認してください。'
      );
    }
    log('[main] loadFile', htmlPath);
    win.loadFile(htmlPath).catch(err => {
      log('[main] loadFile error', err?.stack || err);
    });
  }

  win.on('closed', () => {
    win = null;
  });
}

function startServerAfterWindow() {
  const isProd = app.isPackaged;
  const APP_ROOT = app.getAppPath();
  const USER_DATA_DIR = app.getPath('userData');
  const serverJs = path.join(APP_ROOT, 'server', 'server.js');

  // ---- 本番は同梱 venv の Python を使う ----
  const PYTHON_BIN = isProd
    ? (process.platform === 'win32'
        ? path.join(process.resourcesPath, 'python-win', 'Scripts', 'python.exe')
        : path.join(process.resourcesPath, 'python-mac', 'bin', 'python'))
    : 'python3';

  log('[main] startServerAfterWindow');
  log('[main] APP_ROOT=', APP_ROOT);
  log('[main] USER_DATA_DIR=', USER_DATA_DIR);
  log('[main] serverJs=', serverJs);
  log('[main] PYTHON_BIN=', PYTHON_BIN);

  try {
    serverProc = spawn(process.execPath, [serverJs], {
      env: {
        ...process.env,
        ELECTRON_RUN_AS_NODE: '1',
        APP_ROOT,
        USER_DATA_DIR,
        PYTHON_BIN,
        NODE_ENV: isProd ? 'production' : 'development',
        PYTHONNOUSERSITE: '1' // ← ユーザー環境を無視して隔離
      },
      stdio: 'pipe',
      windowsHide: true,
    });

    serverProc.stdout.on('data', d => log('[server][out]', String(d).trim()));
    serverProc.stderr.on('data', d => log('[server][err]', String(d).trim()));

    serverProc.on('error', (err) => {
      log('[server] spawn error', err?.stack || err);
      dialog.showErrorBox('サーバ起動に失敗', String(err?.message || err));
    });

    serverProc.on('exit', (code, sig) => {
      log('[server] exit code=', code, 'signal=', sig);
    });
  } catch (e) {
    log('[server] spawn threw', e?.stack || e);
  }
}

// 予期せぬ例外もログに
process.on('uncaughtException', (err) => log('[uncaughtException]', err?.stack || err));
process.on('unhandledRejection', (err) => log('[unhandledRejection]', err?.stack || err));

app.whenReady().then(() => {
  log('[main] app.whenReady');
  createWindow();           // まずウィンドウを作る
  startServerAfterWindow(); // その後にサーバを起動
});

app.on('window-all-closed', () => {
  log('[main] window-all-closed');
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => {
  log('[main] before-quit');
  if (serverProc) {
    try { serverProc.kill(); } catch {}
  }
});
