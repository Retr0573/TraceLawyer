import http.client
import json
import ssl

# ssl._create_default_https_context = ssl._create_unverified_context

headers = {
    "Content-Type": "application/json",
    "Accept": "text/event-stream",
    "Authorization": "Bearer 98fb62695047338d32729257a65a48a6:NDNkOTVmZmJjYzc0OTg5MTg5ODI5MDNi",
}
PDF_LIST = [
    "maomi",
    "mimao"
]
data = {
    "flow_id": "7357096384330665986",
    "uid": "123",
    "parameters": {"AGENT_USER_INPUT": "你好",
                   "pdf_list":PDF_LIST},
    "ext": {"bot_id": "adjfidjf", "caller": "workflow"},
    "stream": True,
}
payload = json.dumps(data)

conn = http.client.HTTPSConnection("xingchen-api.xf-yun.com", timeout=120)
conn.request(
    "POST", "/workflow/v1/chat/completions", payload, headers, encode_chunked=True
)
res = conn.getresponse()

import json

if data.get("stream"):
    while chunk := res.readline():
        chunk_str = chunk.decode("utf-8").strip()
        # 检查是否是SSE格式的数据
        if chunk_str.startswith("data: "):
            # 提取JSON部分
            json_str = chunk_str[6:]  # 去掉"data: "前缀
            try:
                # 转换为字典
                data_dict = json.loads(json_str)
                
                # 提取回复内容
                if "choices" in data_dict and len(data_dict["choices"]) > 0:
                    choice = data_dict["choices"][0]
                    if "delta" in choice and "content" in choice["delta"]:
                        content = choice["delta"]["content"]
                        # print(f"回复内容: {content}")
                        print(f"{content}")
                        
            except json.JSONDecodeError:
                print(f"JSON解析错误: {chunk_str}")
        else:
            print(chunk_str)
else:
    data = res.readline()
    print(data.decode("utf-8"))
