# 测试代码 deepseek
import time
from openai import OpenAI
key = "sk-c23c7cdf318c413392e48371e0efa667"
sty = "你是一个海关报关工作者"

def deepseek(say):
    client = OpenAI(api_key=key, base_url="https://api.deepseek.com")
    print("请稍等...正在思考")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": sty},
            {"role": "user", "content": say},
        ],
        stream=True
    )

    full_content = ""
    for chunk in response:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            print(content, end="", flush=True)
            full_content += content
    print() # 换行
    return full_content

def printChar(text, daylay=0.1):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(daylay)
    print()

# while True:
#     myin = input("有什么问题捏：")
#     if myin == "exit":
#         print("遛了喵")
#         break
#     resp = deepseek(myin)
#     print("----------------------------------------------------------------------------------")
    



