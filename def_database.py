import os
import json

DB_FILE = "camera_database.json"

def deduce_overlay(sensor_name):
    # 根据树莓派底层核心，匹配映射传感器名字以输出驱动项 overlays 命令
    sensor_map = {
        "hawkeye": "arducam-64mp",
        "pivariety": "arducam-pivariety", 
    }
    s = str(sensor_name).lower()
    return sensor_map.get(s, s)

# 加载原始提示全套数据构建出的映射（全数据源支持初始化生成使用）
# 包括了 CSV: B0031 OV5647 ~ B0584 IMX708 所有支持!
CSV_SOURCE = [
    ("B0031", "OV5647"), ("B0032", "OV5647"), ("B0033", "OV5647"), ("B0033", "OV5647"), 
    ("B003301", "OV5647"), ("B0033C", "OV5647"), ("B0033R", "OV5647"), ("B0035", "OV5647"), 
    ("B003503", "OV5647"), ("B003504", "OV5647"), ("B0066", "OV5647"), ("B0066-02", "OV5647"), 
    ("B006603", "OV5647"), ("B006604", "OV5647"), ("B006605", "OV5647"), ("B0102", "IMX219"), 
    ("B0103", "IMX219"), ("B0151", "OV5647"), ("B0152", "IMX219"), ("B0153", "IMX219"), 
    ("B0154", "IMX219"), ("B0161", "OV7251"), ("B0165", "OV9281"), ("B016712MP", "IMX477"), 
    ("B01675MP", "OV5647"), ("B01678MP", "IMX219"), ("B0167B12", "IMX477"), ("B0167B5", "OV5647"), 
    ("B0167B8", "IMX219"), ("B0176", "OV5647"), ("B0176R", "OV5647"), ("B0180", "IMX219"), 
    ("B0182", "IMX219"), ("B0184", "IMX219"), ("B0188", "IMX219"), ("B0190", "IMX219"), 
    ("B0194", "IMX219"), ("B0206", "OV7251"), ("B0224", "OV9281"), ("B0240", "IMX477"), 
    ("B024001", "IMX477"), ("B0240E", "IMX477"), ("B0262", "IMX477"), ("B0265R", "IMX477"), 
    ("B0266", "Pivariety"), ("B0267", "Pivariety"), ("B0270", "IMX477"), ("B0272", "IMX477"), 
    ("B0280", "IMX477"), ("B0286", "IMX219"), ("B0288", "IMX477"), ("B0303R", "IMX477"), 
    ("B0306", "IMX708"), ("B0307", "IMX708"), ("B0308", "IMX708"), ("B0309", "IMX708"), 
    ("B0310", "IMX708"), ("B0311", "IMX708"), ("B0312", "IMX708"), ("B031202", "IMX708"), 
    ("B031203", "IMX708"), ("B0324", "Pivariety"), ("B0331", "Pivariety"), ("B0333", "Pivariety"), 
    ("B0348", "Pivariety"), ("B0353", "Pivariety"), ("B0367", "Pivariety"), ("B0371", "IMX519"), 
    ("B0381", "Pivariety"), ("B0386", "IMX519"), ("B0388", "IMX519"), ("B0389", "IMX519"), 
    ("B0390", "IMX219"), ("B039001", "IMX219"), ("B0391", "IMX519"), ("B0392", "IMX219"), 
    ("B0393", "IMX219"), ("B0394", "IMX219"), ("B0395", "IMX219"), ("B0396", "IMX219"), 
    ("B0397", "IMX477"), ("B0399", "Hawkeye"), ("B0402", "Hawkeye"), ("B0404", "OV5647"), 
    ("B0405", "OV9281"), ("B0408", "IMX290"), ("B0410", "Pivariety"), ("B0411", "OV9281"), 
    ("B0412", "IMX378"), ("B0423", "IMX462"), ("B0424", "IMX290"), ("B0425", "IMX327"), 
    ("B0428", "OV5647"), ("B0444", "Pivariety"), ("B0445", "IMX296"), ("B0449", "IMX519"), 
    ("B0452", "IMX477"), ("B0466R", "IMX477"), ("B0483", "OV64A40"), ("B0484", "IMX708"), 
    ("B0491", "IMX219"), ("B0492R", "Pivariety"), ("B0513", "Hawkeye"), ("B0526", "Pivariety"), 
    ("B0549", "IMX219"), ("B0550", "IMX477"), ("B0568", "IMX335"), ("B0569", "IMX415"), 
    ("B0584", "IMX708")
]

def generate_default_data():
    dataset = []
    # 使用去重逻辑机制去处源中的多次重复数据。确保展示 UI不杂乱无章 
    sku_added = set()
    for row in CSV_SOURCE:
        sku = row[0].upper()
        if sku not in sku_added:
            sensor = row[1]
            dataset.append({
                "sku": sku, 
                "sensor": sensor.lower(), 
                "overlay": deduce_overlay(sensor), 
                "desc": f"{sensor}系列标准装配机型(从大工厂库继承同步)"
            })
            sku_added.add(sku)
    return dataset

DEFAULT_CAMERAS = generate_default_data()

class DataEngine:
    @staticmethod
    def fetch_records():
        if not os.path.exists(DB_FILE):
            DataEngine.commit_records(DEFAULT_CAMERAS)
            return DEFAULT_CAMERAS
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            return DEFAULT_CAMERAS
            
    @staticmethod
    def commit_records(data_list):
        try:
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump(data_list, f, ensure_ascii=False, indent=4)
        except Exception:
            pass
