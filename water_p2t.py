import os
import argparse
from pathspec.gitignore import GitIgnoreSpec

__version__ = "1.2.2"

def build_tree_structure(root_dir: str, ignore_rules: list) -> tuple[list[str], int]:
    """
    构建项目树形结构
    Args:
        root_dir: 项目根目录
        ignore_rules: 忽略规则函数列表
    Returns:
        (树形结构行列表, 文件总数)
    """
    tree = []
    file_count = 0
    
    def add_node(path: str, prefix: str = "", is_last: bool = True):
        nonlocal file_count
        basename = os.path.basename(path)
        relative_path = os.path.relpath(path, root_dir)
        
        # 提前过滤隐藏目录，避免不必要的递归（性能优化）
        if os.path.isdir(path) and basename.startswith("."):
            return
        
        # 应用所有忽略规则
        for rule in ignore_rules:
            if rule(relative_path, path):
                return
        
        if os.path.isdir(path):
            # 处理目录
            tree.append(f"{prefix}{'└── ' if is_last else '├── '}{basename}/")
            new_prefix = prefix + ("    " if is_last else "│   ")
            
            # 获取目录下所有条目并排序（目录在前，文件在后）
            entries = sorted(os.listdir(path))
            dirs = [e for e in entries if os.path.isdir(os.path.join(path, e))]
            files = [e for e in entries if os.path.isfile(os.path.join(path, e))]
            all_entries = dirs + files
            
            for i, entry in enumerate(all_entries):
                entry_path = os.path.join(path, entry)
                add_node(entry_path, new_prefix, i == len(all_entries) - 1)
        else:
            # 处理文件
            tree.append(f"{prefix}{'└── ' if is_last else '├── '}{basename}")
            file_count += 1
    
    # 从根目录开始构建
    root_name = os.path.basename(root_dir) or root_dir  # 修复根目录显示问题
    tree.append(root_name + "/")
    entries = sorted(os.listdir(root_dir))
    dirs = [e for e in entries if os.path.isdir(os.path.join(root_dir, e))]
    files = [e for e in entries if os.path.isfile(os.path.join(root_dir, e))]
    all_entries = dirs + files
    
    for i, entry in enumerate(all_entries):
        entry_path = os.path.join(root_dir, entry)
        add_node(entry_path, "", i == len(all_entries) - 1)
    
    return tree, file_count

def water_p2t(
    root_dir: str = None, 
    output_file: str = None,
    remove_empty_lines: bool = True,
    include_readme: bool = False,
    struct_only: bool = False
):
    """
    Water_p2t - 项目代码合并工具
    递归读取项目文件 + 自动忽略所有隐藏文件 + 遵循.gitignore过滤 + 自动去除空行 + 合并为TXT
    
    Args:
        root_dir: 项目根目录，默认使用终端当前工作目录
        output_file: 输出文件路径，普通模式默认"项目代码合集.txt"，结构模式默认"项目代码结构.txt"
        remove_empty_lines: 是否自动去除所有空行，默认开启
        include_readme: 是否包含根目录下的README文件，默认关闭
        struct_only: 只输出项目结构，不包含文件内容，默认关闭
    """
    # 核心：默认使用终端当前工作目录
    if root_dir is None:
        root_dir = os.getcwd()
    
    # 动态设置默认输出文件名
    if output_file is None:
        output_file = "项目代码结构.txt" if struct_only else "项目代码合集.txt"
    
    # 转换为绝对路径，避免路径比较错误
    root_dir = os.path.abspath(root_dir)
    output_abs_path = os.path.abspath(output_file)
    
    # 配置项
    TARGET_EXTENSIONS = {".py", ".json", ".yaml", ".yml", ".md", ".txt", ".toml", ".ini"}
    file_count = 0
    gitignore_spec = None

    # 加载 .gitignore 规则（即使是隐藏文件也读取，不影响输出）
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

    # 定义通用忽略规则
    def ignore_output_file(relative_path: str, full_path: str) -> bool:
        return full_path == output_abs_path
    
    def ignore_root_readme(relative_path: str, full_path: str) -> bool:
        if include_readme:
            return False
        dir_path = os.path.dirname(full_path)
        file_name = os.path.basename(full_path)
        return dir_path == root_dir and file_name.lower().startswith("readme.")
    
    def ignore_gitignore(relative_path: str, full_path: str) -> bool:
        if not gitignore_spec:
            return False
        return gitignore_spec.match_file(relative_path)
    
    def ignore_unsupported_extension(relative_path: str, full_path: str) -> bool:
        if os.path.isdir(full_path):
            return False
        file_ext = os.path.splitext(full_path)[-1].lower()
        return file_ext not in TARGET_EXTENSIONS
    
    # 全局递归忽略所有隐藏文件/文件夹（包括.gitignore）
    def ignore_hidden_files(relative_path: str, full_path: str) -> bool:
        basename = os.path.basename(full_path)
        return basename.startswith(".")
    
    ignore_rules = [
        ignore_hidden_files,  # 放在最前面，优先过滤所有隐藏文件
        ignore_output_file,
        ignore_root_readme,
        ignore_gitignore,
        ignore_unsupported_extension
    ]

    # 写入输出文件
    with open(output_file, "w", encoding="utf-8") as out_f:
        if struct_only:
            # 只输出项目结构
            print("🔍 正在生成项目结构...")
            tree_lines, file_count = build_tree_structure(root_dir, ignore_rules)
            
            # 写入文件
            out_f.write("=" * 50 + "\n")
            out_f.write("【项目结构】\n")
            out_f.write("=" * 50 + "\n")
            for line in tree_lines:
                out_f.write(line + "\n")
            
            # 打印到终端
            print("\n" + "=" * 50)
            print("【项目结构】")
            print("=" * 50)
            for line in tree_lines:
                print(line)
            
        else:
            # 正常合并文件内容
            for dir_path, _, file_names in os.walk(root_dir):
                dir_path = os.path.abspath(dir_path)
                dir_name = os.path.basename(dir_path)
                
                # 提前过滤隐藏目录，避免进入遍历（大幅优化性能）
                if dir_name.startswith("."):
                    continue
                
                for file_name in file_names:
                    # 提前过滤隐藏文件（与ignore_rules保持一致）
                    if file_name.startswith("."):
                        continue
                    
                    file_ext = os.path.splitext(file_name)[-1].lower()
                    if file_ext not in TARGET_EXTENSIONS:
                        continue

                    # 生成路径
                    full_path = os.path.join(dir_path, file_name)
                    relative_path = os.path.relpath(full_path, root_dir)

                    # 应用剩余忽略规则
                    if ignore_output_file(relative_path, full_path):
                        continue
                    if ignore_root_readme(relative_path, full_path):
                        print(f"🚫 已忽略根目录README：{relative_path}")
                        continue
                    if ignore_gitignore(relative_path, full_path):
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

    print(f"\n🎉 Water_p2t v{__version__} 处理完成！")
    if struct_only:
        print(f"📊 共扫描 {file_count} 个文件，生成项目结构")
    else:
        print(f"📄 共合并 {file_count} 个文件")
        if remove_empty_lines:
            print("ℹ️  已自动去除所有空行")
        if not include_readme:
            print("ℹ️  已自动忽略根目录README文件（使用--include-readme可包含）")
    print("ℹ️  已自动忽略所有隐藏文件和文件夹（仅读取.gitignore规则）")
    print(f"📄 输出文件：{output_abs_path}")

def main():
    """命令行入口函数（全小写调用：water_p2t）"""
    parser = argparse.ArgumentParser(
        description=f"Water_p2t v{__version__} - 项目代码合并工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
  water_p2t                    # 处理当前目录，输出到"项目代码合集.txt"
  water_p2t ./my_project       # 处理指定项目目录
  water_p2t -o 代码汇总.txt    # 指定输出文件名
  water_p2t --keep-empty       # 保留空行
  water_p2t --include-readme   # 包含根目录README文件
  water_p2t --struct           # 只输出项目结构，默认输出到"项目代码结构.txt"
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
        default=None,
        help="输出文件路径（普通模式默认：项目代码合集.txt，结构模式默认：项目代码结构.txt）"
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
        "--struct", 
        action="store_true",
        help="只输出项目结构，不包含文件内容（默认：关闭）"
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
        include_readme=args.include_readme,
        struct_only=args.struct
    )

if __name__ == "__main__":
    main()