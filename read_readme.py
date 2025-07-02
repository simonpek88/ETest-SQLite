def read_file_line_by_line(file_path):
    """按行读取文件并返回包含每行内容的列表"""
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    return lines


# 读取README.md文件
readme_path = "README.md"
readme_content = read_file_line_by_line(readme_path)

# 打印前5行作为示例
for line in readme_content[:5]:
    print(line.strip())