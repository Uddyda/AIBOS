const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let nodeProcess = null;
let pythonProcess = null;

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  const isDev = !app.isPackaged;
  if (isDev) {
    win.loadURL('http://localhost:5173');
  } else {
    win.loadFile(path.join(__dirname, '../dist/index.html'));
  }
}

app.whenReady().then(() => {
  // 1. Nodeサーバーをspawnで裏起動（例: server/server.js）
  nodeProcess = spawn('node', [path.join(__dirname, '../server/server.js')], {
    shell: true,
    stdio: 'inherit',
  });

  // 2. Pythonスクリプトもspawnで裏起動（例: shift_generator/hello.py）
  pythonProcess = spawn('python3', [path.join(__dirname, '../shift_generator/json_converter.py')], {
    shell: true,
    stdio: 'inherit',
  });

  // 3. Pythonスクリプトもspawnで裏起動（例: shift_generator/hello.py）
  pythonProcess = spawn('python3', [path.join(__dirname, '../shift_generator/shift_generater.py')], {
    shell: true,
    stdio: 'inherit',
  });

  setTimeout(createWindow, 2000); // サーバー起動待ち
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => {
  if (nodeProcess) nodeProcess.kill();
  if (pythonProcess) pythonProcess.kill();
});
