import os
import ast
import fnmatch

class ProjectScanner:
    def __init__(self, root_path, output_filename="project_structure.txt"):
        self.root_path = os.path.abspath(root_path)
        self.output_file = output_filename
        self.ignore_patterns = self._load_gitignore()
        self.file_handle = None

    def _load_gitignore(self):
        """
        读取 .gitignore 文件并加载默认忽略规则
        """
        patterns = [
            '.git', '.idea', '.vscode', '__pycache__', 
            '*.pyc', '*.pyo', '.DS_Store', 'venv', 'env', '.env'
        ]
        
        gitignore_path = os.path.join(self.root_path, '.gitignore')
        if os.path.exists(gitignore_path):
            try:
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # 简单处理：移除末尾斜杠，适应 fnmatch
                            patterns.append(line.rstrip('/'))
            except Exception as e:
                print(f"⚠️ 读取 .gitignore 失败: {e}")
        return patterns

    def _is_ignored(self, path, is_dir=False):
        """
        判断路径是否应该被忽略 (基于文件名和相对路径)
        """
        name = os.path.basename(path)
        # 获取相对于项目根目录的路径
        rel_path = os.path.relpath(path, self.root_path)
        if rel_path == '.':
            return False

        for pattern in self.ignore_patterns:
            # 1. 匹配文件名/文件夹名 (例如: *.pyc, venv)
            if fnmatch.fnmatch(name, pattern):
                return True
            # 2. 匹配相对路径 (例如: src/temp)
            if fnmatch.fnmatch(rel_path, pattern):
                return True
            # 3. 如果是目录，尝试匹配 pattern/* (处理 dir/* 的情况)
            if is_dir and fnmatch.fnmatch(name, pattern.rstrip('/')):
                return True
        return False

    def _get_definitions(self, file_path):
        """
        解析 Python 文件获取函数和类定义
        """
        definitions = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if not content.strip():
                    return []
                tree = ast.parse(content)
                
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    # 记录函数，并标注是否是私有函数
                    prefix = "🔒 " if node.name.startswith('_') else "⚡ "
                    definitions.append(f"{prefix}def {node.name}")
                elif isinstance(node, ast.ClassDef):
                    definitions.append(f"📦 class {node.name}")
        except Exception:
            # 忽略解析错误（如语法错误的文件）
            pass
        return definitions

    def log(self, message):
        """
        同时打印到控制台和写入文件
        """
        print(message)
        if self.file_handle:
            self.file_handle.write(message + "\n")

    def scan(self):
        print(f"🚀 开始扫描: {self.root_path}")
        print(f"📄 结果将保存至: {self.output_file}\n")
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            self.file_handle = f
            self.log(f"Project Tree for: {os.path.basename(self.root_path)}")
            self.log("=" * 40)
            
            for root, dirs, files in os.walk(self.root_path):
                # 1. 过滤目录 (修改 dirs 列表以阻止 os.walk 进入被忽略的目录)
                # 使用切片 [:] 原地修改列表
                dirs[:] = [d for d in dirs if not self._is_ignored(os.path.join(root, d), is_dir=True)]
                
                # 计算缩进层级
                level = root.replace(self.root_path, '').count(os.sep)
                indent = ' ' * 4 * level
                
                # 打印当前文件夹
                folder_name = os.path.basename(root)
                if root != self.root_path: # 根目录不重复打印
                    self.log(f"{indent}📂 {folder_name}/")
                
                subindent = ' ' * 4 * (level + 1)
                
                # 2. 遍历并过滤文件
                for file in files:
                    full_path = os.path.join(root, file)
                    if self._is_ignored(full_path):
                        continue
                        
                    if file.endswith('.py'):
                        self.log(f"{subindent}📄 {file}")
                        defs = self._get_definitions(full_path)
                        func_indent = ' ' * 4 * (level + 2)
                        for d in defs:
                            self.log(f"{func_indent}└── {d}")
                            
        print(f"\n✅ 扫描完成! 结果已保存至 {self.output_file}")

if __name__ == "__main__":
    # 获取用户输入路径，默认为当前目录
    target = input("请输入项目路径 (回车扫描当前目录): ").strip() or "."
    
    scanner = ProjectScanner(target)
    scanner.scan()
