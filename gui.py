import tkinter as tk
import subprocess
import sys
import os

def run_main_script():
    """
    运行主脚本 main.py。
    使用 subprocess.Popen 在新的控制台窗口中运行，以避免阻塞 GUI。
    """
    try:
        # 获取当前脚本所在的目录，并构建 main.py 的绝对路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        main_script_path = os.path.join(current_dir, 'main.py')

        if not os.path.exists(main_script_path):
             # 如果在当前目录找不到，弹出错误提示
             tk.messagebox.showerror("错误", f"无法找到主脚本 'main.py' 在路径: {main_script_path}")
             return

        # 使用 Popen 启动一个新进程，这样它就不会阻塞 GUI。
        # 根据操作系统使用不同的方式在新窗口中启动。
        if sys.platform == "win32":
            subprocess.Popen([sys.executable, main_script_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
        elif sys.platform == "darwin": # macOS
            subprocess.Popen(['open', '-a', 'Terminal', sys.executable, main_script_path])
        else: # Linux
            try:
                subprocess.Popen(['x-terminal-emulator', '-e', sys.executable, main_script_path])
            except FileNotFoundError:
                tk.messagebox.showwarning("警告", "无法找到 'x-terminal-emulator'。请在终端中手动运行 'python3 main.py'。")

    except Exception as e:
        tk.messagebox.showerror("错误", f"启动 'main.py' 时出错: {e}")

def create_gui():
    """
    创建并运行 GUI 窗口。
    """
    window = tk.Tk()
    window.title("小说生成器")

    # 设置窗口大小和位置
    window.geometry("320x180")
    # 将窗口居中
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')


    # 创建一个框架来容纳内容
    frame = tk.Frame(window, padx=20, pady=20)
    frame.pack(expand=True, fill=tk.BOTH)

    # 添加标签
    label = tk.Label(frame, text="点击按钮启动小说生成器控制台", wraplength=280)
    label.pack(pady=(0, 15))

    # 创建按钮
    start_button = tk.Button(frame, text="开始生成", command=run_main_script, width=15, height=2)
    start_button.pack()

    # 运行主循环
    window.mainloop()

if __name__ == "__main__":
    create_gui()