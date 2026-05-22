import os
import argparse
from pathspec.gitignore import GitIgnoreSpec

__version__ = "1.1.0"  # 版本号升级

def water_p2t(
    root_dir: str = None, 
    output_file: str = "项目代码合集.txt",
    remove_empty_lines: bool = True,
    include_readme: bool = False  # 新增：默认不包含根目录README
):
    """
    Water_p2t - 项目代码合并工具
    递归读取项目文件 + 遵循.gitignore过滤 + 自动去除空行 + 合并为TXT
    
    Args:
        root_dir: 项目根目录，默认使用终端当前工作目录
        output_file: 输出文件路径，默认在当前工作目录生成"项目代码合集.txt"
        remove_empty_lines: 是否自动去除所有空行，默认开启
        include_readme: 是否包含根目录下的README文件，默认关闭
    """
    # 核心：默认使用终端当前工作目录
    if root_dir is None:
        root_dir = os.getcwd()
    
    # 转换为绝对路径，避免路径比较错误
    root_dir = os.path.abspath(root_dir)
    output_abs_path = os.path.abspath(output_file)
    
    # 配置项
    TARGET_EXTENSIONS = {".py", ".json", ".yaml", ".yml", ".md", ".txt", ".toml", ".ini"}
    file_count = 0
    gitignore_spec = None

    # 加载 .gitignore 规则
    gitignore_path = os.path.join(root_dir, ".gitignore")
    if os.path.exists(gitignore_path):
        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
            gitignore_spec = GitIgnoreSpec.from_lines(lines)
            print(f"✅ 已加载 .gitignore 规则")
        except Exception as e:
            print(f"⚠️  .gitignore 读取失败，跳过忽略规则：{str(e)}")
    else:
        print("ℹ️  未检测到 .gitignore 文件")

    # 写入合并文件
    with open(output_file, "w", encoding="utf-8") as out_f:
        for dir_path, _, file_names in os.walk(root_dir):
            dir_path = os.path.abspath(dir_path)
            
            for file_name in file_names:
                file_ext = os.path.splitext(file_name)[-1].lower()
                if file_ext not in TARGET_EXTENSIONS:
                    continue

                # 生成路径
                full_path = os.path.join(dir_path, file_name)
                relative_path = os.path.relpath(full_path, root_dir)

                # 1. 排除输出文件本身（关键bug修复）
                if full_path == output_abs_path:
                    continue

                # 2. 默认忽略根目录下所有README文件（不区分大小写）
                if not include_readme and dir_path == root_dir and file_name.lower().startswith("readme."):
                    print(f"🚫 已忽略根目录README：{relative_path}")
                    continue

                # 3. gitignore 过滤
                if gitignore_spec and gitignore_spec.match_file(relative_path):
                    print(f"🚫 已忽略：{relative_path}")
                    continue

                try:
                    # 读取文件内容
                    with open(full_path, "r", encoding="utf-8") as in_f:
                        content = in_f.read()

                    # 自动去除空行
                    if remove_empty_lines:
                        raw_lines = content.splitlines()
                        cleaned_lines = [line for line in raw_lines if line.strip() != ""]
                        cleaned_content = "\n".join(cleaned_lines)
                    else:
                        cleaned_content = content

                    # 写入处理后的内容
                    out_f.write("=" * 50 + "\n")
                    out_f.write(f"【文件路径】{relative_path}\n")
                    out_f.write("=" * 50 + "\n")
                    out_f.write(cleaned_content + "\n\n")

                    file_count += 1
                    print(f"已处理：{relative_path}")

                except Exception as e:
                    print(f"❌ 读取失败：{relative_path}，原因：{str(e)}")

    print(f"\n🎉 Water_p2t v{__version__} 处理完成！共合并 {file_count} 个文件")
    if remove_empty_lines:
        print("ℹ️  已自动去除所有空行")
    if not include_readme:
        print("ℹ️  已自动忽略根目录README文件（使用--include-readme可包含）")
    print(f"📄 输出文件：{output_abs_path}")

def main():
    """命令行入口函数（全小写调用：water_p2t）"""
    parser = argparse.ArgumentParser(
        description=f"Water_p2t v{__version__} - 项目代码合并工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
  water_p2t                    # 处理当前目录，自动忽略根目录README
  water_p2t ./my_project       # 处理指定项目目录
  water_p2t -o 代码汇总.txt    # 指定输出文件名
  water_p2t --keep-empty       # 保留空行
  water_p2t --include-readme   # 包含根目录README文件
        """
    )
    
    parser.add_argument(
        "root_dir", 
        nargs="?", 
        default=None,
        help="项目根目录（默认：终端当前工作目录）"
    )
    
    parser.add_argument(
        "-o", "--output", 
        default="项目代码合集.txt",
        help="输出文件路径（默认：项目代码合集.txt）"
    )
    
    parser.add_argument(
        "--keep-empty", 
        action="store_true",
        help="保留文件中的空行（默认：自动去除）"
    )
    
    parser.add_argument(
        "--include-readme", 
        action="store_true",
        help="包含根目录下的README文件（默认：自动忽略）"
    )
    
    parser.add_argument(
        "-v", "--version", 
        action="version",
        version=f"Water_p2t v{__version__}"
    )
    
    args = parser.parse_args()
    
    water_p2t(
        root_dir=args.root_dir,
        output_file=args.output,
        remove_empty_lines=not args.keep_empty,
        include_readme=args.include_readme
    )

if __name__ == "__main__":
    main()