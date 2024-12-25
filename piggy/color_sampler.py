import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

def analyze_image():
    root = tk.Tk()
    root.title("Ring Color Analyzer")
    root.withdraw()  # Sembunyikan window utama
    
    # Buka dialog pemilihan file
    file_path = filedialog.askopenfilename(
        title="Pilih gambar ring",
        filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")]
    )
    
    if not file_path:
        print("Tidak ada file yang dipilih")
        return
    
    # Baca gambar
    image = cv2.imread(file_path)
    if image is None:
        print("Gagal membaca gambar")
        return
    
    # Convert BGR to RGB untuk display
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    # Convert BGR to HSV untuk analisis
    image_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Buat window baru
    window = tk.Toplevel()
    window.title("Ring Color Analyzer")
    
    drawing = False
    points = []
    
    def start_draw(event):
        nonlocal drawing
        drawing = True
        points.clear()
        canvas.delete("area")
        points.append((event.x, event.y))
    
    def draw(event):
        if drawing:
            points.append((event.x, event.y))
            if len(points) > 1:
                p1 = points[-2]
                p2 = points[-1]
                canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill='red', width=2, tags="area")
    
    def stop_draw(event):
        nonlocal drawing
        if drawing:
            drawing = False
            if len(points) > 2:
                canvas.create_line(points[-1][0], points[-1][1], 
                                 points[0][0], points[0][1], 
                                 fill='red', width=2, tags="area")
                analyze_area()
    
    def analyze_area():
        if len(points) < 3:
            print("Area terlalu kecil untuk dianalisis")
            return
        
        # Buat mask dari polygon
        mask = np.zeros(image_hsv.shape[:2], dtype=np.uint8)
        polygon_points = np.array(points, np.int32)
        cv2.fillPoly(mask, [polygon_points], 255)
        
        # Ambil nilai warna dari area yang dipilih
        masked_hsv = cv2.bitwise_and(image_hsv, image_hsv, mask=mask)
        
        # Ambil nilai-nilai HSV yang tidak nol
        hsv_values = masked_hsv[mask > 0]
        hsv_values = hsv_values.reshape(-1, 3)
        
        if len(hsv_values) > 0:
            # Pisahkan komponen H, S, V
            h_values = hsv_values[:, 0]
            s_values = hsv_values[:, 1]
            v_values = hsv_values[:, 2]
            
            print("\n=== ANALISIS WARNA AREA ===")
            print("\nRange HSV yang disarankan:")
            print("# Range merah bagian bawah")
            print(f"lower_red1 = np.array([0, {max(0, np.min(s_values)-30)}, {max(0, np.min(v_values)-30)}])")
            print(f"upper_red1 = np.array([10, {min(255, np.max(s_values)+30)}, {min(255, np.max(v_values)+30)}])")
            print("\n# Range merah bagian atas")
            print(f"lower_red2 = np.array([170, {max(0, np.min(s_values)-30)}, {max(0, np.min(v_values)-30)}])")
            print(f"upper_red2 = np.array([180, {min(255, np.max(s_values)+30)}, {min(255, np.max(v_values)+30)}])")
            
            print("\nStatistik nilai HSV:")
            print(f"Hue range: {np.min(h_values):.1f} - {np.max(h_values):.1f}")
            print(f"Saturation range: {np.min(s_values):.1f} - {np.max(s_values):.1f}")
            print(f"Value range: {np.min(v_values):.1f} - {np.max(v_values):.1f}")
    
    # Convert untuk display
    image_pil = Image.fromarray(image_rgb)
    photo = ImageTk.PhotoImage(image_pil)
    
    # Buat canvas
    canvas = tk.Canvas(window, width=image_pil.width, height=image_pil.height)
    canvas.pack()
    
    # Tampilkan gambar
    canvas.create_image(0, 0, anchor=tk.NW, image=photo)
    
    # Bind events
    canvas.bind("<Button-1>", start_draw)
    canvas.bind("<B1-Motion>", draw)
    canvas.bind("<ButtonRelease-1>", stop_draw)
    
    # Tombol kontrol
    button_frame = tk.Frame(window)
    button_frame.pack(pady=10)
    
    def reset():
        points.clear()
        canvas.delete("area")
        print("\n=== Reset ===")
    
    reset_button = tk.Button(button_frame, text="Reset", command=reset)
    reset_button.pack(side=tk.LEFT, padx=5)
    
    quit_button = tk.Button(button_frame, text="Keluar", command=window.destroy)
    quit_button.pack(side=tk.LEFT, padx=5)
    
    instruction_label = tk.Label(window, 
                               text="Gambar area di sekitar ring dengan mengklik dan drag mouse", 
                               font=('Arial', 12))
    instruction_label.pack(pady=5)
    
    window.mainloop()

if __name__ == "__main__":
    analyze_image() 