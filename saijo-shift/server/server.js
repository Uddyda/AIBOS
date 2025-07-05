// server.js
const express = require("express");
const cors = require("cors");
const fs = require("fs");
const path = require("path");

const app = express();
const PORT = 3001;

// ------------ 設定値(必要に応じて変更) ------------
const OUTPUT_DIR = path.join(__dirname, "output");
const DEFINE_JSON_DIRECTORY = path.join(__dirname, "define");
const MAX_FILE_COUNT = 30; // JSONファイルの上限数
const MAX_FILE_AGE_DAYS = 90; // 何日経過で削除するか。不要なら0にして無効化

// ------------ ミドルウェア ------------
app.use(cors());
app.use(express.json());

// ------------ 初期化 ------------
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

// ------------ 1) ファイル一覧 ------------
app.get("/api/list-files", (req, res) => {
  try {
    const files = fs
      .readdirSync(OUTPUT_DIR) // output/ディレクトリの一覧取得
      .filter((f) => f.endsWith(".json")) // 拡張子 .json のみ
      .map((f) => path.parse(f).name); // 拡張子を除いたファイル名だけ返す

    res.status(200).json(files);
  } catch (err) {
    console.error("ファイル一覧取得エラー:", err);
    res.status(500).send("ファイル一覧取得に失敗しました");
  }
});

// ------------ 2) ファイル読み込み ------------
app.get("/api/load-json", (req, res) => {
  // /api/load-json?filename=xxx
  const filename = req.query.filename;
  if (!filename) {
    return res
      .status(400)
      .send("filename パラメータが必要です。例: ?filename=myShift");
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

// ------------ 3) ファイル保存 ------------
app.post("/api/save-json", (req, res) => {
  // /api/save-json?filename=xxx
  const { filename, key } = req.query;  
  console.log("受け取った filename:", filename); // ログを追加

  if (!filename) {
    return res.status(400).send("filename パラメータが必要です。例: ?filename=myShift");
  }

  // key に基づいて保存先を分ける
  if (key === 'define') {
    // 'define'の場合は、define.jsonという名前で保存
    filePath = path.join(DEFINE_JSON_DIRECTORY, "define.json");
    console.log(`key=${key}`);
  } else {
    // 'normal'の場合は通常の名前で保存
    filePath = path.join(OUTPUT_DIR, `${filename}.json`);
    console.log(`key=${key}`);

  }

  const data = req.body;

  fs.writeFile(filePath, JSON.stringify(data, null, 2), (err) => {
    if (err) {
      console.error("ファイル保存エラー:", err);
      return res.status(500).send("ファイル保存に失敗しました");
    }
    console.log(`保存成功: ${filePath}`);

    // オプション：古いファイルを削除する cleanup
    cleanupOldFiles(OUTPUT_DIR);

    return res.status(200).send(`ファイルを保存しました: ${filename}.json`);
  });
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
        mtime: stats.mtime, // 更新日時
      };
    });

  // (A) ファイル数が多い場合、古い順に削除
  if (files.length > MAX_FILE_COUNT) {
    files.sort((a, b) => a.mtime.getTime() - b.mtime.getTime());
    const overCount = files.length - MAX_FILE_COUNT;
    const toDelete = files.slice(0, overCount);
    toDelete.forEach((file) => {
      fs.unlinkSync(file.path);
      console.log("ファイル数制限で削除:", file.filename);
    });
  }

  // (B) 一定日数経過で削除
  if (MAX_FILE_AGE_DAYS > 0) {
    const now = Date.now();
    files.forEach((file) => {
      const ageMs = now - file.mtime.getTime();
      const ageDays = ageMs / (1000 * 60 * 60 * 24);
      if (ageDays > MAX_FILE_AGE_DAYS) {
        fs.unlinkSync(file.path);
        console.log("期間超過で削除:", file.filename);
      }
    });
  }
}

// ------------ サーバー起動 ------------
app.listen(PORT, () => {
  console.log(`✅ サーバー起動: http://localhost:${PORT}`);
});
