from ultralytics import YOLO
from flask import Flask, request
from flask_cors import CORS
import time
import os
import sys

# 创建临时目录
os.makedirs("./temp", exist_ok=True)
os.makedirs("./runs/detect", exist_ok=True)

app = Flask(__name__, static_folder="./runs/detect", static_url_path="/runs/detect")
CORS(app)

# ===== 加载模型 =====
# 优先加载微调模型, 回退到预训练模型
MODEL_CANDIDATES = [
    "yolo11n.pt",          # 微调后的模型 (与预训练同名, 覆盖)
    "best.pt",             # 直接放置的训练权重
    "runs/train/defect_detect/weights/best.pt",  # 训练默认输出路径
]

model = None
model_source = None
for candidate in MODEL_CANDIDATES:
    if os.path.exists(candidate):
        model = YOLO(candidate)
        model_source = candidate
        break

if model is None:
    print("[错误] 未找到任何模型文件")
    sys.exit(1)

print(f"[模型] 已加载: {model_source}")


@app.route("/test", methods=["GET"])
def test():
    return f"AI检测服务运行中... (模型: {model_source})"


@app.route("/model_info", methods=["GET"])
def model_info():
    """返回当前模型信息"""
    names = model.names if hasattr(model, "names") else {}
    return {
        "model": model_source,
        "classes": names,
        "nc": len(names),
    }


@app.route("/ai_detect", methods=["POST"])
def ai_detect():
    """接收图片 -> AI检测 -> 返回结果图片URL"""
    file = request.files["my_img"]

    # 保存临时文件
    temp_file_path = f"./temp/{file.filename}"
    file.save(temp_file_path)

    try:
        # AI推理
        result = model.predict(temp_file_path)

        # 保存结果图
        t = time.time()
        save_path = f"runs/detect/{t}{file.filename}"
        result[0].save(filename=save_path)

        # 返回图片URL
        return f"http://localhost:5000/{save_path}"
    finally:
        # 清理临时文件
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
