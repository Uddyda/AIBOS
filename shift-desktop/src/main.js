// topdir/src/main.js
const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let serverProc = null;

function createWindow() {
  const isProd = app.isPackaged;

  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  if (!isProd) {
    // Dev: Vite の開発サーバ
    win.loadURL('http://localhost:5173');
  } else {
    // Prod: asar内でも安全に参照できるように app.getAppPath() からの相対にする
    win.loadFile(path.join(app.getAppPath(), 'dist', 'index.html'));
  }
}

app.whenReady().then(() => {
  const isProd = app.isPackaged;

  // 読み取り用ルート（dev: リポジトリ直下 / prod: app.asar or resources）
  const APP_ROOT = app.getAppPath();

  // 書き込み用（OSごとのユーザーデータ領域）
  const USER_DATA_DIR = app.getPath('userData');

  // server.js の実体（dev も prod も APP_ROOT 配下を見る）
  const serverJs = path.join(APP_ROOT, 'server', 'server.js');

  // Python 実行ファイル（prod は同梱、dev はシステム python）
  const PYTHON_BIN = isProd
    ? path.join(
        process.resourcesPath,
        'python',
        process.platform === 'win32' ? 'python.exe' : 'bin/python3'
      )
    : 'python3';

  // Electron 実行ファイルを Node として使い server.js を起動
  serverProc = spawn(process.execPath, [serverJs], {
    env: {
      ...process.env,
      ELECTRON_RUN_AS_NODE: '1',
      APP_ROOT,
      USER_DATA_DIR,
      PYTHON_BIN,
      NODE_ENV: isProd ? 'production' : 'development',
    },
    stdio: 'inherit',
  });

  // NOTE: 厳密には wait-on 等で http://localhost:3001 を待つ方が安全
  setTimeout(createWindow, 1500);
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => {
  if (serverProc) serverProc.kill();
});
