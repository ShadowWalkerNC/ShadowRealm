const { app, BrowserWindow, shell, Tray, Menu } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

let mainWindow;
let pyProcess;
let tray;

const PORT = process.env.PORT || 7000;
const SERVER_URL = `http://127.0.0.1:${PORT}`;

function startPythonBackend() {
  console.log('Starting Odysseus Python FastAPI backend...');
  const pythonExecutable = process.platform === 'win32' ? 'python' : 'python3';
  
  pyProcess = spawn(pythonExecutable, ['-m', 'uvicorn', 'app:app', '--host', '0.0.0.0', '--port', String(PORT)], {
    cwd: __dirname,
    env: { ...process.env, APP_BIND: '0.0.0.0', APP_PORT: String(PORT) }
  });

  pyProcess.stdout.on('data', (data) => {
    console.log(`[Odysseus Backend]: ${data}`);
  });

  pyProcess.stderr.on('data', (data) => {
    console.error(`[Odysseus Backend Error]: ${data}`);
  });

  pyProcess.on('close', (code) => {
    console.log(`Odysseus backend exited with code ${code}`);
  });
}

function pollServer(callback) {
  http.get(SERVER_URL, (res) => {
    callback(true);
  }).on('error', () => {
    setTimeout(() => pollServer(callback), 500);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    title: 'Odysseus - Autonomous AI Developer Suite',
    icon: path.join(__dirname, 'static', 'favicon.ico'),
    frame: true,
    autoHideMenuBar: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      webSecurity: true
    }
  });

  mainWindow.loadURL(SERVER_URL);

  // Handle external links opening in user's default browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http:') || url.startsWith('https:')) {
      shell.openExternal(url);
      return { action: 'deny' };
    }
    return { action: 'allow' };
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function createSystemTray() {
  try {
    const iconPath = path.join(__dirname, 'static', 'favicon.ico');
    tray = new Tray(iconPath);
    const contextMenu = Menu.buildFromTemplate([
      { label: 'Open Odysseus', click: () => { if (mainWindow) mainWindow.show(); else createWindow(); } },
      { label: 'Open in Browser', click: () => shell.openExternal(SERVER_URL) },
      { type: 'separator' },
      { label: 'Quit Odysseus', click: () => { app.isQuitting = true; app.quit(); } }
    ]);
    tray.setToolTip('Odysseus AI Developer Suite');
    tray.setContextMenu(contextMenu);
    tray.on('double-click', () => {
      if (mainWindow) mainWindow.show();
    });
  } catch (e) {
    console.log('System tray creation skipped:', e.message);
  }
}

app.whenReady().then(() => {
  startPythonBackend();
  createSystemTray();
  
  pollServer(() => {
    createWindow();
  });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('will-quit', () => {
  if (pyProcess) {
    console.log('Stopping Python backend...');
    pyProcess.kill('SIGTERM');
  }
});
