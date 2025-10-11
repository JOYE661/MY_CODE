#!/bin/bash

# 启动Streamlit应用的脚本

# 确保脚本在出错时退出
set -e

# 获取当前目录
CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 打印启动信息
 echo "🚀 正在启动ISAP数据生成器控制面板..."
 echo "📁 当前工作目录: $CURRENT_DIR"

# 检查Python是否可用
if ! command -v python3 &> /dev/null
then
    echo "❌ 错误: 未找到python3命令，请先安装Python3"
    exit 1
fi

# 运行Streamlit应用
# 使用-m参数确保即使不在PATH中也能运行
python3 -m streamlit run "$CURRENT_DIR/streamlit_app.py" --server.port 8501

# 如果启动失败，显示错误信息
if [ $? -ne 0 ]
then
    echo "❌ 应用启动失败，请检查错误信息"
    echo "📝 可能的解决方案:"
    echo "1. 确保所有依赖已安装: pip3 install -r requirements.txt"
    echo "2. 检查数据库连接配置是否正确"
    echo "3. 确保8502端口未被占用"
    exit 1
fi