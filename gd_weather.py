# coding utf-8
import re

import requests


def get_weather(city_code):
    url = 'https://restapi.amap.com/v3/weather/weatherInfo?parameters'
    params_realtime = {
        'key':'0befa0ca3650bc4cbf6d9d2607b13001',
        'city':city_code,
        'extensions':'base'
    }
    params_estimate = {
        'key':'0befa0ca3650bc4cbf6d9d2607b13001',
        'city':city_code,
        'extensions':'all'
    }

    res = requests.get(url=url,params=params_realtime) # 实时天气
    #res = requests.get(url=url,params=params_estimate) # 预报天气
    weather_info = res.json()

    return weather_info


def get_city_weather(city_code):
    # 输入验证
    if not isinstance(city_code, str) or not city_code.isdigit():
        raise ValueError("Invalid city code")

    try:
        city_weather_info = get_weather(city_code)

        # 检查状态码
        if city_weather_info.get('status') == '1':
            # 直接获取天气信息，不需要使用.get()因为已经是字典了
            live_data = city_weather_info['lives'][0] if city_weather_info.get('lives') else None

            if live_data:
                # 提取数据
                province = live_data["province"]  # 获取省份
                city = live_data["city"]  # 获取城市
                adcode = live_data["adcode"]  # 获取城市编码
                reporttime = live_data["reporttime"]  # 获取发布数据时间
                weather = live_data["weather"]  # 天气现象
                temperature = live_data["temperature"]  # 温度
                winddirection = live_data["winddirection"]  # 风向
                windpower = live_data["windpower"]  # 风力
                humidity = live_data["humidity"]  # 湿度

                # 使用正则表达式提取数字部分
                wind_power_dig = re.search(r'\d+', windpower)
                if wind_power_dig:
                    wind_power_dig = int(wind_power_dig.group())
                else:
                    wind_power_dig = 0
                # 根据风力强度选择图标
                if wind_power_dig < 5:
                    wind_icon = '🍃 微风'
                elif 5 <= wind_power_dig < 10:
                    wind_icon = '🌬️ 轻风'
                elif 10 <= wind_power_dig < 20:
                    wind_icon = '🌬️ 和风'
                elif 20 <= wind_power_dig < 30:
                    wind_icon = '💨 强风'
                elif 30 <= wind_power_dig < 40:
                    wind_icon = '🌪️ 大风'
                else:
                    wind_icon = '🌀 暴风'

                temperature_dig = int(temperature)
                # 根据温度选择体感图标
                if temperature_dig < 10:
                    temp_icon = '❄️ 寒冷'
                elif 10 <= temperature_dig <= 25:
                    temp_icon = '🌡️ 舒适'
                elif 26 <= temperature_dig <= 35:
                    temp_icon = '⚠️ 较热'
                else:
                    temp_icon = '🔥 高温'

                humidity_dig = int(humidity)
                # 根据湿度选择图标
                if humidity_dig < 40:
                    humidity_icon = '🌵 干燥'
                elif 40 <= humidity_dig <= 70:
                    humidity_icon = '💧 舒适'
                else:
                    humidity_icon = '💦 潮湿'

                return {
                    'province': province,
                    'city': city,
                    'adcode': adcode,
                    'reporttime': reporttime,
                    'weather': weather,
                    'temperature': temperature,
                    'winddirection': winddirection,
                    'windpower': windpower,
                    'humidity': humidity,
                    'wind_icon': wind_icon,
                    'temp_icon': temp_icon,
                    'humidity_icon': humidity_icon
                }

    except Exception as e:
        # 异常处理
        print(f"Error fetching weather data: {e}")

    return None
