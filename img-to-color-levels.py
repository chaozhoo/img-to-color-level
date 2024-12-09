import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
import colorsys
import os
from typing import List, Tuple, Dict
import math
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
            
    def get_pixel_hsl(self, pixel: Tuple[int, int, int]) -> Tuple[float, float, float]:
        r, g, b = [x/255.0 for x in pixel]
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        return (h, s, l)
    
    def generate_gradient_data(self, image_path: str, steps: int) -> List[Tuple[int, int, int]]:
        # 使用OpenCV读取图片
        img = cv2.imread(image_path)
        # 转换为RGB颜色空间（OpenCV默认是BGR）
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # 将图像重塑为一维数组
        pixels = img.reshape(-1, 3)
        
        # 获取唯一的像素值
        unique_pixels = np.unique(pixels, axis=0)
        
        # 转换为HSL并进行排序
        pixel_hsl = [(tuple(p), self.get_pixel_hsl(tuple(p))) for p in unique_pixels]
        sorted_pixels = sorted(pixel_hsl, key=lambda x: (x[1][2], x[1][0], x[1][1]))
        
        # 选择指定数量的阶梯
        step_size = max(1, len(sorted_pixels) // steps)
        gradient_colors = [p[0] for p in sorted_pixels[::step_size]][:steps]
        
        return gradient_colors
    
    def get_color_info(self, color: Tuple[int, int, int]) -> Dict:
        """获取颜色的详细信息"""
        # 确保颜色值是Python原生int类型
        r, g, b = int(color[0]), int(color[1]), int(color[2])
        
        # 计算HSL
        h, l, s = self.get_pixel_hsl((r, g, b))
        # 转换为更易读的格式
        h = round(h * 360)  # 转换为0-360度
        s = round(s * 100)  # 转换为百分比
        l = round(l * 100)  # 转换为百分比
        
        # 计算HEX
        hex_color = '#{:02x}{:02x}{:02x}'.format(r, g, b)
        
        return {
            'RGB': f'({r}, {g}, {b})',
            'HSL': f'({h}°, {s}%, {l}%)',
            'HEX': hex_color.upper(),
            'R': int(r),  # 确保是Python原生int类型
            'G': int(g),
            'B': int(b),
            'H': int(h),
            'S': int(s),
            'L': int(l)
        }

    def create_color_grid(self, colors: List[Tuple[int, int, int]], block_size: int = 400) -> Tuple[np.ndarray, List[Dict]]:
        """创建色块网格图和颜色信息"""
        blocks_per_row = 8
        rows = math.ceil(len(colors) / blocks_per_row)
        
        # 创建画布
        img_width = blocks_per_row * block_size
        img_height = rows * block_size
        img = np.full((img_height, img_width, 3), (255, 255, 255), dtype=np.uint8)
        
        # 存储色块信息
        color_info = []
        
        # 绘制色块
        for i, color in enumerate(colors):
            row = i // blocks_per_row
            col = i % blocks_per_row
            
            x1 = col * block_size
            y1 = row * block_size
            x2 = x1 + block_size
            y2 = y1 + block_size
            
            # 确保颜色值是整数元组，并转换为BGR格式
            bgr_color = (
                int(color[2]),  # B
                int(color[1]),  # G
                int(color[0])   # R
            )
            
            # 使用OpenCV绘制矩形
            cv2.rectangle(
                img, 
                pt1=(x1, y1),  # 明确指定参数名称
                pt2=(x2, y2),
                color=bgr_color,
                thickness=-1  # 填充矩形
            )
            
            # 收集颜色信息（使用原始RGB颜色）
            info = self.get_color_info(color)
            info.update({
                'Index': i + 1,
                'Position': f'行{row + 1}, 列{col + 1}',
                'Coordinates': f'({x1}, {y1}, {x2}, {y2})'
            })
            color_info.append(info)
        
        return img, color_info

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

    def save_color_info(self, color_info: List[Dict], output_path: str):
        """保存颜色信息到JSON文件"""
        # 构建JSON数据结构
        json_data = {
            "total_colors": len(color_info),
            "colors": color_info
        }
        
        # 生成唯一的JSON文件路径
        json_path = self.get_unique_filename(
            os.path.splitext(output_path)[0], 
            '_info.json'
        )
        
        # 保存JSON文件，使用缩进格式化
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

    def generate_color_grid(self):
        """生成色块网格图的主函数"""
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
                colors = self.generate_gradient_data(file_path, steps)
                grid_image, color_info = self.create_color_grid(colors)
                
                # 生成基础文件名
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                
                # 获取唯一的PNG文件路径
                png_path = self.get_unique_filename(
                    os.path.join(save_dir, f"{base_name}_color_grid"),
                    '.png'
                )
                
                # 保存图片
                cv2.imwrite(png_path, grid_image)
                
                # 保存颜色信息（使用相同的基础文件名）
                self.save_color_info(color_info, png_path)
                
                self.progress['value'] = i + 1
                self.window.update()
            except Exception as e:
                messagebox.showerror("错误", f"处理文件 {os.path.basename(file_path)} 时出错：{str(e)}")
                
        self.progress['value'] = 0
        messagebox.showinfo("完成", "色块图和颜色信息生成完成！")

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = GradientGenerator()
    app.run()