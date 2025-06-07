import os
import re
import requests

# 文件路径和保存目录
file_path = r"C:\Users\wyg\Desktop\NO.23_牧场物语_乳猪.md"
save_directory = r"C:\Users\wyg\Desktop\images"

# 确保保存目录存在
os.makedirs(save_directory, exist_ok=True)

# 正则匹配 URL (简单版，匹配 http 或 https 开头的图片链接)
url_pattern = re.compile(r'(https?://[^\s\'"()]+(?:\.png|\.jpg|\.jpeg|\.gif|\.bmp|\.webp))', re.IGNORECASE)

# 读取文件内容
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 查找所有图片 URL
urls = url_pattern.findall(content)
print(f"找到 {len(urls)} 张图片链接")

# 下载函数
def download_image(url, save_dir):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        # 从 URL 里取文件名
        filename = os.path.basename(url.split('?')[0])
        save_path = os.path.join(save_dir, filename)
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"下载成功: {filename}")
    except Exception as e:
        print(f"下载失败: {url}  错误: {e}")

# 批量下载
for url in urls:
    download_image(url, save_directory)
