import os

def get_all_files(directory):
    file_paths = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_paths.append(file_path)
    return file_paths

# 指定目录路径
directory = "D:/workspace/youtube_dl_gui/data"

# 获取目录及其子目录中的所有文件路径
files = get_all_files(directory)

# 打印所有文件路径
for file in files:
    print(file)