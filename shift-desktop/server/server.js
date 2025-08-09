// server/server.js
const express = require("express");
const cors = require("cors");
const fs = require("fs");
const path = require("path");
const { execFile } = require("child_process");
const archiver = require("archiver");

const app = express();
const PORT = 3001;

/** ========================
 *  パス方針
 *  - 読み取り（同梱物）: APP_ROOT / resourcesPath
 *  - 書き込み（ユーザーデータ）: USER_DATA_DIR
 * ======================== */
const IS_PROD = process.env.NODE_ENV === "production";
const APP_ROOT = process.env.APP_ROOT || path.resolve(__dirname, ".."); // dev fallback
const USER_DATA_DIR = process.env.USER_DATA_DIR || path.join(APP_ROOT, ".user_data"); // dev fallback
const PYTHON_BIN = process.env.PYTHON_BIN || "python3";
const RESOURCES_DIR = IS_PROD ? process.resourcesPath : APP_ROOT;

console.log("[BOOT] APP_ROOT      :", APP_ROOT);
console.log("[BOOT] USER_DATA_DIR :", USER_DATA_DIR);
console.log("[BOOT] PYTHON_BIN    :", PYTHON_BIN);
console.log("[BOOT] RESOURCES_DIR :", RESOURCES_DIR);

// ------------ 書込み系ディレクトリ ------------
const OUTPUT_DIR = path.join(USER_DATA_DIR, "output_json");
const OUTPUT_CSV = path.join(USER_DATA_DIR, "output_shift");
const DEFINE_JSON_DIRECTORY = path.join(USER_DATA_DIR, "define");

// 読み取り専用（同梱スクリプトは extraResources で resources/shift_generator に出す）
const baseDir = path.join(RESOURCES_DIR, "shift_generator");

const MAX_FILE_COUNT = 30;
const MAX_FILE_AGE_DAYS = 90;

// ------------ ミドルウェア ------------
app.use(cors());
app.use(express.json());

// ------------ 初期化 ------------
[USER_DATA_DIR, OUTPUT_DIR, OUTPUT_CSV, DEFINE_JSON_DIRECTORY].forEach((d) => {
  if (!fs.existsSync(d)) fs.mkdirSync(d, { recursive: true });
});

// ========== 診断 ==========
app.get("/api/diag", (req, res) => {
  execFile(PYTHON_BIN, ["-V"], (err, stdout, stderr) => {
    res.json({
      PYTHON_BIN,
      stdout: stdout?.toString(),
      stderr: stderr?.toString(),
      err: err ? String(err) : null,
      APP_ROOT,
      USER_DATA_DIR,
      RESOURCES_DIR,
      baseDir,
      exists: {
        baseDir: fs.existsSync(baseDir),
        converter: fs.existsSync(path.join(baseDir, "json_converter.py")),
        generator: fs.existsSync(path.join(baseDir, "shift_generator.py")),
        rokuyou: fs.existsSync(path.join(baseDir, "rokuyou.json")),
        define: fs.existsSync(path.join(DEFINE_JSON_DIRECTORY, "define.json")),
      },
    });
  });
});

// ------------ ファイル一覧取得 ------------
app.get("/api/list-files", (req, res) => {
  try {
    const files = fs
      .readdirSync(OUTPUT_DIR)
      .filter((f) => f.endsWith(".json"))
      .map((f) => path.parse(f).name);
    res.status(200).json(files);
  } catch (err) {
    console.error("ファイル一覧取得エラー:", err);
    res.status(500).send("ファイル一覧取得に失敗しました");
  }
});

// ------------ ファイル読み込み ------------
app.get("/api/load-json", (req, res) => {
  const filename = req.query.filename;
  if (!filename) return res.status(400).send("filename パラメータが必要です。");
  const filePath = path.join(OUTPUT_DIR, `${filename}.json`);
  if (!fs.existsSync(filePath)) return res.status(404).send("指定ファイルは存在しません");

  fs.readFile(filePath, "utf8", (err, fileData) => {
    if (err) return res.status(500).send("ファイル読み込みに失敗しました");
    try {
      res.status(200).json(JSON.parse(fileData));
    } catch {
      res.status(500).send("JSON解析に失敗しました");
    }
  });
});

// ------------ ファイル保存 ------------
app.post("/api/save-json", (req, res) => {
  const { filename, key } = req.query;
  if (!filename) return res.status(400).send("filename パラメータが必要です。");

  const filePath =
    key === "define"
      ? path.join(DEFINE_JSON_DIRECTORY, "define.json")
      : path.join(OUTPUT_DIR, `${filename}.json`);

  fs.writeFile(filePath, JSON.stringify(req.body, null, 2), (err) => {
    if (err) {
      console.error("ファイル保存エラー:", err);
      return res.status(500).send("ファイル保存に失敗しました");
    }
    cleanupOldFiles(OUTPUT_DIR);
    res.status(200).send(`ファイルを保存しました: ${path.basename(filePath)}`);
  });
});

// ------------ ファイル削除 ------------
app.delete("/api/delete-json", (req, res) => {
  const { filename } = req.query;
  if (!filename) return res.status(400).send("filename が必要です");
  const filePath = path.join(OUTPUT_DIR, `${filename}.json`);
  try {
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath);
      return res.status(200).send("削除しました");
    }
    return res.status(404).send("指定ファイルが存在しません");
  } catch (e) {
    console.error("削除エラー:", e);
    return res.status(500).send("削除に失敗しました");
  }
});

// ------------ Python実行（変換→生成） ------------
app.post("/api/run-python", (req, res) => {
  console.log("==== /api/run-python called ====");
  const { filename } = req.body;
  if (!filename) return res.status(400).send("filenameパラメータが必要です");

  const now = new Date();
  const dateStr = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, "0")}${String(
    now.getDate()
  ).padStart(2, "0")}`;
  const dynamicDirName = `shift_${filename}_${dateStr}`;

  // パスを明示
  const defineJsonPath = path.join(DEFINE_JSON_DIRECTORY, "define.json");
  const newJsonPath = path.join(USER_DATA_DIR, "new.json");
  const converterPy = path.join(baseDir, "json_converter.py");
  const shiftGenPy = path.join(baseDir, "shift_generator.py");
  const rokuyouJsonPath = path.join(baseDir, "rokuyou.json");
  const targetOutputDir = path.join(USER_DATA_DIR, dynamicDirName);

  console.log("[RUN] PYTHON_BIN      :", PYTHON_BIN);
  console.log("[RUN] converterPy     :", converterPy);
  console.log("[RUN] shiftGenPy      :", shiftGenPy);
  console.log("[RUN] defineJsonPath  :", defineJsonPath);
  console.log("[RUN] newJsonPath     :", newJsonPath);
  console.log("[RUN] rokuyouJsonPath :", rokuyouJsonPath);
  console.log("[RUN] targetOutputDir :", targetOutputDir);

  if (!fs.existsSync(defineJsonPath)) {
    console.error("define.json が見つかりません:", defineJsonPath);
    return res.status(404).send("define.json がありません");
  }
  if (!fs.existsSync(converterPy) || !fs.existsSync(shiftGenPy)) {
    console.error("Pythonスクリプトが見つかりません:", baseDir);
    return res.status(500).send("Pythonスクリプトが見つかりません");
  }
  if (!fs.existsSync(path.dirname(newJsonPath))) {
    fs.mkdirSync(path.dirname(newJsonPath), { recursive: true });
  }
  if (!fs.existsSync(targetOutputDir)) {
    fs.mkdirSync(targetOutputDir, { recursive: true });
  }

  const execOpts = { env: { ...process.env }, cwd: USER_DATA_DIR };

  // 1) 旧→新 変換
  execFile(
    PYTHON_BIN,
    [converterPy, defineJsonPath, newJsonPath, rokuyouJsonPath],
    execOpts,
    (err1, stdout1, stderr1) => {
      console.log("=== [json_converter.py] ===");
      if (stdout1) console.log(stdout1);
      if (stderr1) console.log(stderr1);
      if (err1) {
        console.error("json_converter.py error:", err1);
        return res
          .status(500)
          .send("json_converter.py 実行に失敗しました\n" + (stderr1 || String(err1)));
      }

      // 2) シフト生成
      execFile(
        PYTHON_BIN,
        [shiftGenPy, dynamicDirName, newJsonPath, USER_DATA_DIR],
        execOpts,
        (err2, stdout2, stderr2) => {
          console.log("=== [shift_generator.py] ===");
          if (stdout2) console.log(stdout2);
          if (stderr2) console.log(stderr2);
          if (err2) {
            console.error("shift_generator.py error:", err2);
            return res
              .status(500)
              .send("shift_generator.py 実行に失敗しました\n" + (stderr2 || String(err2)));
          }

          res.status(200).json({
            message: "計算成功",
            zipFileName: dynamicDirName,
            zipUrl: `/download_zip/${dynamicDirName}`,
          });
        }
      );
    }
  );
});

// ------------ ZIPダウンロード ------------
app.get("/download_zip/:dirName", (req, res) => {
  const { dirName } = req.params;
  const targetDir = path.join(USER_DATA_DIR, dirName);
  if (!fs.existsSync(targetDir)) return res.status(404).send("指定ディレクトリが存在しません");

  res.attachment(`${dirName}.zip`);
  const archive = archiver("zip");
  archive.directory(targetDir, false);
  archive.pipe(res);
  archive.finalize();
});

// ------------ 過去出力一覧 ------------
app.get("/api/list-shift-dirs", (req, res) => {
  const basePath = USER_DATA_DIR;
  const re = /^shift_.*_\d{8}$/;
  try {
    const dirs = fs
      .readdirSync(basePath)
      .filter((f) => re.test(f) && fs.statSync(path.join(basePath, f)).isDirectory())
      .map((f) => {
        const stats = fs.statSync(path.join(basePath, f));
        return { dirName: f, mtime: stats.mtime };
      })
      .sort((a, b) => b.mtime - a.mtime);
    res.status(200).json(dirs);
  } catch (err) {
    console.error("shiftディレクトリ一覧取得エラー:", err);
    res.status(500).send("shiftディレクトリ一覧取得に失敗しました");
  }
});

// ------------ cleanup --------------
function cleanupOldFiles(dirPath) {
  const files = fs
    .readdirSync(dirPath)
    .filter((f) => f.endsWith(".json"))
    .map((f) => {
      const fullPath = path.join(dirPath, f);
      const stats = fs.statSync(fullPath);
      return { filename: f, path: fullPath, mtime: stats.mtime };
    });

  if (files.length > MAX_FILE_COUNT) {
    files.sort((a, b) => a.mtime - b.mtime);
    const toDelete = files.slice(0, files.length - MAX_FILE_COUNT);
    toDelete.forEach((file) => fs.unlinkSync(file.path));
  }

  if (MAX_FILE_AGE_DAYS > 0) {
    const now = Date.now();
    files.forEach((file) => {
      const ageDays = (now - file.mtime.getTime()) / (1000 * 60 * 60 * 24);
      if (ageDays > MAX_FILE_AGE_DAYS) fs.unlinkSync(file.path);
    });
  }
}

function cleanupOldShiftDirs(basePath, maxCount) {
  const re = /^shift_.*_\d{8}$/;
  const dirs = fs
    .readdirSync(basePath)
    .filter((f) => re.test(f) && fs.statSync(path.join(basePath, f)).isDirectory())
    .map((f) => {
      const fullPath = path.join(basePath, f);
      const stats = fs.statSync(fullPath);
      return { name: f, path: fullPath, mtime: stats.mtime };
    });

  dirs.sort((a, b) => a.mtime - b.mtime);
  if (dirs.length > maxCount) {
    const toDelete = dirs.slice(0, dirs.length - maxCount);
    toDelete.forEach((dir) => {
      fs.rmSync(dir.path, { recursive: true, force: true });
      console.log("古いshiftディレクトリ削除:", dir.name);
    });
  }
}

// ------------ 起動 ------------
app.listen(PORT, () => {
  console.log(`✅ サーバー起動: http://localhost:${PORT}`);
});
