import os
import tempfile
import ctypes
import pytest
import json
import pyogrio
import pandas as pd
import shutil

#出力先のディレクトリ内をクリーンする
def clear_directory(directory_path):
    """指定したディレクトリ内のファイルのみをすべて削除"""
    if os.path.exists(directory_path):
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print('Error file can not be deleted')


clear_directory('./tmp/results')#ディレクトリの中身を一度削除

# 複数の入力ファイルパスをリストとして定義する####
df_keys = pd.read_csv('./tmp/matching_route_and_edges.csv')
INP_FILES = []

for k in range(0,len(df_keys)):
    inp_file_path=f"./tmp/input_files/input{k}.inp"
    INP_FILES.append(inp_file_path)
LIB_PATH = "./../EPANET/build/lib/libepanet2.so"

def count_nodes(inp_file):
    with open(inp_file, 'r') as f:
        lines = f.readlines()
    node_section = False
    node_count = 0
    for line in lines:
        line = line.strip()
        if line.startswith("[JUNCTIONS]") or line.startswith("[RESERVOIRS]") or line.startswith("[TANKS]"):
            node_section = True
        elif not line:
            node_section = False
        elif line.startswith(";ID"):
            pass
        elif node_section and line.strip():
            node_count += 1
    return node_count

def count_links(inp_file):
    with open(inp_file, 'r') as f:
        lines = f.readlines()
    link_section = False
    link_count = 0
    for line in lines:
        line = line.strip()
        if line.startswith("[PIPES]") or line.startswith("[PUMPS]"):
            link_section = True
        elif not line:
            link_section = False
        elif line.startswith(";ID"):
            pass
        elif link_section and line.strip():
            link_count += 1
    return link_count

@pytest.fixture
def create_temp_files():
    with tempfile.NamedTemporaryFile(suffix='.rpt', delete=False) as rpt_file:
        rpt_file_path = rpt_file.name

    with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as bin_file:
        bin_file_path = bin_file.name

    return rpt_file_path, bin_file_path


def load():
    epanetlib = ctypes.CDLL(LIB_PATH)
    epanetlib.ENepanet.argtypes = [
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_void_p,
    ]
    epanetlib.ENepanet.restype = ctypes.POINTER(ctypes.c_double)
    return epanetlib.ENepanet

def perform(func, inp_file, rpt_file, out_file, size):
    result = func(
        ctypes.c_char_p(inp_file.encode("utf-8")),
        ctypes.c_char_p(rpt_file.encode("utf-8")),
        ctypes.c_char_p(out_file.encode("utf-8")),
        ctypes.c_int(size),
        None,
    )
    return result

@pytest.fixture(params=INP_FILES)####
def setup(request,create_temp_files):
    inp_file = request.param
    rpt_file, out_file = create_temp_files
    func = load()
    return func, inp_file, rpt_file, out_file


def test_perform(setup):
    func, inp_file, rpt_file, out_file = setup
    node_count = count_nodes(inp_file) 
    link_count = count_links(inp_file)
    size = link_count + node_count 
    result = perform(func, inp_file, rpt_file, out_file, size)
    result_array = ctypes.cast(result, ctypes.POINTER(ctypes.c_double * (2 * size))).contents
    os.remove(out_file)

    # 結果を格納するリスト
    results = {
        "nodes": [],
        "links": []
    }

    # ノードのデータを追加
    for i in range(2 * node_count):
        if i % 2 == 0:
            node_info = {
                "ノード番号": result_array[i]
            }
        else:
            node_info["水圧"] = result_array[i]
            results["nodes"].append(node_info)

    # リンクのデータを追加
    for j in range(2 * link_count):
        if j % 2 == 0:
            link_info = {
                "リンク番号": result_array[2 * node_count + j]
            }
        else:
            link_info["流量"] = result_array[2 * node_count + j]
            results["links"].append(link_info)

    

    # 各入力ファイルごとに異なる JSON ファイルとして保存####
    seg_name=os.path.splitext(os.path.basename(inp_file))[0]
    file_name=f"results_{seg_name}.json"
    output_directory = './tmp/results'
    output_path = os.path.join(output_directory, file_name)

    # ディレクトリが存在しない場合は作成
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    with open(output_path, "w", encoding="utf-8") as log_file:
        json.dump(results, log_file, ensure_ascii=False, indent=4)

    assert len(result_array) == 2 * size

if __name__ == "__main__":
    pytest.main([__file__])
