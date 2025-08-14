# coding utf-8
import requests

from commFunc import gen_jwt


def get_weather(city_code, query_type, query_date=None):
    jwt_token = gen_jwt()
    headers = {
        'Authorization': f'Bearer {jwt_token}'
    }
    if query_type == 'now':
        response = requests.get(f'https://kq359en4pj.re.qweatherapi.com/v7/weather/now?location={city_code}', headers=headers)
    elif query_type == 'historical':
        response = requests.get(f'https://kq359en4pj.re.qweatherapi.com/v7/historical/weather?location={city_code}&date={query_date}', headers=headers)
    elif query_type == 'warning':
        response = requests.get(f'https://kq359en4pj.re.qweatherapi.com/v7/warning/now?location={city_code}', headers=headers)
    elif query_type == 'aqi':
        lat = city_code[:city_code.find('_')]
        lon = city_code[city_code.find('_') + 1:]
        response = requests.get(f'https://kq359en4pj.re.qweatherapi.com/airquality/v1/current/{lat}/{lon}', headers=headers)
    elif query_type == 'pf':
        lat = city_code[:city_code.find('_')]
        lon = city_code[city_code.find('_') + 1:]
        response = requests.get(f'https://kq359en4pj.re.qweatherapi.com/v7/minutely/5m?location={lon},{lat}', headers=headers)

    data = response.json()

    return data


def get_city_history_weather(city_code, query_date=None):
    try:
        city_weather_info = get_weather(city_code, 'historical', query_date)

        # 检查状态码
        if city_weather_info.get('code') == '200':
            history_data = city_weather_info['weatherDaily'] if city_weather_info.get('weatherDaily') else None
            history_data_hourly = city_weather_info['weatherHourly'] if city_weather_info.get('weatherHourly') else None

            if history_data:
                # 提取数据
                sunrise = history_data["sunrise"]
                sunset = history_data["sunset"]
                moonrise = history_data["moonrise"]
                moonset = history_data["moonset"]
                moonPhase = history_data["moonPhase"]
                tempMax = history_data["tempMax"]
                tempMin = history_data["tempMin"]
                humidity = history_data["humidity"]
                pressure = history_data["pressure"]

                WEATHERICON = {'多云': '☁️', '阴': '⛅', '小雨': '🌦️', '中雨': '🌧️', '大雨': '🌧️', '暴雨': '🌧️💧', '阵雨': '🌦️', '雷阵雨': '⛈️', '小雪': '🌨️',
                            '中雪': '❄️🌨', '大雪': '🌨❄️🌨', '暴雪': '❄️🌨❄️', '晴': '☀️', '雾': '🌫️', '霾': '🌫️', '风': '💨', '雪': '🌨️',
                            '冰雹': '🌨️', '冻雨': '❄️', '沙尘暴': '🌪️'}

                # 根据月相值插入对应的图标
                if moonPhase == '新月':
                    moon_icon = '🌑'
                elif moonPhase == '蛾眉月':
                    moon_icon = '🌒'
                elif moonPhase == '上弦月':
                    moon_icon = '🌓'
                elif moonPhase == '盈凸月':
                    moon_icon = '🌔'
                elif moonPhase == '满月':
                    moon_icon = '🌕'
                elif moonPhase == '亏凸月':
                    moon_icon = '🌖'
                elif moonPhase == '下弦月':
                    moon_icon = '🌗'
                elif moonPhase == '残月':
                    moon_icon = '🌘'
                else:
                    moon_icon = '🌙'

                temperature_dig = int(tempMax)
                # 根据温度选择体感图标
                if temperature_dig < 10:
                    temp_icon = '❄️ 寒冷'
                elif 10 <= temperature_dig <= 29:
                    temp_icon = '🌿 舒适'
                elif 30 <= temperature_dig <= 35:
                    temp_icon = '🥵 较热'
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

                temp_pack, weather_pack, precip_pack, windir_pack, windscale_pack, windspeed, humidity_pack, pressure_pack, weather_icon_pack = [], [], [], [], [], [], [], [], []
                if history_data_hourly:
                    for each in history_data_hourly:
                        temp_pack.append(each['temp'])
                        weather_pack.append(each['text'])
                        precip_pack.append(each['precip'])
                        windir_pack.append(each['windDir'])
                        windscale_pack.append(each['windScale'])
                        windspeed.append(each['windSpeed'])
                        humidity_pack.append(each['humidity'])
                        pressure_pack.append(each['pressure'])
                        if each['text'] in WEATHERICON:
                            weather_icon_pack.append(WEATHERICON[each['text']])
                        else:
                            weather_icon_pack.append('🚫')

                return {
                    'sunrise': sunrise,
                    'sunset': sunset,
                    'moonrise': moonrise,
                    'moonset': moonset,
                    'moonPhase': moonPhase,
                    'tempMax': tempMax,
                    'tempMin': tempMin,
                    'humidity': humidity,
                    'pressure': pressure,
                    'moon_icon': moon_icon,
                    'temp_icon': temp_icon,
                    'humidity_icon': humidity_icon,
                    'temp_hourly': '/'.join(temp_pack),
                    'weather_hourly': '/'.join(weather_pack),
                    'precip_hourly': '/'.join(precip_pack),
                    'windir_hourly': '/'.join(windir_pack),
                    'windscale_hourly': '/'.join(windscale_pack),
                    'windspeed_hourly': '/'.join(windspeed),
                    'humidity_hourly': '/'.join(humidity_pack),
                    'pressure_hourly': '/'.join(pressure_pack),
                    'weather_icon_hourly': '/'.join(weather_icon_pack)
                }
            else:
                return None
        else:
            return None
    except Exception as e:
        # 异常处理
        print(f"无法获取数据: {e}")

    return None


def get_city_now_weather(city_code):
    try:
        city_weather_info = get_weather(city_code, 'now')
        #print(city_weather_info)

        # 检查状态码
        if city_weather_info.get('code') == '200':
            # 直接获取天气信息，不需要使用.get()因为已经是字典了
            now = city_weather_info['now'] if city_weather_info.get('now') else None
            #print(now)

            if now:
                # 提取数据
                obstime = now["obsTime"]  # 获取发布数据时间
                weather = now["text"]  # 天气现象
                weather_icon_id = now['icon'] # 和风天气图标ID
                temp = now["temp"] # 温度
                feelslike = now["feelsLike"] # 体感温度
                winddir = now["windDir"]  # 风向
                windscale = now["windScale"] # 风级
                windspeed = now["windSpeed"]  # 风力
                humidity = now["humidity"]  # 湿度
                precip = now["precip"] # 降水
                pressure = now["pressure"] # 大气压强
                vis = now["vis"] # 能见度
                cloud = now["cloud"] # 云量

                WEATHERICON = {'多云': '☁️', '阴': '⛅', '小雨': '🌦️', '中雨': '🌧️', '大雨': '🌧️', '暴雨': '🌧️💧', '阵雨': '🌦️', '雷阵雨': '⛈️', '小雪': '🌨️',
                            '中雪': '❄️🌨', '大雪': '🌨❄️🌨', '暴雪': '❄️🌨❄️', '晴': '☀️', '雾': '🌫️', '霾': '🌫️', '风': '💨', '雪': '🌨️',
                            '冰雹': '🌨️', '冻雨': '❄️', '沙尘暴': '🌪️'}
                if weather in WEATHERICON:
                    weather_icon = WEATHERICON[weather]
                else:
                    weather_icon = '🚫'

                WINDDIRECTIONICON = {
                    '北风': '⬆️',
                    '南风': '⬇️',
                    '东风': '➡️',
                    '西风': '⬅️',
                    '东北风': '↗️',
                    '东南风': '↘️',
                    '西南风': '↙️',
                    '西北风': '↖️',
                    '静风': '🚩💤'
                }
                winddir_icon = WINDDIRECTIONICON[winddir]

                WINDDIRECTIONICON_HTML = {
                    '北风': '<img width="icon_size" height="icon_size" src="https://img.icons8.com/color/icon_size/north.png" alt="north"/>',
                    '南风': '<img width="icon_size" height="icon_size" src="https://img.icons8.com/color/icon_size/south.png" alt="south"/>',
                    '东风': '<img width="icon_size" height="icon_size" src="https://img.icons8.com/fluency/icon_size/east.png" alt="east"/>',
                    '西风': '<img width="icon_size" height="icon_size" src="https://img.icons8.com/color/icon_size/west.png" alt="west"/>',
                    '东北风': '<img width="icon_size" height="icon_size" src="https://img.icons8.com/color/icon_size/north-east.png" alt="north-east"/>',
                    '东南风': '<img width="icon_size" height="icon_size" src="https://img.icons8.com/color/icon_size/south-east.png" alt="south-east"/>',
                    '西南风': '<img width="icon_size" height="icon_size" src="https://img.icons8.com/color/icon_size/south-west.png" alt="south-west"/>',
                    '西北风': '<img width="icon_size" height="icon_size" src="https://img.icons8.com/color/icon_size/north-west.png" alt="north-west"/>',
                    '静风': '🚩💤'
                }
                winddir_icon_html = WINDDIRECTIONICON_HTML[winddir]

                wind_power_dig = int(windspeed)
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

                temperature_dig = int(temp)
                # 根据温度选择体感图标
                if temperature_dig < 10:
                    temp_icon = '❄️ 寒冷'
                elif 10 <= temperature_dig <= 29:
                    temp_icon = '🌿 舒适'
                elif 30 <= temperature_dig <= 35:
                    temp_icon = '🥵 较热'
                else:
                    temp_icon = '🔥 高温'

                # 根据温度选择体感图标
                feelslike_dig = int(feelslike)
                if feelslike_dig < 10:
                    feelslike_icon = '❄️ 寒冷'
                elif 10 <= feelslike_dig <= 29:
                    feelslike_icon = '🌿 舒适'
                elif 30 <= feelslike_dig <= 35:
                    feelslike_icon = '🥵 较热'
                else:
                    feelslike_icon = '🔥 高温'

                humidity_dig = int(humidity)
                # 根据湿度选择图标
                if humidity_dig < 40:
                    humidity_icon = '🌵 干燥'
                elif 40 <= humidity_dig <= 70:
                    humidity_icon = '💧 舒适'
                else:
                    humidity_icon = '💦 潮湿'

                vis_dig = int(vis)
                # 根据能见度选择图标
                if vis_dig < 10:
                    vis_icon = '🌫️'
                elif 10 <= vis_dig < 20:
                    vis_icon = '🌁'
                else:
                    vis_icon = '🏞️'

                return {
                    'obstime': obstime,
                    'weather': weather,
                    'temp': temp,
                    'feelslike': feelslike,
                    'winddir': winddir,
                    'windscale': windscale,
                    'windspeed': windspeed,
                    'humidity': humidity,
                    'precip': precip,
                    'pressure': pressure,
                    'vis': vis,
                    'cloud': cloud,
                    'weather_icon': weather_icon,
                    'weather_icon_id': weather_icon_id,
                    'temp_icon': temp_icon,
                    'feelslike_icon': feelslike_icon,
                    'wind_icon': wind_icon,
                    'winddir_icon': winddir_icon,
                    'winddir_icon_html': winddir_icon_html,
                    'humidity_icon': humidity_icon,
                    'vis_icon': vis_icon
                }
            else:
                return None
        else:
            return None
    except Exception as e:
        # 异常处理
        print(f"无法获取数据: {e}")

    return None


def get_city_warning_now(city_code):
    try:
        city_weather_info = get_weather(city_code, 'warning')

        # 检查状态码
        if city_weather_info.get('code') == '200':
            warnings = city_weather_info['warning']
            results = []
            for warning in warnings:
                if warning["status"] == 'active':
                    if warning["text"].find('：') != -1:
                        warning["text"] = warning["text"][warning["text"].find("：") + 1:].strip()
                    results.append({
                        'id': warning["id"], # 本条预警的唯一标识
                        'sender': warning["sender"], # 预警发布单位
                        'pubTime': warning['pubTime'], # 预警发布时间
                        'title': warning["title"], # 预警信息标题
                        'startTime': warning["startTime"], # 预警开始时间
                        'endTime': warning["endTime"], # 预警结束时间
                        'status': warning["status"], # 预警状态
                        'severity': warning["severity"], # 预警等级
                        'severityColor': warning["severityColor"], # 预警严重等级颜色
                        'type': warning["type"], # 预警类型
                        'typeName': warning["typeName"], # 预警类型名称
                        'urgency': warning["urgency"], # 预警信息的紧迫程度
                        'certainty': warning["certainty"], # 预警信息的确定性
                        'text': warning["text"] # 预警信息
                    })

            return results

        return None
    except Exception as e:
        # 异常处理
        print(f"无法获取数据: {e}")

    return None


def get_city_aqi(city_code):
    try:
        city_weather_info = get_weather(city_code, 'aqi')

        # 检查状态码
        if city_weather_info['indexes']:
            results, sub_results = {}, {}
            results["name"] = city_weather_info['indexes'][0]['name']
            results["aqi"] = city_weather_info['indexes'][0]['aqi']
            results["level"] = city_weather_info['indexes'][0]['level']
            results["category"] = city_weather_info['indexes'][0]['category']
            results["color"] = city_weather_info['indexes'][0]['color']
            results["primaryPollutant"] = city_weather_info['indexes'][0]['primaryPollutant']
            results["health"] = city_weather_info['indexes'][0]['health']['effect'] + city_weather_info['indexes'][0]['health']['advice']['sensitivePopulation']
            results["primaryPollutant_vu"] = None
            if results["health"].endswith("。"):
                results["health"] = results["health"][:-1]
            for each in city_weather_info['pollutants']:
                if each['name'] == results['primaryPollutant']:
                    results['primaryPollutant_vu'] = each['concentration']
                else:
                    sub_results[each['name']] = each['concentration']
            results['sub_pollutants'] = sub_results

            return results

        return None
    except Exception as e:
        # 异常处理
        print(f"无法获取数据: {e}")

    return None


def get_city_pf_weather(city_code):
    try:
        city_weather_info = get_weather(city_code, 'pf')

        # 检查状态码
        if city_weather_info.get('code') == '200':

            return city_weather_info['summary']

        return None
    except Exception as e:
        # 异常处理
        print(f"无法获取数据: {e}")

    return None
