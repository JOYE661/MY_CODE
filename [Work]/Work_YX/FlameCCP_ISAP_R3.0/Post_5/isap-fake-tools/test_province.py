import json
import random
from faker import Faker
import os

# 初始化Faker
fake = Faker('zh_CN')

# 读取省市区联动数据
script_dir = os.path.dirname(os.path.abspath(__file__))
pca_file_path = os.path.join(script_dir, 'dist', 'pca.json')
with open(pca_file_path, 'r', encoding='utf-8') as f:
    pca_data = json.load(f)

def generate_address():
    """
    生成符合中国行政区划的地址信息
    """
    # 随机选择一个省
    province = random.choice(list(pca_data.keys()))
    
    # 随机选择一个市
    city = random.choice(list(pca_data[province].keys()))
    
    # 随机选择一个区/县
    area = random.choice(pca_data[province][city])
    
    # 生成详细地址
    detail_address = fake.street_address()
    
    # 组合完整地址
    full_address = f"{province}{city}{area}{detail_address}"
    
    return {
        'province': province,
        'city': city,
        'area': area,
        'detail': detail_address,
        'full_address': full_address
    }

def generate_multiple_addresses(count=10):
    """
    生成多个地址
    """
    addresses = []
    for _ in range(count):
        addresses.append(generate_address())
    return addresses

# 使用示例
if __name__ == "__main__":
    # 生成一个地址
    address = generate_address()
    print("单个地址:")
    print(f"省份: {address['province']}")
    print(f"城市: {address['city']}")
    print(f"区县: {address['area']}")
    print(f"详细地址: {address['detail']}")
    print(f"完整地址: {address['full_address']}")
    print("\n")
    
    # 生成多个地址
    print("多个地址:")
    addresses = generate_multiple_addresses(5)
    for i, addr in enumerate(addresses, 1):
        print(f"{i}. {addr['full_address']}")
