import os
import sys
from modify import process_swift_file  # 导入你写的处理单个文件函数

def traverse_and_process(root_dir):
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".swift"):
                full_path = os.path.join(dirpath, filename)
                print(f"Processing file: {full_path}")
                try:
                    process_swift_file(full_path)
                except Exception as e:
                    print(f"⚠️ 处理文件 {full_path} 时出错: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <root_directory>")
        sys.exit(1)

    root_directory = sys.argv[1]
    if not os.path.isdir(root_directory):
        print(f"错误：{root_directory} 不是有效目录")
        sys.exit(1)

    traverse_and_process(root_directory)