"""
整理精灵-文件自动整理工具
作者: PhiloKun
个人网站: www.zhangkunzhe.cn
"""

import os
import shutil
import datetime
import json
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, messagebox
import threading

# 尝试导入拖放支持库
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DRAG_DROP_SUPPORT = True
except ImportError:
    DRAG_DROP_SUPPORT = False

def organize_files(directory, output_callback=None):
    """根据文件类型整理文件到不同文件夹"""
    # 定义文件类型和对应的文件夹
    file_types = {
        '图片': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.tiff', '.tif', '.raw', '.heic', '.ico', '.psd', '.ai', '.eps', '.cr2', '.nef', '.arw', '.dng'],
        '文档': ['.doc', '.docx', '.pdf', '.txt', '.rtf', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp', '.csv', '.md', '.epub', '.mobi', '.azw', '.azw3', '.djvu', '.xps', '.pages', '.numbers', '.key', '.tex', '.log'],
        '视频': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg', '.3gp', '.m2ts', '.vob', '.ts', '.mts', '.asf', '.rm', '.rmvb', '.ogv', '.divx'],
        '音频': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.opus', '.alac', '.aiff', '.ape', '.mid', '.midi', '.amr', '.ac3', '.dts', '.ra', '.mka', '.mpc', '.gsm'],
        '压缩文件': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso', '.tgz', '.tbz2', '.lzma', '.cab', '.jar', '.war', '.bz', '.lz', '.lzh', '.arj', '.z', '.deb', '.rpm', '.pkg'],
        '代码': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h', '.json', '.xml', '.php', '.rb', '.swift', '.kt', '.go', '.rs', '.ts', '.dart', '.lua', '.pl', '.sh', '.bat', '.ps1', '.sql', '.yaml', '.yml', '.toml', '.ini', '.config', '.jsx', '.tsx', '.vue', '.cs', '.vb', '.scala', '.groovy', '.coffee', '.scss', '.sass', '.less'],
        '可执行文件': ['.exe', '.msi', '.app', '.dmg', '.apk', '.bin', '.com', '.run', '.msc', '.action', '.command', '.gadget', '.vb', '.vbs', '.vbe', '.jse', '.ws', '.wsf', '.wsh', '.scr'],
        '字体': ['.ttf', '.otf', '.woff', '.woff2', '.eot', '.pfb', '.pfm', '.fon', '.bdf', '.fnt', '.pfa', '.afm', '.pcf'],
        '3D模型': ['.obj', '.stl', '.fbx', '.blend', '.dae', '.3ds', '.max', '.c4d', '.mb', '.ma', '.lwo', '.lws', '.skp', '.ply', '.x3d', '.gltf', '.glb', '.vrml', '.x'],
        '设计文件': ['.psd', '.ai', '.indd', '.xd', '.sketch', '.fig', '.xcf', '.cdr', '.sai', '.psb', '.afdesign', '.afphoto', '.aep', '.prproj', '.aepx', '.ppj', '.drw', '.dgn', '.dwg', '.dxf'],
        '数据库': ['.db', '.sqlite', '.sqlite3', '.mdb', '.accdb', '.dbf', '.sql', '.bak', '.csv', '.tsv', '.dat', '.xml', '.json', '.bson']
    }
    
    # 用于记录移动操作的列表
    move_records = []
    
    # 确保目录存在
    directory = os.path.abspath(directory)
    if not os.path.exists(directory):
        message = f"目录 '{directory}' 不存在！"
        if output_callback:
            output_callback(message)
        else:
            print(message)
        return None
    
    # 获取目录下的所有文件
    all_files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    total_files = len(all_files)
    
    # 先统计每种类型文件的数量，只为有文件的类型创建文件夹
    file_type_counts = {folder: 0 for folder in file_types}
    other_count = 0
    
    for filename in all_files:
        # 跳过当前脚本和历史记录文件
        if filename == os.path.basename(__file__) or filename == ".organize_history.json":
            continue
        
        # 获取文件扩展名
        _, extension = os.path.splitext(filename)
        extension = extension.lower()
        
        # 统计各类型文件数量
        file_categorized = False
        for folder, extensions in file_types.items():
            if extension in extensions:
                file_type_counts[folder] += 1
                file_categorized = True
                break
        
        # 如果不属于任何类别，归为"其他"
        if not file_categorized:
            other_count += 1
    
    # 只为有文件的类型创建文件夹
    created_folders = []  # 记录创建的分类文件夹
    folders_map = {}  # 用于映射文件类型到文件夹路径
    
    for folder, count in file_type_counts.items():
        if count > 0:
            folder_path = os.path.join(directory, folder)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                created_folders.append(folder_path)
                message = f"创建文件夹: {folder} (包含 {count} 个文件)"
                if output_callback:
                    output_callback(message)
                else:
                    print(message)
            folders_map[folder] = folder_path
    
    # 如果有"其他"类型的文件，创建"其他"文件夹
    other_folder = None
    if other_count > 0:
        other_folder = os.path.join(directory, "其他")
        if not os.path.exists(other_folder):
            os.makedirs(other_folder)
            created_folders.append(other_folder)
            message = f"创建文件夹: 其他 (包含 {other_count} 个文件)"
            if output_callback:
                output_callback(message)
            else:
                print(message)
    
    # 整理文件
    files_moved = 0
    for i, filename in enumerate(all_files):
        file_path = os.path.join(directory, filename)
        
        # 跳过当前脚本和历史记录文件
        if filename == os.path.basename(__file__) or filename == ".organize_history.json":
            continue
        
        # 获取文件扩展名
        _, extension = os.path.splitext(filename)
        extension = extension.lower()
        
        # 确定目标文件夹
        target_folder = other_folder
        for folder, extensions in file_types.items():
            if extension in extensions:
                # 使用映射获取文件夹路径，确保文件夹已创建
                if folder in folders_map:
                    target_folder = folders_map[folder]
                    break
        
        # 如果没有对应的目标文件夹（可能没有"其他"类别的文件），则跳过
        if target_folder is None:
            continue
        
        # 移动文件
        target_path = os.path.join(target_folder, filename)
        
        # 如果目标路径已存在同名文件，添加时间戳
        new_filename = filename
        if os.path.exists(target_path):
            name, ext = os.path.splitext(filename)
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            new_filename = f"{name}_{timestamp}{ext}"
            target_path = os.path.join(target_folder, new_filename)
        
        # 移动前记录文件原位置和目标位置
        move_record = {
            "original_path": file_path,
            "target_path": target_path,
            "original_filename": filename,
            "new_filename": new_filename
        }
        move_records.append(move_record)
        
        # 移动文件
        shutil.move(file_path, target_path)
        files_moved += 1
        
        message = f"移动文件: {filename} -> {os.path.relpath(target_path, directory)}"
        if output_callback:
            # 更新进度
            progress = (i + 1) / total_files * 100
            output_callback(message, progress)
        else:
            print(message)
    
    # 保存整理记录到隐藏文件
    if move_records:
        history_file = os.path.join(directory, ".organize_history.json")
        try:
            # 读取已有历史记录
            existing_records = []
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    existing_records = json.load(f)
            
            # 添加时间戳到本次记录
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            record_entry = {
                "timestamp": timestamp,
                "records": move_records,
                "created_folders": created_folders  # 记录创建的文件夹，用于还原时删除
            }
            
            # 将新记录添加到历史记录开头
            existing_records.insert(0, record_entry)
            
            # 保存更新后的历史记录
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(existing_records, f, ensure_ascii=False, indent=2)
            
            message = f"整理记录已保存到: {history_file}"
            if output_callback:
                output_callback(message)
            else:
                print(message)
        except Exception as e:
            message = f"保存整理记录时发生错误: {str(e)}"
            if output_callback:
                output_callback(message)
            else:
                print(message)
    
    message = f"\n整理完成! 共移动了 {files_moved} 个文件。"
    if output_callback:
        output_callback(message)
    else:
        print(message)
    
    return move_records

def restore_files(directory, history_index=0, output_callback=None):
    """还原文件到原始位置"""
    history_file = os.path.join(directory, ".organize_history.json")
    
    if not os.path.exists(history_file):
        message = "找不到整理历史记录，无法还原文件。"
        if output_callback:
            output_callback(message)
        else:
            print(message)
        return False
    
    try:
        # 读取历史记录
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        if not history or history_index >= len(history):
            message = "找不到指定的整理记录，无法还原文件。"
            if output_callback:
                output_callback(message)
            else:
                print(message)
            return False
        
        # 获取指定的整理记录
        selected_history = history[history_index]
        timestamp = selected_history["timestamp"]
        records = selected_history["records"]
        
        # 获取该记录创建的文件夹列表，如果不存在则使用默认分类文件夹
        created_folders = selected_history.get("created_folders", [])
        if not created_folders:
            # 如果历史记录中没有保存创建的文件夹，使用默认的分类文件夹
            default_folders = ['图片', '文档', '视频', '音频', '压缩文件', '代码', '可执行文件', '字体', '3D模型', '设计文件', '数据库', '其他']
            created_folders = [os.path.join(directory, folder) for folder in default_folders]
        
        message = f"开始还原 {timestamp} 的整理操作，共有 {len(records)} 个文件需要处理..."
        if output_callback:
            output_callback(message)
        else:
            print(message)
        
        # 逆序处理记录，以便先还原最后移动的文件
        records.reverse()
        
        # 开始还原文件
        restored_count = 0
        failed_count = 0
        
        for i, record in enumerate(records):
            original_path = record["original_path"]
            target_path = record["target_path"]
            
            # 如果目标文件仍然存在
            if os.path.exists(target_path):
                # 确保原始路径的目录存在
                original_dir = os.path.dirname(original_path)
                if not os.path.exists(original_dir):
                    os.makedirs(original_dir)
                
                # 如果原始位置已有同名文件，添加时间戳
                if os.path.exists(original_path):
                    original_dir = os.path.dirname(original_path)
                    original_filename = os.path.basename(original_path)
                    name, ext = os.path.splitext(original_filename)
                    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                    new_original_path = os.path.join(original_dir, f"{name}_restored_{timestamp}{ext}")
                    original_path = new_original_path
                
                # 移动文件回原位置
                try:
                    shutil.move(target_path, original_path)
                    restored_count += 1
                    
                    message = f"还原文件: {os.path.basename(target_path)} -> {os.path.basename(original_path)}"
                    if output_callback:
                        progress = (i + 1) / len(records) * 100
                        output_callback(message, progress)
                    else:
                        print(message)
                except Exception as e:
                    failed_count += 1
                    message = f"还原文件失败: {os.path.basename(target_path)} - {str(e)}"
                    if output_callback:
                        output_callback(message)
                    else:
                        print(message)
            else:
                failed_count += 1
                message = f"文件不存在，无法还原: {os.path.basename(target_path)}"
                if output_callback:
                    output_callback(message)
                else:
                    print(message)
        
        # 删除空的分类文件夹
        folders_removed = 0
        for folder_path in created_folders:
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                # 检查文件夹是否为空
                if not os.listdir(folder_path):
                    try:
                        os.rmdir(folder_path)
                        folders_removed += 1
                        message = f"删除空文件夹: {os.path.basename(folder_path)}"
                        if output_callback:
                            output_callback(message)
                        else:
                            print(message)
                    except Exception as e:
                        message = f"删除文件夹失败: {os.path.basename(folder_path)} - {str(e)}"
                        if output_callback:
                            output_callback(message)
                        else:
                            print(message)
                else:
                    message = f"文件夹非空，保留: {os.path.basename(folder_path)}"
                    if output_callback:
                        output_callback(message)
                    else:
                        print(message)
        
        # 更新历史记录，删除已还原的记录
        if restored_count > 0:
            del history[history_index]
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        
        # 完成还原
        message = f"\n还原完成! 成功还原 {restored_count} 个文件，失败 {failed_count} 个文件，删除 {folders_removed} 个空文件夹。"
        if output_callback:
            output_callback(message)
        else:
            print(message)
        
        return True
    
    except Exception as e:
        message = f"还原文件过程中发生错误: {str(e)}"
        if output_callback:
            output_callback(message)
        else:
            print(message)
        return False

def get_organize_history(directory):
    """获取整理历史记录"""
    history_file = os.path.join(directory, ".organize_history.json")
    if not os.path.exists(history_file):
        return []
    
    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
        return history
    except:
        return []

class FileOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("整理精灵-文件自动整理工具")
        self.root.geometry("700x500")
        self.root.resizable(True, True)
        
        # 设置应用图标
        try:
            # 使用ICO文件作为程序图标
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "file_organizer.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"加载图标出错: {e}")
        
        # 设置样式
        self.style = ttk.Style()
        self.style.configure("TButton", font=("微软雅黑", 10))
        self.style.configure("TLabel", font=("微软雅黑", 10))
        self.style.configure("TEntry", font=("微软雅黑", 10))
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建顶部信息标签
        if DRAG_DROP_SUPPORT:
            drag_tip = ttk.Label(self.main_frame, text="提示: 您可以直接将文件夹拖放到此窗口中进行整理", foreground="blue")
            drag_tip.pack(fill=tk.X, pady=(0, 10))
        
        # 创建目录选择框架
        self.dir_frame = ttk.Frame(self.main_frame)
        self.dir_frame.pack(fill=tk.X, pady=10)
        
        self.dir_label = ttk.Label(self.dir_frame, text="选择要整理的目录:")
        self.dir_label.pack(side=tk.LEFT, padx=5)
        
        self.dir_var = tk.StringVar()
        self.dir_entry = ttk.Entry(self.dir_frame, textvariable=self.dir_var, width=50)
        self.dir_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 为Entry添加拖放支持
        if DRAG_DROP_SUPPORT:
            self.dir_entry.drop_target_register(DND_FILES)
            self.dir_entry.dnd_bind('<<Drop>>', self.on_drop)
        
        self.browse_button = ttk.Button(self.dir_frame, text="浏览...", command=self.browse_directory)
        self.browse_button.pack(side=tk.LEFT, padx=5)
        
        # 创建操作按钮框架
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=10)
        
        self.organize_button = ttk.Button(self.button_frame, text="开始整理", command=self.start_organizing)
        self.organize_button.pack(side=tk.LEFT, padx=5)
        
        self.restore_button = ttk.Button(self.button_frame, text="还原文件", command=self.show_restore_dialog)
        self.restore_button.pack(side=tk.LEFT, padx=5)
        
        # 添加关于按钮
        self.about_button = ttk.Button(self.button_frame, text="关于", command=self.show_about_dialog)
        self.about_button.pack(side=tk.RIGHT, padx=5)
        
        # 创建进度条
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(self.main_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(fill=tk.X, pady=10)
        
        # 创建输出文本区域
        self.output_frame = ttk.LabelFrame(self.main_frame, text="整理进度")
        self.output_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.output_text = scrolledtext.ScrolledText(self.output_frame, wrap=tk.WORD, width=80, height=20)
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 添加底部作者信息
        self.author_label = ttk.Label(self.main_frame, text="作者: PhiloKun | www.zhangkunzhe.cn", foreground="gray")
        self.author_label.pack(side=tk.BOTTOM, pady=(5, 0))
        
        # 为整个窗口添加拖放支持
        if DRAG_DROP_SUPPORT:
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.on_drop)
        
        # 设置默认目录为当前目录
        self.dir_var.set(os.getcwd())
        
        # 设置初始状态
        self.is_operating = False
        self.last_organize_records = None
        
        # 检查是否有整理历史
        self.check_restore_availability()
    
    def on_drop(self, event):
        """处理文件/文件夹拖放事件"""
        # 获取拖放的文件或文件夹
        dropped_path = event.data
        
        # 根据系统清理路径字符串
        if os.name == 'nt':  # Windows
            # 移除花括号，处理引号和多个文件的情况
            dropped_path = dropped_path.replace('{', '').replace('}', '')
            # 移除首尾的引号(如果有)
            if dropped_path.startswith('"') and dropped_path.endswith('"'):
                dropped_path = dropped_path[1:-1]
        else:  # Unix/Linux/Mac
            # 处理文件 URL 格式(如果是)
            if dropped_path.startswith('file:///'):
                dropped_path = dropped_path[7:]  # 移除 'file://'
                dropped_path = dropped_path.replace('%20', ' ')  # 替换URL编码的空格
        
        # 如果是文件夹，则设置为目录
        if os.path.isdir(dropped_path):
            self.dir_var.set(dropped_path)
            self.check_restore_availability()
        else:
            messagebox.showinfo("提示", "请拖放文件夹，而不是文件。")
    
    def browse_directory(self):
        """打开目录选择对话框"""
        directory = filedialog.askdirectory(initialdir=self.dir_var.get())
        if directory:
            self.dir_var.set(directory)
            # 检查是否有整理历史
            self.check_restore_availability()
    
    def check_restore_availability(self):
        """检查是否有整理历史记录可供还原"""
        directory = self.dir_var.get()
        if directory and os.path.exists(directory):
            history = get_organize_history(directory)
            if history:
                self.restore_button.config(state="normal")
            else:
                self.restore_button.config(state="disabled")
        else:
            self.restore_button.config(state="disabled")
    
    def log_message(self, message, progress=None):
        """将消息添加到输出区域并更新进度条"""
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)  # 自动滚动到底部
        
        if progress is not None:
            self.progress_var.set(progress)
            
        # 更新UI
        self.root.update_idletasks()
    
    def start_organizing(self):
        """开始整理文件的处理"""
        if self.is_operating:
            return
        
        directory = self.dir_var.get()
        if not directory:
            self.log_message("请选择一个有效的目录！")
            return
        
        # 确认对话框
        if not tk.messagebox.askyesno("确认", f"确定要整理目录: {directory} 吗？"):
            return
        
        # 清空输出文本
        self.output_text.delete(1.0, tk.END)
        self.progress_var.set(0)
        
        # 禁用按钮，防止重复点击
        self.organize_button.config(state="disabled")
        self.browse_button.config(state="disabled")
        self.restore_button.config(state="disabled")
        self.is_operating = True
        
        # 在新线程中运行整理任务
        self.log_message(f"开始整理目录: {directory}")
        threading.Thread(target=self.organize_thread, args=(directory,), daemon=True).start()
    
    def organize_thread(self, directory):
        """在单独的线程中运行整理任务"""
        try:
            self.last_organize_records = organize_files(directory, self.log_message)
        except Exception as e:
            self.log_message(f"发生错误: {str(e)}")
        finally:
            # 恢复按钮状态
            self.root.after(0, self.reset_ui)
    
    def show_restore_dialog(self):
        """显示还原对话框"""
        directory = self.dir_var.get()
        if not directory or not os.path.exists(directory):
            tk.messagebox.showwarning("警告", "请先选择一个有效的目录！")
            return
        
        # 获取整理历史记录
        history = get_organize_history(directory)
        if not history:
            tk.messagebox.showinfo("提示", "未找到整理历史记录，无法还原文件。")
            return
        
        # 创建还原对话框
        restore_dialog = tk.Toplevel(self.root)
        restore_dialog.title("选择要还原的整理记录")
        restore_dialog.geometry("500x300")
        restore_dialog.transient(self.root)
        restore_dialog.grab_set()
        
        # 创建列表框
        frame = ttk.Frame(restore_dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        label = ttk.Label(frame, text="请选择要还原的整理记录:")
        label.pack(anchor=tk.W, pady=5)
        
        history_list = tk.Listbox(frame, height=10, width=70)
        history_list.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(history_list, orient="vertical", command=history_list.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        history_list.config(yscrollcommand=scrollbar.set)
        
        # 填充历史记录
        for i, record in enumerate(history):
            timestamp = record["timestamp"]
            file_count = len(record["records"])
            history_list.insert(tk.END, f"{timestamp} - 整理了 {file_count} 个文件")
        
        # 默认选择第一项
        if history_list.size() > 0:
            history_list.selection_set(0)
        
        # 按钮框架
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        def on_restore():
            selection = history_list.curselection()
            if not selection:
                tk.messagebox.showwarning("警告", "请选择要还原的记录！")
                return
            
            index = selection[0]
            timestamp = history[index]["timestamp"]
            file_count = len(history[index]["records"])
            
            if tk.messagebox.askyesno("确认还原", f"确定要还原 {timestamp} 的整理操作吗？\n这将移动 {file_count} 个文件回原位置并删除空的分类文件夹。"):
                restore_dialog.destroy()
                self.start_restore(index)
        
        restore_btn = ttk.Button(button_frame, text="还原", command=on_restore)
        restore_btn.pack(side=tk.RIGHT, padx=5)
        
        cancel_btn = ttk.Button(button_frame, text="取消", command=restore_dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=5)
    
    def start_restore(self, history_index):
        """开始还原文件"""
        if self.is_operating:
            return
        
        directory = self.dir_var.get()
        
        # 清空输出文本
        self.output_text.delete(1.0, tk.END)
        self.progress_var.set(0)
        
        # 禁用按钮，防止重复点击
        self.organize_button.config(state="disabled")
        self.browse_button.config(state="disabled")
        self.restore_button.config(state="disabled")
        self.is_operating = True
        
        # 在新线程中运行还原任务
        self.log_message(f"开始还原文件...")
        threading.Thread(target=self.restore_thread, args=(directory, history_index), daemon=True).start()
    
    def restore_thread(self, directory, history_index):
        """在单独的线程中运行还原任务"""
        try:
            restore_files(directory, history_index, self.log_message)
        except Exception as e:
            self.log_message(f"发生错误: {str(e)}")
        finally:
            # 恢复按钮状态
            self.root.after(0, self.reset_ui)
    
    def reset_ui(self):
        """重置UI状态"""
        self.organize_button.config(state="normal")
        self.browse_button.config(state="normal")
        self.is_operating = False
        self.progress_var.set(100)  # 确保进度条显示完成
        
        # 检查是否有整理历史记录
        self.check_restore_availability()
    
    def show_about_dialog(self):
        """显示关于对话框"""
        about_window = tk.Toplevel(self.root)
        about_window.title("关于整理精灵-文件自动整理工具")
        about_window.geometry("400x200")
        about_window.resizable(False, False)
        about_window.transient(self.root)  # 设置为主窗口的子窗口
        about_window.grab_set()  # 模态对话框
        
        # 居中对话框内容
        frame = ttk.Frame(about_window, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title = ttk.Label(frame, text="整理精灵-文件自动整理工具", font=("微软雅黑", 16, "bold"))
        title.pack(pady=(0, 10))
        
        # 版本信息
        version = ttk.Label(frame, text="版本 1.0")
        version.pack()
        
        # 作者信息
        author = ttk.Label(frame, text="作者: PhiloKun")
        author.pack()
        
        # 网站链接
        website = ttk.Label(frame, text="作者网站: www.zhangkunzhe.cn", foreground="blue", cursor="hand2")
        website.pack()
        website.bind("<Button-1>", lambda e: self.open_website())
        
        # 版权信息
        copyright_info = ttk.Label(frame, text="© 2025 保留所有权利")
        copyright_info.pack(pady=(10, 0))
        
        # 关闭按钮
        close_btn = ttk.Button(frame, text="关闭", command=about_window.destroy)
        close_btn.pack(pady=(10, 0))
    
    def open_website(self):
        """打开作者网站"""
        try:
            import webbrowser
            webbrowser.open("http://www.zhangkunzhe.cn")
        except Exception as e:
            tk.messagebox.showerror("错误", f"无法打开网站: {str(e)}")

def main():
    # 检查是否支持拖放功能
    if DRAG_DROP_SUPPORT:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    
    app = FileOrganizerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 