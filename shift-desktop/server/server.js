const express = require("express");
const cors = require("cors");
const fs = require("fs");
const path = require("path");
const { execFile } = require("child_process");
const archiver = require("archiver");
const app = express();
const PORT = 3001;

current_path=process.cwd()
console.log("現在の__dirname:", __dirname);
console.log("現在のカレントディレクトリ(process.cwd()):", process.cwd());

// ------------ 設定値 ------------
const OUTPUT_DIR = path.join(__dirname, "output_json");
const OUTPUT_CSV = path.join(current_path, "output_shift");
const DEFINE_JSON_DIRECTORY = path.join(__dirname, "define");
const baseDir = path.join(__dirname, "../shift_generator");
const MAX_FILE_COUNT = 30;
const MAX_FILE_AGE_DAYS = 90;

// ------------ ミドルウェア ------------
app.use(cors());
app.use(express.json());




// ------------ 初期化 ------------
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

// ------------ ファイル一覧取得 ------------
app.get("/api/list-files", (req, res) => {
  console.log("GET /api/list-files called");
  try {
    console.log("OUTPUT_DIR:", OUTPUT_DIR);
    const files = fs
      .readdirSync(OUTPUT_DIR)
      .filter((f) => f.endsWith(".json"))
      .map((f) => path.parse(f).name);
    console.log("json files:", files);
    res.status(200).json(files);
  } catch (err) {
    console.error("ファイル一覧取得エラー:", err, typeof err, JSON.stringify(err));
    res.status(500).send(`ファイル一覧取得に失敗しました\nerr: ${err}\nJSON: ${JSON.stringify(err)}\nstack: ${err && err.stack}`);
  }
});

// ------------ ファイル読み込み ------------
app.get("/api/load-json", (req, res) => {
  const filename = req.query.filename;
  if (!filename) {
    return res.status(400).send("filename パラメータが必要です。例: ?filename=myShift");
  }
  const filePath = path.join(OUTPUT_DIR, `${filename}.json`);
  if (!fs.existsSync(filePath)) {
    return res.status(404).send("指定ファイルは存在しません");
  }

  fs.readFile(filePath, "utf8", (err, fileData) => {
    if (err) {
      console.error("読み込みエラー:", err);
      return res.status(500).send("ファイル読み込みに失敗しました");
    }
    try {
      const jsonObj = JSON.parse(fileData);
      res.status(200).json(jsonObj);
    } catch (parseErr) {
      console.error("JSON解析エラー:", parseErr);
      res.status(500).send("JSON解析に失敗しました");
    }
  });
});

// ------------ ファイル保存 ------------
app.post("/api/save-json", (req, res) => {
  const { filename, key } = req.query;
  if (!filename) {
    return res.status(400).send("filename パラメータが必要です。例: ?filename=myShift");
  }

  let filePath;
  if (key === 'define') {
    filePath = path.join(DEFINE_JSON_DIRECTORY, "define.json");
  } else {
    filePath = path.join(OUTPUT_DIR, `${filename}.json`);
  }

  const data = req.body;

  fs.writeFile(filePath, JSON.stringify(data, null, 2), (err) => {
    if (err) {
      console.error("ファイル保存エラー:", err);
      return res.status(500).send("ファイル保存に失敗しました");
    }
    cleanupOldFiles(OUTPUT_DIR);
    return res.status(200).send(`ファイルを保存しました: ${filename}.json`);
  });
});

// ------------ ファイル削除 ------------
app.delete("/api/delete-json", (req, res) => {
  const filename = req.query.filename;
  if (!filename) {
    return res.status(400).send("filename パラメータが必要です。例: ?filename=myShift");
  }
  const filePath = path.join(OUTPUT_DIR, `${filename}.json`);
  if (!fs.existsSync(filePath)) {
    return res.status(404).send("指定ファイルが存在しません");
  }
  fs.unlink(filePath, (err) => {
    if (err) {
      console.error("ファイル削除エラー:", err);
      return res.status(500).send("ファイル削除に失敗しました");
    }
    return res.status(200).send("ファイル削除に成功しました");
  });
});


// ------------ Pythonスクリプトを順次実行するAPI ------------
app.post("/api/run-python", (req, res) => {
  console.log("==== /api/run-python called ====");

  // 動的な出力ディレクトリ名生成
  const { filename } = req.body;
  const now = new Date();// 例: "2024-07-11T15:30:45.123Z"
  const yyyy = now.getFullYear();
  const mm = String(now.getMonth() + 1).padStart(2, "0"); // 月は0始まり
  const dd = String(now.getDate()).padStart(2, "0");
  const dateStr = `${yyyy}${mm}${dd}`;  // "20240711"
  const dynamicDirName = `shift_${filename}_${dateStr}`;
    if (!filename) {
    return res.status(400).send("filenameパラメータが必要です");
  }

  const jsonPath = path.join(DEFINE_JSON_DIRECTORY, `define.json`);
  const baseDir = path.join(__dirname, "../shift_generator");
  const converterPy = path.join(baseDir, "json_converter.py");
  const shiftGenPy = path.join(baseDir, "shift_generator.py");

  if (!fs.existsSync(jsonPath)) {
    console.error("jsonファイルが見つかりません: " + jsonPath);
    return res.status(404).send("指定jsonファイルがありません");
  }

  // Mac の pip --user 問題対策
  const env = { ...process.env, PYTHONPATH: '/Users/uchidaatsuya/Library/Python/3.9/lib/python/site-packages' };//書き換える必要あり

  // 1. json_converter.py
  execFile("python3", [converterPy, jsonPath], { env }, (err1, stdout1, stderr1) => {
    console.log("=== [json_converter.py] ===");
    if (stdout1) console.log("stdout:", stdout1);
    if (stderr1) console.log("stderr:", stderr1);
    if (err1) {
      console.error("json_converter.py error:", err1);
      return res.status(500).send("json_converter.py 実行に失敗しました\n" + (stderr1 || err1));
    }

    // 2. shift_generator.py
    execFile("python3", [shiftGenPy, dynamicDirName], { env }, (err2, stdout2, stderr2) => {
      console.log("=== [shift_generator.py] ===");
      if (stdout2) console.log("stdout:", stdout2);
      if (stderr2) console.log("stderr:", stderr2);
      if (err2) {
        console.error("shift_generator.py error:", err2);
        return res.status(500).send("shift_generator.py 実行に失敗しました\n" + (stderr2 || err2));
      }

      // ★成功時
      res.status(200).json({
        message: "計算成功",
        zipFileName: dynamicDirName,
        zipUrl: `/download_zip/${dynamicDirName}`,
      });
    });
  });
  const shiftParentDir = process.cwd();
  cleanupOldShiftDirs(shiftParentDir, 10);// 古いshiftディレクトリを保持する数（ここに書いた数字＋１個まで保持）
});

// ------------ 静的ファイルを公開(ユーザーがダウンロードするファイル) ------------
app.get("/download_zip/:dirName", (req, res) => {
  const { dirName } = req.params;
  const targetDir = path.join(process.cwd(), dirName);

  if (!fs.existsSync(targetDir)) {
    return res.status(404).send("指定ディレクトリが存在しません");
  }
  res.attachment(`${dirName}.zip`);
  const archive = archiver('zip');
  archive.directory(targetDir, false);
  archive.pipe(res);
  archive.finalize();
});

// 過去の出力CSVのダウンロードリンクを取得
app.get("/api/list-shift-dirs", (req, res) => {
  const basePath = path.join(__dirname, ".."); // ← serverと同階層
  const re = /^shift_.*_\d{8}$/;
  try {
    const dirs = fs.readdirSync(basePath)
      .filter(f => re.test(f) && fs.statSync(path.join(basePath, f)).isDirectory())
      .map(f => {
        const stats = fs.statSync(path.join(basePath, f));
        return {
          dirName: f,
          mtime: stats.mtime, // 作成・最終更新日時
        };
      })
      .sort((a, b) => b.mtime - a.mtime); // 新しい順
    res.status(200).json(dirs);
  } catch (err) {
    console.error("shiftディレクトリ一覧取得エラー:", err);
    res.status(500).send("shiftディレクトリ一覧取得に失敗しました");
  }
});


// ------------ cleanup関数 --------------
function cleanupOldFiles(dirPath) {
  const files = fs
    .readdirSync(dirPath)
    .filter((f) => f.endsWith(".json"))
    .map((f) => {
      const fullPath = path.join(dirPath, f);
      const stats = fs.statSync(fullPath);
      return {
        filename: f,
        path: fullPath,
        mtime: stats.mtime,
      };
    });

  if (files.length > MAX_FILE_COUNT) {
    files.sort((a, b) => a.mtime.getTime() - b.mtime.getTime());
    const overCount = files.length - MAX_FILE_COUNT;
    const toDelete = files.slice(0, overCount);
    toDelete.forEach((file) => {
      fs.unlinkSync(file.path);
    });
  }

  if (MAX_FILE_AGE_DAYS > 0) {
    const now = Date.now();
    files.forEach((file) => {
      const ageMs = now - file.mtime.getTime();
      const ageDays = ageMs / (1000 * 60 * 60 * 24);
      if (ageDays > MAX_FILE_AGE_DAYS) {
        fs.unlinkSync(file.path);
      }
    });
  }
}

// shift_xxx_YYYYMMDD 形式だけを残す
function cleanupOldShiftDirs(basePath, maxCount) {
  const re = /^shift_.*_\d{8}$/;  // shift_で始まり_8桁で終わる

  const dirs = fs.readdirSync(basePath)
    .filter(f => re.test(f) && fs.statSync(path.join(basePath, f)).isDirectory())
    .map(f => {
      const fullPath = path.join(basePath, f);
      const stats = fs.statSync(fullPath);
      return { name: f, path: fullPath, mtime: stats.mtime };
    });

  dirs.sort((a, b) => a.mtime - b.mtime);

  if (dirs.length > maxCount) {
    const toDelete = dirs.slice(0, dirs.length - maxCount);
    toDelete.forEach(dir => {
      fs.rmSync(dir.path, { recursive: true, force: true });
      console.log("古いshiftディレクトリ削除:", dir.name);
    });
  }
}

// ------------ サーバー起動 ------------
app.listen(PORT, () => {
  console.log(`✅ サーバー起動: http://localhost:${PORT}`);
});
