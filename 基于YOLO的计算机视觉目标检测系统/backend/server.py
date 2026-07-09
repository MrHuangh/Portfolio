from ultralytics import YOLO
from flask import Flask, request
from flask_cors import CORS
import time
import os

# 创建临时目录
os.makedirs("./temp", exist_ok=True)
os.makedirs("./runs/detect", exist_ok=True)

app = Flask(__name__, static_folder="./runs/detect", static_url_path="/runs/detect")
CORS(app)

# 加载模型
model = YOLO("./yolo11n.pt")


@app.route("/test", methods=["GET"])
def test():
    return "AI检测服务运行中..."


@app.route("/ai_detect", methods=["POST"])
def ai_detect():
    """接收图片 → AI检测 → 返回结果图片URL"""
    file = request.files["my_img"]
    # 保存临时文件
    temp_file_path = f"./temp/{file.filename}"
    file.save(temp_file_path)
    # AI推理
    result = model.predict(temp_file_path)
    # 保存结果图
    t = time.time()
    save_path = f"runs/detect/{t}{file.filename}"
    result[0].save(filename=save_path)
    # 清理临时文件
    os.remove(temp_file_path)
    # 返回图片URL
    return f"http://localhost:5000/{save_path}"


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
