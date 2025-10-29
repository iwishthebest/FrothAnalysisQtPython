import requests


def get_process_data():
    url = "http://10.12.18.2:8081/open/realdata/snapshot/batchGet"
    tag_list = ["KYFX.kyfx_gqxk_grade_Pb", "KYFX.kyfx_gqxk_grade_Zn"]
    tag_param = ",".join(tag_list)
    try:
        params = {"tagNameList": tag_param}
        response = requests.get(url=url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            records = []
            for item in data.get("data", []):
                tag_name = item['TagName'].strip()
                value = item['Value']
                records.append((tag_name, value))
            grade_pb = int(records[0][1])
            grade_zn = int(records[1][1])
        else:
            print(f"请求失败，状态码：{response.status_code}")
            return False
    except Exception as e:
        print(f"采集异常：{e}")
        return False
    return grade_pb, grade_zn