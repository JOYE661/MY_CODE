import requests
from lxml import etree

# 定义一个全局数组,用了存放获取到的ip地址
list_ips = []
# 获取ip地址
def get_url(urls='https://hidemy.name/cn/proxy-list/?type=s#list'):
    # 构建请求头
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',
        'cookie': '_ym_uid=1631777163767759683; _ym_d=1631777163; PAPVisitorId=b90c63abf5f4ae440925e5MpEdpDVCg3; PAPVisitorId=b90c63abf5f4ae440925e5MpEdpDVCg3; _ga=GA1.2.2061127712.1631777164; _gid=GA1.2.1247344787.1631777164; _ym_isad=2; _dc_gtm_UA-90263203-1=1; _gat_UA-90263203-1=1; _fbp=fb.1.1631777165623.195031136',
    }
    respons = requests.get(urls, headers=headers, )
    # 获取请求内容,并且转换成html格式
    html_content = etree.HTML(respons.content.decode('utf-8'))
    tbody_list = html_content.xpath("//*[@class='table_block']/table/tbody/tr")
    print(len(tbody_list))
    # 如果能获取到数据，进行下一步
    if len(tbody_list):
        # 遍历内容
        for tbody in tbody_list:
            # 获取ip地址
            ip_name = tbody.xpath('./td[1]/text()')[0]
            # 获取端口号
            port_name = tbody.xpath('./td[2]/text()')[0]
            # 字符串拼接
            ips = ip_name + ':' + port_name
            # 添加到全局数组中
            list_ips.append(ips)
        else:
            # 获取下一页url
            next_url_xpath = html_content.xpath("//*[@class='next_array']/a/@href")
            if len(next_url_xpath):
                # 拼接下一页url
                next_url = 'https://hidemy.name' + next_url_xpath[0]
                # 继续请求
                get_url(next_url)
            else:
                print('没有下一页了')
    else:
        print('没有获取到')
    # 返回数据
    return list_ips

# 调用方法
if __name__ == '__main__':
   list_ip = get_url()
   print(list_ip)

