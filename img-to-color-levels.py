import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from typing import List, Tuple, Optional
import os
import json
from PIL import Image, ImageTk
from tkinterdnd2 import TkinterDnD, DND_FILES  # 修改导入方式

class GradientGenerator:
    def __init__(self):
        # 使用TkinterDnD.Tk()来创建支持拖放的窗口
        self.window = TkinterDnD.Tk()
        self.window.title("图片生成色阶网格图 by Oahc")
        self.window.geometry("1200x700")  # 增加窗口大小以容纳预览
        
        # 创建左右分栏
        left_frame = ttk.Frame(self.window, padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        right_frame = ttk.Frame(self.window, padding="10")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 左侧：原有的控制界面
        self.setup_control_panel(left_frame)
        
        # 右侧：预览区域
        self.setup_preview_panel(right_frame)
        
        self.selected_files = []
        
    def setup_control_panel(self, parent):
        """设置控制面板"""
        # 文件列表框架
        self.files_frame = ttk.LabelFrame(parent, text="选择的文件（可拖放图片）", padding=10)
        self.files_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.files_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 使用tk.Listbox而不是tkdnd.Listbox
        self.files_listbox = tk.Listbox(
            self.files_frame,
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE
        )
        self.files_listbox.pack(fill=tk.BOTH, expand=True, padx=(0, 5))
        scrollbar.config(command=self.files_listbox.yview)
        
        # 绑定拖放事件
        self.files_listbox.drop_target_register(DND_FILES)
        self.files_listbox.dnd_bind('<<Drop>>', self.handle_drop)
        
        # 绑定选择事件
        self.files_listbox.bind('<<ListboxSelect>>', self.on_select_file)
        
        # 控制按钮 - 固定高度
        self.control_frame = ttk.Frame(parent)
        self.control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(self.control_frame, text="选择文件", command=self.select_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.control_frame, text="清除列表", command=self.clear_files).pack(side=tk.LEFT, padx=5)
        
        # 阶梯数设置 - 固定高度
        self.settings_frame = ttk.LabelFrame(parent, text="渐变设置", padding=10)
        self.settings_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(self.settings_frame, text="阶梯数:").pack(side=tk.LEFT)
        self.steps_var = tk.StringVar(value="10")
        self.steps_entry = ttk.Entry(self.settings_frame, textvariable=self.steps_var, width=10)
        self.steps_entry.pack(side=tk.LEFT, padx=5)
        
        # 添加色相正态分布模式选项
        self.hue_normal_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.settings_frame, 
            text="使用色相正态分布", 
            variable=self.hue_normal_var
        ).pack(side=tk.LEFT, padx=15)
        
        # 添加保存重排图片选项
        self.save_sorted_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.settings_frame, 
            text="保存像素重排图", 
            variable=self.save_sorted_var
        ).pack(side=tk.LEFT, padx=15)
        
        # 底部框架 - 用于容纳进度条和生成按钮
        bottom_frame = ttk.Frame(parent)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)
        
        # 进度条
        self.progress = ttk.Progressbar(bottom_frame, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(0, 10))
        
        # 生成按钮
        ttk.Button(bottom_frame, text="生成色块图", command=self.generate_color_grid).pack(fill=tk.X)
        
    def setup_preview_panel(self, parent):
        """设置预览面板"""
        # 预览开关
        self.preview_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            parent,
            text="启用预览",
            variable=self.preview_var,
            command=self.toggle_preview
        ).pack(fill=tk.X, pady=5)
        
        # 重排图预览
        sorted_frame = ttk.LabelFrame(parent, text="像素重排预览", padding=10)
        sorted_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.sorted_preview = ttk.Label(sorted_frame)
        self.sorted_preview.pack(fill=tk.BOTH, expand=True)
        
        # 色块图预览
        grid_frame = ttk.LabelFrame(parent, text="色块图预览", padding=10)
        grid_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.grid_preview = ttk.Label(grid_frame)
        self.grid_preview.pack(fill=tk.BOTH, expand=True)

    def handle_drop(self, event):
        """处理文件拖放"""
        # 修改文件路径获取方式
        files = event.data.split()  # 文件路径以空格分隔
        valid_files = []
        for f in files:
            # 移除可能的花括号（某些系统会添加）
            f = f.strip('{}')
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                valid_files.append(f)
        
        if valid_files:
            self.selected_files.extend(valid_files)
            self.update_files_list()

    def on_select_file(self, event):
        """处理文件选择事件"""
        if not self.preview_var.get():
            return
            
        selection = self.files_listbox.curselection()
        if not selection:
            return
            
        try:
            file_path = self.selected_files[selection[0]]
            self.update_preview(file_path)
        except Exception as e:
            messagebox.showerror("预览错误", str(e))

    def update_preview(self, file_path: str):
        """更新预览图像"""
        try:
            steps = int(self.steps_var.get())
            if steps < 2 or steps > 256:
                raise ValueError("阶梯数必须在2-256之间")
                
            # 生成预览图像
            grid_image, _, sorted_image = self.process_image(file_path, steps)
            
            # 调整预览图像大小
            preview_width = 400
            
            if sorted_image is not None:
                h, w = sorted_image.shape[:2]
                scale = preview_width / w
                preview_size = (preview_width, int(h * scale))
                sorted_preview = cv2.resize(sorted_image, preview_size)
                # 转换为PhotoImage
                sorted_preview = cv2.cvtColor(sorted_preview, cv2.COLOR_BGR2RGB)
                sorted_preview = Image.fromarray(sorted_preview)
                sorted_preview = ImageTk.PhotoImage(sorted_preview)
                self.sorted_preview.configure(image=sorted_preview)
                self.sorted_preview.image = sorted_preview
            
            h, w = grid_image.shape[:2]
            scale = preview_width / w
            preview_size = (preview_width, int(h * scale))
            grid_preview = cv2.resize(grid_image, preview_size)
            # 转换为PhotoImage
            grid_preview = cv2.cvtColor(grid_preview, cv2.COLOR_BGR2RGB)
            grid_preview = Image.fromarray(grid_preview)
            grid_preview = ImageTk.PhotoImage(grid_preview)
            self.grid_preview.configure(image=grid_preview)
            self.grid_preview.image = grid_preview
            
        except Exception as e:
            messagebox.showerror("预览错误", str(e))

    def toggle_preview(self):
        """切换预览状态"""
        if self.preview_var.get():
            selection = self.files_listbox.curselection()
            if selection:
                self.on_select_file(None)
        else:
            self.sorted_preview.configure(image='')
            self.grid_preview.configure(image='')

    def select_files(self):
        files = filedialog.askopenfilenames(
            title="选择图片文件",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp")]
        )
        if files:
            self.selected_files.extend(files)
            self.update_files_list()
            
    def clear_files(self):
        self.selected_files.clear()
        self.files_listbox.delete(0, tk.END)
        
    def update_files_list(self):
        self.files_listbox.delete(0, tk.END)
        for file in self.selected_files:
            self.files_listbox.insert(tk.END, os.path.basename(file))
            
    def create_sorted_image(self, img: np.ndarray, use_hue_normal: bool) -> np.ndarray:
        """创建像素重排后的图片"""
        # 保持原始图片形状
        height, width = img.shape[:2]
        
        # 转换到HSV空间
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        pixels_hsv = hsv.reshape(-1, 3)
        pixels_bgr = img.reshape(-1, 3)
        
        if use_hue_normal:
            # 色相正态分布模式：按V->H->S排序
            # 计算色相权重
            hist_h = cv2.calcHist([hsv], [0], None, [180], [0, 180])
            hist_smooth = cv2.GaussianBlur(hist_h, (1, 15), 3).reshape(-1)
            h_weights = hist_smooth[pixels_hsv[:, 0]]
            
            # 创建排序键
            sort_keys = np.column_stack([
                pixels_hsv[:, 2],  # V (主要排序键)
                h_weights,         # 色相权重（第二排序键）
                pixels_hsv[:, 1]   # S（第三排序键）
            ])
        else:
            # 普通模式：按V->H->S排序
            sort_keys = pixels_hsv
        
        # 获取排序索引
        sort_idx = np.lexsort((sort_keys[:, 1], sort_keys[:, 0], sort_keys[:, 2]))
        
        # 重排像素
        sorted_pixels = pixels_bgr[sort_idx]
        
        # 重塑回原始形状
        sorted_image = sorted_pixels.reshape(height, width, 3)
        
        return sorted_image

    def process_image(self, image_path: str, steps: int) -> Tuple[np.ndarray, List[dict], Optional[np.ndarray]]:
        """优化的图像处理主函数"""
        # 1. 读取图片
        img = cv2.imread(image_path)
        
        # 2. 如果需要，创建重排图片
        sorted_image = None
        if self.save_sorted_var.get():
            sorted_image = self.create_sorted_image(img, self.hue_normal_var.get())
        
        # 转换到HSV空间继续处理
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # 2. 将图像重塑为二维数组
        pixels_hsv = hsv.reshape(-1, 3)
        pixels_bgr = img.reshape(-1, 3)
        
        gradient_colors = []
        color_info = []
        
        if self.hue_normal_var.get():
            # 色相正态分布模式
            # 3. 计算色相直方图
            hist_h = cv2.calcHist([pixels_hsv], [0], None, [180], [0, 180])
            hist_smooth = cv2.GaussianBlur(hist_h, (1, 15), 3).reshape(-1)
            
            # 4. 按V值（明度）对像素进行分组
            v_step = 256 // steps
            for i in range(steps):
                v_min = i * v_step
                v_max = min(255, (i + 1) * v_step)
                
                v_mask = (pixels_hsv[:, 2] >= v_min) & (pixels_hsv[:, 2] < v_max)
                if not np.any(v_mask):
                    continue
                    
                range_pixels_hsv = pixels_hsv[v_mask]
                range_pixels_bgr = pixels_bgr[v_mask]
                
                h_values = range_pixels_hsv[:, 0]
                h_weights = hist_smooth[h_values]
                
                max_weight_idx = np.argmax(h_weights)
                selected_color = range_pixels_bgr[max_weight_idx]
                gradient_colors.append(selected_color)
                
                # 收集颜色信息
                bgr_color = tuple(map(int, selected_color))
                rgb_color = bgr_color[::-1]
                color_info.append({
                    'Index': len(gradient_colors),
                    'RGB': f'({rgb_color[0]}, {rgb_color[1]}, {rgb_color[2]})',
                    'BGR': f'({bgr_color[0]}, {bgr_color[1]}, {bgr_color[2]})',
                    'Value': int(range_pixels_hsv[max_weight_idx, 2]),
                    'Hue': int(range_pixels_hsv[max_weight_idx, 0] * 2),
                    'Saturation': int(range_pixels_hsv[max_weight_idx, 1] / 255 * 100)
                })
        else:
            # 普通模式：按明度均匀取样
            # 获取唯一的像素值
            unique_pixels = np.unique(pixels_bgr, axis=0)
            # 转换为HSV进行排序
            unique_hsv = cv2.cvtColor(unique_pixels.reshape(-1, 1, 3), cv2.COLOR_BGR2HSV).reshape(-1, 3)
            # 按V值排序
            sort_idx = np.argsort(unique_hsv[:, 2])
            sorted_pixels = unique_pixels[sort_idx]
            
            # 均匀选择颜色
            step_size = max(1, len(sorted_pixels) // steps)
            gradient_colors = [sorted_pixels[i] for i in range(0, len(sorted_pixels), step_size)][:steps]
            
            # 收集颜色信息
            for color in gradient_colors:
                bgr_color = tuple(map(int, color))
                rgb_color = bgr_color[::-1]
                hsv_color = cv2.cvtColor(np.uint8([[color]]), cv2.COLOR_BGR2HSV)[0][0]
                color_info.append({
                    'Index': len(color_info) + 1,
                    'RGB': f'({rgb_color[0]}, {rgb_color[1]}, {rgb_color[2]})',
                    'BGR': f'({bgr_color[0]}, {bgr_color[1]}, {bgr_color[2]})',
                    'Value': int(hsv_color[2]),
                    'Hue': int(hsv_color[0] * 2),
                    'Saturation': int(hsv_color[1] / 255 * 100)
                })

        # 5. 创建色块网格图
        block_size = 400
        blocks_per_row = 8
        rows = (len(gradient_colors) + blocks_per_row - 1) // blocks_per_row
        
        grid = np.full((rows * block_size, blocks_per_row * block_size, 3), 
                      255, dtype=np.uint8)
        
        for idx, color in enumerate(gradient_colors):
            row = idx // blocks_per_row
            col = idx % blocks_per_row
            x1 = col * block_size
            y1 = row * block_size
            grid[y1:y1+block_size, x1:x1+block_size] = color
            
            # 更新颜色信息中的位置
            color_info[idx].update({
                'Position': f'行{row + 1}, 列{col + 1}',
                'Coordinates': f'({x1}, {y1}, {x1+block_size}, {y1+block_size})'
            })
        
        return grid, color_info, sorted_image

    def generate_color_grid(self):
        """主处理函数"""
        if not self.selected_files:
            messagebox.showwarning("警告", "请先选择图片文件")
            return
            
        try:
            steps = int(self.steps_var.get())
            if steps < 2 or steps > 256:
                raise ValueError("阶梯数必须在2-256之间")
        except ValueError as e:
            messagebox.showerror("错误", str(e))
            return
            
        save_dir = filedialog.askdirectory(title="选择保存目录")
        if not save_dir:
            return
            
        total_files = len(self.selected_files)
        self.progress['maximum'] = total_files
        
        for i, file_path in enumerate(self.selected_files):
            try:
                # 处理图片
                grid_image, color_info, sorted_image = self.process_image(file_path, steps)
                
                # 生成基础文件名
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                
                # 如果启用了保存重排图片
                if self.save_sorted_var.get() and sorted_image is not None:
                    sorted_path = self.get_unique_filename(
                        os.path.join(save_dir, f"{base_name}_sorted"),
                        '.png'
                    )
                    cv2.imwrite(sorted_path, sorted_image)
                
                # 保存色块网格图
                png_path = self.get_unique_filename(
                    os.path.join(save_dir, f"{base_name}_color_grid"),
                    '.png'
                )
                cv2.imwrite(png_path, grid_image)
                
                # 保存颜色信息
                json_path = self.get_unique_filename(
                    os.path.join(save_dir, f"{base_name}_info"),
                    '_info.json'
                )
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'total_colors': len(color_info),
                        'colors': color_info
                    }, f, ensure_ascii=False, indent=2)
                
                self.progress['value'] = i + 1
                self.window.update()
            except Exception as e:
                messagebox.showerror("错误", f"处理文件 {os.path.basename(file_path)} 时出错：{str(e)}")
        
        self.progress['value'] = 0
        messagebox.showinfo("完成", "色块图和颜色信息生成完成！")

    def get_unique_filename(self, base_path: str, ext: str) -> str:
        """获取唯一的文件名，如果存在则自动增加序号"""
        directory = os.path.dirname(base_path)
        filename = os.path.basename(base_path)
        name_without_ext = os.path.splitext(filename)[0]
        
        counter = 1
        new_path = os.path.join(directory, f"{name_without_ext}{ext}")
        
        while os.path.exists(new_path):
            new_path = os.path.join(directory, f"{name_without_ext}_{counter}{ext}")
            counter += 1
            
        return new_path

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = GradientGenerator()
    app.run()