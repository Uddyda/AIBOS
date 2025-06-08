import subprocess

# 実行するコードを順番に入れてください
scripts = [
    "overlay.py",
    "create_network.py",
    "elevation_input.py",
    "redefine_edges.py",
    "matching_route_and_edges.py",
    "create_epanet_input.py",
    "test_epanet.py",  # pytestの実行方法については後述
    "COF.py",
    "visualize_results.py"
]

success = True  # すべてのスクリプトが成功したかどうかのフラグ

# スクリプトを順番に実行、pytestはファイル名を指定して実行
for script in scripts:
    try:
        # ファイル名に応じて実行コマンドを決定
        if script == "test_epanet.py":
            command = ["pytest", script]
        else:
            command = ["python", script]

        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(f"Success: {script}")
    except subprocess.CalledProcessError as e:
        # エラーが発生した場合、エラーメッセージを出力
        print(f"Error in {script}: {e.stderr}")
        success = False
        break  # エラーが出たらループを終了する

# すべてのスクリプトが成功した場合にメッセージを表示
if success:
    print("All Process is Completed!! __**|^O^|**_")
