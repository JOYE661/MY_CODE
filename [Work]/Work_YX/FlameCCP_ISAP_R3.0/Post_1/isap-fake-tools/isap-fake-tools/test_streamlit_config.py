#!/usr/bin/env python3
import os
import json
from app.services.data_generator import DataGenerator
from app.core.config import settings

# 测试Streamlit应用配置
if __name__ == "__main__":
    print("🚀 测试Streamlit应用配置...")
    
    # 检查配置文件目录是否存在
    print(f"\n📁 检查配置文件目录: {settings.CONFIG_FILE_PATH}")
    if os.path.exists(settings.CONFIG_FILE_PATH):
        print("✅ 配置文件目录存在")
        
        # 列出配置文件
        config_files = [f for f in os.listdir(settings.CONFIG_FILE_PATH) if f.endswith('.json')]
        print(f"📋 发现 {len(config_files)} 个配置文件:")
        for file in config_files:
            print(f"  - {file}")
            
            # 检查配置文件格式是否正确
            try:
                with open(os.path.join(settings.CONFIG_FILE_PATH, file), 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 检查必要的配置字段
                required_fields = ['fields']
                missing_fields = [field for field in required_fields if field not in config]
                if missing_fields:
                    print(f"    ⚠️  警告: 缺少必要字段 {missing_fields}")
                else:
                    print(f"    ✅  格式正确，包含 {len(config['fields'])} 个字段")
            except Exception as e:
                print(f"    ❌  错误: 配置文件格式不正确 - {str(e)}")
    else:
        print("❌ 配置文件目录不存在")
    
    # 测试初始化DataGenerator
    print("\n🧪 测试DataGenerator初始化...")
    try:
        generator = DataGenerator()
        available_tables = generator.get_available_tables()
        print(f"✅ DataGenerator初始化成功")
        print(f"📊 可用表数量: {len(available_tables)}")
        
        # 测试生成单条记录（不连接数据库）
        if available_tables:
            print(f"\n🔍 测试生成单条记录（表: {available_tables[0]}）...")
            config = generator.table_configs[available_tables[0]]
            from datetime import date
            record = generator._generate_record(config, available_tables[0], date.today())
            print(f"✅ 成功生成记录，包含 {len(record)} 个字段")
            print(f"📋 字段列表: {list(record.keys())}")
            print("💡 提示: Streamlit应用应该可以正常运行")
    except Exception as e:
        print(f"❌ DataGenerator初始化失败: {str(e)}")
        print("💡 请检查app/services/data_generator.py文件是否有错误")
    
    # 显示数据库配置信息（不包含密码）
    print("\n🔒 数据库配置信息:")
    print(f"  - 主机: {settings.POSTGRES_SERVER}")
    print(f"  - 端口: {settings.POSTGRES_PORT}")
    print(f"  - 用户: {settings.POSTGRES_USER}")
    print(f"  - 数据库: {settings.POSTGRES_DB}")
    print(f"  - URL: postgresql://{settings.POSTGRES_USER}:[密码隐藏]@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
    
    # 显示启动提示
    print("\n🚀 启动指南:")
    print("  1. 确保数据库连接配置正确")
    print("  2. 运行启动脚本: ./run_streamlit.sh")
    print("  3. 或直接运行: python3 -m streamlit run streamlit_app.py")
    print("  4. 访问 http://localhost:8501 查看控制面板")