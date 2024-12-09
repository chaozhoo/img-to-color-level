import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from typing import List, Tuple
import os
import json

class GradientGenerator:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("渐变文件生成器")
        self.window.geometry("600x500")
        
        # 创建主框架来容纳所有元素
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 文件列表 - 给予更合理的高度权重
        self.files_frame = ttk.LabelFrame(main_frame, text="选择的文件", padding=10)
        self.files_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.files_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.files_listbox = tk.Listbox(self.files_frame, yscrollcommand=scrollbar.set)
        self.files_listbox.pack(fill=tk.BOTH, expand=True, padx=(0, 5))
        scrollbar.config(command=self.files_listbox.yview)
        
        # 控制按钮 - 固定高度
        self.control_frame = ttk.Frame(main_frame)
        self.control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(self.control_frame, text="选择文件", command=self.select_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.control_frame, text="清除列表", command=self.clear_files).pack(side=tk.LEFT, padx=5)
        
        # 阶梯数设置 - 固定高度
        self.settings_frame = ttk.LabelFrame(main_frame, text="渐变设置", padding=10)
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
        
        # 底部框架 - 用于容纳进度条和生成按钮
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)
        
        # 进度条
        self.progress = ttk.Progressbar(bottom_frame, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(0, 10))
        
        # 生成按钮
        ttk.Button(bottom_frame, text="生成色块图", command=self.generate_color_grid).pack(fill=tk.X)
        
        self.selected_files = []
        
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
            
    def process_image(self, image_path: str, steps: int) -> Tuple[np.ndarray, List[dict]]:
        """优化的图像处理主函数"""
        # 1. 读取图片并转换到HSV空间（OpenCV的HSV更快）
        img = cv2.imread(image_path)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # 2. 将图像重塑为二维数组 [pixels, (h,s,v)]
        pixels_hsv = hsv.reshape(-1, 3)
        pixels_bgr = img.reshape(-1, 3)
        
        # 3. 计算色相直方图（只关注H通道）
        hist_h = cv2.calcHist([pixels_hsv], [0], None, [180], [0, 180])
        # 使用高斯模糊平滑直方图
        hist_smooth = cv2.GaussianBlur(hist_h, (1, 15), 3).reshape(-1)
        
        # 4. 按V值（明度）对像素进行分组
        v_step = 256 // steps  # 明度步长
        gradient_colors = []
        color_info = []
        
        for i in range(steps):
            v_min = i * v_step
            v_max = min(255, (i + 1) * v_step)
            
            # 在当前明度范围内的像素掩码
            v_mask = (pixels_hsv[:, 2] >= v_min) & (pixels_hsv[:, 2] < v_max)
            if not np.any(v_mask):
                continue
                
            # 获取该明度范围内的所有像素
            range_pixels_hsv = pixels_hsv[v_mask]
            range_pixels_bgr = pixels_bgr[v_mask]
            
            # 获取该范围内最常见的色相
            h_values = range_pixels_hsv[:, 0]
            h_weights = hist_smooth[h_values]
            
            # 使用权重选择颜色
            max_weight_idx = np.argmax(h_weights)
            selected_color = range_pixels_bgr[max_weight_idx]
            
            # 添加到结果列表
            gradient_colors.append(selected_color)
            
            # 收集颜色信息
            bgr_color = tuple(map(int, selected_color))
            rgb_color = bgr_color[::-1]
            color_info.append({
                'Index': len(gradient_colors),
                'RGB': f'({rgb_color[0]}, {rgb_color[1]}, {rgb_color[2]})',
                'BGR': f'({bgr_color[0]}, {bgr_color[1]}, {bgr_color[2]})',
                'Value': int(range_pixels_hsv[max_weight_idx, 2]),
                'Hue': int(range_pixels_hsv[max_weight_idx, 0] * 2),  # 转换到0-360
                'Saturation': int(range_pixels_hsv[max_weight_idx, 1] / 255 * 100)  # 转换到百分比
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
        
        return grid, color_info

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
                grid_image, color_info = self.process_image(file_path, steps)
                
                # 生成输出文件名
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                output_name = f"{base_name}_color_grid"
                
                # 保存图片
                png_path = self.get_unique_filename(
                    os.path.join(save_dir, output_name), 
                    '.png'
                )
                cv2.imwrite(png_path, grid_image)
                
                # 保存颜色信息
                json_path = self.get_unique_filename(
                    os.path.join(save_dir, output_name), 
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