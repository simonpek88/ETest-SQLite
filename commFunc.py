# coding utf-8
import base64
import logging
import os
import random
import time
from hashlib import md5

import pymysql
import qianfan  # type: ignore
from Crypto import Random
from Crypto.Cipher import AES
from openai import OpenAI  # type: ignore

# cSpell:ignoreRegExp /[^\s]{16,}/
# cSpell:ignoreRegExp /\b[A-Z]{3,15}\b/g
# cSpell:ignoreRegExp /\b[A-Z]\b/g


def pad(data):
    # 计算需要填充的字节数
    length = 16 - (len(data) % 16)

    # 将数据编码为utf-8格式
    # 并将填充字符（长度为length）重复length次后编码为utf-8格式
    # 最后将编码后的数据和填充数据拼接返回
    return data.encode(encoding="utf-8") + (chr(length) * length).encode(encoding="utf-8")


def unpad(data):
    # 判断data的最后一个元素是否为整数
    # 如果是整数，则直接作为填充长度
    # 如果不是整数，则通过ord函数获取其ASCII码值作为填充长度
    return data[:-(data[-1] if type(data[-1]) == int else ord(data[-1]))]


def bytes_to_key(data, salt, output=48):
    # 将输入数据编码为utf-8格式
    data = data.encode(encoding="utf-8")
    # 断言盐的长度为8
    assert len(salt) == 8, len(salt)
    # 将盐附加到数据后面
    data += salt
    # 使用MD5算法对数据进行哈希处理，并获取哈希值的二进制表示
    key = md5(data).digest()
    final_key = key
    # 当生成的密钥长度小于指定输出长度时，继续生成密钥
    while len(final_key) < output:
        # 使用MD5算法对密钥和数据再次进行哈希处理，并获取哈希值的二进制表示
        key = md5(key + data).digest()
        # 将新生成的密钥附加到最终密钥后面
        final_key += key

    # 返回指定长度的最终密钥
    return final_key[:output]


def encrypt(message, passphrase):
    # 生成一个随机的8个字节的盐
    salt = Random.new().read(8)

    # 使用bytes_to_key函数生成密钥和IV
    key_iv = bytes_to_key(passphrase, salt, 32 + 16)

    # 分离密钥和IV
    key = key_iv[:32]
    iv = key_iv[32:]

    # 创建一个AES对象，使用CBC模式
    aes = AES.new(key, AES.MODE_CBC, iv)

    # 对消息进行加密，并在加密前添加"Salted__"前缀和盐
    # 加密后，使用base64编码返回结果
    return base64.b64encode(b"Salted__" + salt + aes.encrypt(pad(message)))


def decrypt(encrypted, passphrase):
    # 对加密数据进行base64解码
    encrypted = base64.b64decode(encrypted)

    # 判断加密数据前8个字节是否为"Salted__"
    assert encrypted[0:8] == b"Salted__"

    # 提取盐值，盐值位于"Salted__"之后，长度为8个字节
    salt = encrypted[8:16]

    # 使用bytes_to_key函数生成密钥和IV
    key_iv = bytes_to_key(passphrase, salt, 32 + 16)

    # 分离密钥和IV
    key = key_iv[:32]
    iv = key_iv[32:]

    # 创建一个AES对象，使用CBC模式
    aes = AES.new(key, AES.MODE_CBC, iv)

    # 对加密数据进行解密，并去除前16个字节（包括"Salted__"和盐值）
    # 然后对解密后的数据进行去填充处理
    return unpad(aes.decrypt(encrypted[16:]))


def getEncryptKeys(keyname):
    # 从数据库中查询键名为'key_text'的加密密钥
    sql = "SELECT aikey from aikeys where keyname = 'key_text'"
    # 执行SQL查询并获取结果中的第一个值作为密钥
    key = execute_sql(cur2, sql)[0][0]

    # 构建SQL查询语句，用于查询指定键名的加密数据
    sql = f"SELECT aikey from aikeys where keyname = '{keyname}'"
    # 执行SQL查询并获取结果中的第一个值作为加密数据
    encrypt_data = execute_sql(cur2, sql)[0][0]

    # 使用密钥对加密数据进行解密
    #encrypt_data = encrypt(data, key).decode("utf-8")
    decrypt_data = decrypt(encrypt_data, key).decode("utf-8")

    # 返回解密后的数据
    return decrypt_data


# noinspection GrazieInspection
def getUserEDKeys(userStr, edType):
    # 初始化加密后的字符串为空
    strED = ""
    # 构建SQL查询语句，从数据库中获取密钥
    sql = "SELECT aikey from aikeys where keyname = 'key_text'"
    # 执行SQL查询语句，获取密钥
    key = execute_sql(cur2, sql)[0][0]
    # 判断加密类型是否为"enc"（加密）
    if edType == "enc":
        # 对用户输入字符串进行加密，并将加密后的字符串解码为UTF-8格式
        strED = encrypt(userStr, key).decode("utf-8")
    # 判断加密类型是否为"dec"（解密）
    elif edType == "dec":
        # 对用户输入字符串进行解密，并将解密后的字符串解码为UTF-8格式
        strED = decrypt(userStr, key).decode("utf-8")

    # 返回加密或解密后的字符串
    return strED


def generContent(ques, option, quesType):
    optionStr, content = "", ""
    for each in option:
        optionStr = optionStr + each + " "
    optionStr = optionStr.strip()
    if quesType == "单选题" or quesType == "多选题":
        content = f"\n下面是考试题目:\n<题目>:{ques}\n<题型>:{quesType}\n<选项>:{optionStr}"
    else:
        content = f"\n下面是考试题目:\n<题目>:{ques}\n<题型>:{quesType}"

    return content


def deepseek_AI(ques, option, quesType, useModel='deepseek-chat'):
    # 模型版本可选deepseek-reasoner(R1)和deepseek-chat(V3) 默认V3
    try:
        aikey = getEncryptKeys("deepseek")
        contentStr = generContent(ques, option, quesType)
        if contentStr:
            client = OpenAI(api_key=aikey, base_url="https://api.deepseek.com")
            response = client.chat.completions.create(
                model=useModel,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专家，我会给你<题目>和<题型>和<选项>，请依据你的行业知识和给定的选项，选择正确的答案，并给出解题推导过程。要求：\n1. 给出每个选项的对错, 判断题和填空题直接给出答案和解析过程\n2. 生成内容应清晰、精确、详尽并易于理解\n3. 输出如果有国家标准或行业规范需要提供来源出处, 若能检索到具体出处, 需要精确到是第几条, 并引用\n4. 不输出原题, 但要输出选项, 并给出每个选项的解析过程\n5. 解析内容每行不要超过40个字, 但是可以多行\n6. 着重显示正确的答案并给出一个详尽的小结"
                    },
                    {
                        "role": "user",
                        "content": f"{contentStr}"
                    },
                ],
                stream=False
            )
            return response.choices[0].message.content
        else:
            return ""
    except Exception as e:
        logging.error(f"An error occurred while calling Deepseek AI: {e}")
        return ""


def deepseek_AI_GenerQues(reference, quesType, quesCount, useModel='deepseek-chat'):
    # 模型版本可选deepseek-reasoner(R1)和deepseek-chat(V3) 默认V3
    aikey = getEncryptKeys("deepseek")
    prompt = f"您是一名老师，需要出{quesCount}道{quesType}类型的试题，请按照以下要求进行：\n1. 依据参考资料给出的内容出题\n2. 基于生成的试题和标准答案逐步推导，输出相应的试题解答，尽可能简明扼要\n3. 填空题没有选项\n4. 判断题选项为A. 正确和B. 错误\n5. 结尾有分割线，同一道题内没有分割线\n6. 单选题和多选题标准答案只含选项，不含内容\n7. 必须是{quesType}题型\n8. 题干中不显示选项"
    prompt = prompt + "\n请按照以下格式出题\n题型: \n试题: \n选项: \n标准答案: \n试题解析: \n\n按以下内容出题\n参考资料:\n"
    client = OpenAI(api_key=aikey, base_url="https://api.deepseek.com")
    response = client.chat.completions.create(
        model=useModel,
        messages=[
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": reference
            },
        ],
        stream=False
    )

    return response.choices[0].message.content


def qianfan_AI(ques, AImodel, option, quesType):
    aikeyAK = getEncryptKeys("qianfan_ak")
    aikeySK = getEncryptKeys("qianfan_sk")
    contentStr = generContent(ques, option, quesType)
    if contentStr != "":
        os.environ["QIANFAN_ACCESS_KEY"] = aikeyAK
        os.environ["QIANFAN_SECRET_KEY"] = aikeySK
        #prompt = "我会给你<题目>和<题型>和<选项>，请依据你的行业知识和给定的选项，选择正确的答案，并给出对应的做题推导过程，输出内容请严格按以下要求执行：\n推导过程逐步思考，从知识本身出发给出客观的解析内容，但只输出核心内容\n输出内容尽量【简洁明了】，但不能缺失核心推导过程\n输出如果有国家标准或行业规范需要提供来源出处，若能检索到具体出处，需要精确到是【第几条】，并引用\n最后做一个小结，需要强调正确答案是什么，并输出详细推导过程\n判断题直接给出对错并输出推导过程\n填空题直接给出答案并输出推导过程"
        prompt = "我会给你<题目>和<题型>和<选项>，请依据你的行业知识和给定的选项，选择正确的答案，并给出解题推导过程。请注意，推导过程必须逐步思考，从知识本身出发给出客观的解析内容，但仅限于核心内容。输入内容必须简明扼要，但不能缺少核心推导过程。如果有国家标准或行业规范需要引用，请提供相关出处，若能检索到具体出处，需要精确到是第几条，并引用。最后，总结正解，强调正确答案并提供详尽的推导过程。对于判断题直接给出对错并解释推断过程。对于填空题直接给出答案并解释推导过程。"
        chat_comp = qianfan.ChatCompletion()
        resp = chat_comp.do(model=f"{AImodel}", messages=[{
            "role": "user",
            "content": f"{prompt}{contentStr}"
        }])
        return resp["body"]["result"]
    else:
        return ""


def xunfei_xh_AI(ques, option, quesType):
    aikey = getEncryptKeys("xfxh")
    contentStr = generContent(ques, option, quesType)
    if contentStr != "":
        #prompt = "我会给你<题目>和<题型>和<选项>，请根据你的行业知识以及给你的选项选出正确答案，并给出对应的做题推导过程，输出内容请严格按以下要求执行：\n以markdown的格式输出\n推导过程逐步思考，从知识本身出发给出客观的解析内容，但只输出核心内容\n输出内容尽量【简洁明了】，但不能缺失核心推导过程\n输出如果有国家标准或行业规范需要提供来源出处，若能检索到具体出处，需要精确到是【第几条】，并引用\n最后做一个小结，需要强调正确答案是什么，并输出详细推导过程\n判断题直接给出正确或错误的答案，并输出推导过程\n填空题直接给出答案并输出推导过程\n输出每行不要超过40个字"
        prompt = "我会给你<题目>和<题型>和<选项>，请依据你的行业知识和给定的选项，选择正确的答案，并给出解题推导过程。请注意，推导过程必须逐步思考，从知识本身出发给出客观的解析内容，但仅限于核心内容。输入内容必须简明扼要，但不能缺少核心推导过程。如果有国家标准或行业规范需要引用，请提供相关出处，若能检索到具体出处，需要精确到是第几条，并引用。最后，总结正解，强调正确答案并提供详尽的推导过程。对于判断题直接给出对错并解释推断过程。对于填空题直接给出答案并解释推导过程。"
        client = OpenAI(api_key=aikey, base_url='https://spark-api-open.xf-yun.com/v1')
        completion = client.chat.completions.create(
            model='4.0Ultra',
            messages=[
                {
                    "role": "user",
                    "content": f"{prompt}{contentStr}"
                }
            ]
        )
        if completion.code == 0:
            return completion.choices[0].message.content
        else:
            return ""
    else:
        return ""


def xunfei_xh_AI_GenerQues(reference, quesType, quesCount):
    aikey = getEncryptKeys("xfxh")
    prompt = f"您是一名老师，需要出{quesCount}道{quesType}类型的试题，请按照以下要求进行：\n1. 依据参考资料给出的内容出题\n2. 基于生成的试题和标准答案逐步推导，输出相应的试题解答，尽可能简明扼要\n3. 填空题没有选项\n4. 判断题选项为A. 正确和B. 错误\n5. 结尾有分割线，同一道题内没有分割线\n6. 单选题和多选题标准答案只含选项，不含内容\n7. 必须是{quesType}题型\n8. 题干中不显示选项\n9. 选项中不要加强调符号"
    prompt = prompt + "\n请按照以下格式出题\n题型: \n试题: \n选项: \n标准答案: \n试题解析: \n\n按以下内容出题\n参考资料:\n"
    client = OpenAI(api_key=aikey, base_url='https://spark-api-open.xf-yun.com/v1')
    completion = client.chat.completions.create(
        model='4.0Ultra',
        messages=[
            {
                "role": "user",
                "content": f"{prompt}{reference}"
            }
        ]
    )
    if completion.code == 0:
        return completion.choices[0].message.content
    else:
        return ""


def xunfei_xh_AI_fib(ques, ques2):
    aikey = getEncryptKeys("xfxh")
    prompt = "我给你一行话，请根据我给你的参考资料判断提供的答案替换参考资料中括号内的内容后是否正确，不做推导过程，只输出正确还是错误，格式如下:<参考资料>:\n\n<答案>:\n\n"
    client = OpenAI(api_key=aikey, base_url='https://spark-api-open.xf-yun.com/v1')
    completion = client.chat.completions.create(
        model='4.0Ultra',
        messages=[
            {
                "role": "user",
                "content": f"{prompt}\n<参考资料>:\n\n{ques2}\n\n<答案>:\n\n{ques}"
            }
        ]
    )
    if completion.code == 0:
        return completion.choices[0].message.content
    else:
        return ""


def qianfan_AI_GenerQues(reference, quesType, quesCount, AImodel):
    aikeyAK = getEncryptKeys("qianfan_ak")
    aikeySK = getEncryptKeys("qianfan_sk")
    os.environ["QIANFAN_ACCESS_KEY"] = aikeyAK
    os.environ["QIANFAN_SECRET_KEY"] = aikeySK
    prompt = f"您是一名老师，需要出{quesCount}道{quesType}类型的试题，请按照以下要求进行：\n1. 依据参考资料给出的内容出题\n2. 基于生成的试题和标准答案逐步推导，输出相应的试题解答，尽可能简明扼要\n3. 填空题没有选项\n4. 判断题选项为A. 正确和B. 错误\n5. 结尾有分割线，同一道题内没有分割线\n6. 单选题和多选题标准答案只含选项，不含内容\n7. 必须是{quesType}题型\n8. 题干中不显示选项"
    prompt = prompt + "\n请按照以下格式出题\n题型: \n试题: \n选项: \n标准答案: \n试题解析: \n\n按以下内容出题\n参考资料:\n"
    chat_comp = qianfan.ChatCompletion()
    resp = chat_comp.do(model=f"{AImodel}", messages=[{
        "role": "user",
        "content": f"{prompt}{reference}"
    }])

    return resp["body"]["result"]


def CreateExamTable(tablename, examRandom):
    # 查询数据库中是否存在该表（MySQL）
    sql = f"SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = '{tablename}'"
    cur2.execute(sql)
    tempTable = cur2.fetchone()

    flagTableExist = bool(tempTable)

    if flagTableExist:
        if tablename.find("exam_final_") != -1 or examRandom:
            # 如果表存在且需要重建，则删除旧表
            execute_sql_and_commit(conn2, cur2, f"DROP TABLE IF EXISTS {tablename}")
            flagTableExist = False
    else:
        flagTableExist = False

    if not flagTableExist:
        if tablename.find("exam_final_") != -1:
            # 创建 exam_final_xxx 表结构
            sql = f"""CREATE TABLE `{tablename}` (
                        ID INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        Question TEXT NOT NULL,
                        qOption TEXT,
                        qAnswer TEXT NOT NULL,
                        qType TINYTEXT NOT NULL,
                        qAnalysis TEXT,
                        userAnswer TINYTEXT,
                        userName INT DEFAULT 0,
                        SourceType TINYTEXT
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"""

        elif tablename.find("exam_") != -1:
            # 创建 exam_xxx 表结构
            sql = f"""CREATE TABLE `{tablename}` (
                        ID INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        Question TEXT NOT NULL,
                        qOption TEXT,
                        qAnswer TEXT NOT NULL,
                        qType TINYTEXT NOT NULL,
                        qAnalysis TEXT,
                        randomID INT NOT NULL,
                        SourceType TINYTEXT
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"""

        # 执行建表语句
        cur2.execute(sql)
        conn2.commit()
        return False  # 表被新创建了
    else:
        return True   # 表已存在


# noinspection PyBroadException
def execute_sql(cur, sql, params=None):
    try:
        # 参数化查询以预防SQL注入
        if params:
            cur.execute(sql, params)
        else:
            # 如果sql是外部输入的，请确保它是安全的，或者使用其他方法来避免SQL注入
            cur.execute(sql)
        return cur.fetchall()
    except Exception as e:
        logging.error(f"An error occurred while executing SQL: {sql}, Error: {e}")
        return []


# noinspection PyBroadException
def execute_sql_and_commit(conn, cur, sql, params=None):
    try:
        # 参数化查询以预防SQL注入
        if params:
            cur.execute(sql, params)
        else:
            # 如果sql是外部输入的，请确保它是安全的，或者使用其他方法来避免SQL注入
            cur.execute(sql)
        conn.commit()
        return True
    except Exception as e:
        logging.error(f"An error occurred while executing SQL: {sql}, Error: {e}")
        return False


def getParam(paramName, StationCN):
    # 构造SQL查询语句
    sql = f"SELECT param from Setup_{StationCN} where paramName = '{paramName}'"
    # 执行SQL查询语句
    cur2.execute(sql)
    # 获取查询结果
    table = cur2.fetchone()
    # 判断查询结果是否为空
    if table:
        # 如果不为空，则取查询结果的第一个值作为参数
        param = table[0]
    else:
        # 如果为空，则参数值为0
        param = 0

    # 返回参数值
    return param


def getChapterRatio(StationCN, qAff, examType):
    # 判断考试类型
    if examType == "training":
        # 如果是练习类型，则选择chapterRatio字段
        sql = "SELECT chapterRatio from questionAff where StationCN = '" + StationCN + "' and chapterName = '" + qAff + "'"
    else:
        # 如果是其他类型，则选择examChapterRatio字段
        sql = "SELECT examChapterRatio from questionAff where StationCN = '" + StationCN + "' and chapterName = '" + qAff + "'"
    # 执行SQL查询
    quesCRTable = execute_sql(cur2, sql)
    # 判断查询结果是否为空
    if quesCRTable:
        # 如果不为空，获取第一个结果的第一列值
        cr = quesCRTable[0][0]
    else:
        # 如果为空，则默认比率为5
        cr = 5

    # 返回比率值
    return cr


# noinspection DuplicatedCode
def GenerExam(qAffPack, StationCN, userName, examName, examType, quesType, examRandom, flagNewOnly):
    if examRandom:
        examTable = f"exam_{StationCN}_{userName}_{examName}"
        examFinalTable = f"exam_final_{StationCN}_{userName}_{examName}"
    else:
        examTable = f"exam_{StationCN}_{examName}"
        examFinalTable = f"exam_final_{StationCN}_{examName}"
    flagTableExist = CreateExamTable(examTable, examRandom)
    if not flagTableExist:
        for k in quesType:
            if flagNewOnly and examType == "training":
                sql = f"SELECT Question, qOption, qAnswer, qType, qAnalysis, chapterName, SourceType from questions where (ID not in (SELECT cid from studyinfo where questable = 'questions' and userName = {userName}) and StationCN = '{StationCN}' and qType = '{k[0]}') and (chapterName = '"
            else:
                sql = f"SELECT Question, qOption, qAnswer, qType, qAnalysis, chapterName, SourceType from questions where (StationCN = '{StationCN}' and qType = '{k[0]}') and (chapterName = '"
            for each in qAffPack:
                if each != "错题集" and each != "公共题库":
                    sql = sql + each + "' or chapterName = '"
            sql = sql[:-20] + "')"
            rows = execute_sql(cur2, sql)
            for row in rows:
                chapterRatio = getChapterRatio(StationCN, row[5], examType)
                sql = f"INSERT INTO {examTable}(Question, qOption, qAnswer, qType, qAnalysis, randomID, SourceType) VALUES('{row[0]}', '{row[1]}', '{row[2]}', '{row[3]}', '{row[4]}', {random.randint(int(1000 - 100 * chapterRatio), int(1100 - 100 * chapterRatio))}, '{row[6]}')"
                #sql = f"INSERT INTO {examTable}(Question, qOption, qAnswer, qType, qAnalysis, randomID, SourceType) VALUES('{row[0]}', '{row[1]}', '{row[2]}', '{row[3]}', '{row[4]}', {random.randint(1, 1100)}, '{row[6]}')"
                execute_sql_and_commit(conn2, cur2, sql)
        if "错题集" in qAffPack and examType == "training":
            chapterRatio = getChapterRatio(StationCN, "错题集", examType)
            for k in quesType:
                sql = f"SELECT Question, qOption, qAnswer, qType, qAnalysis, SourceType from morepractise where qType = '{k[0]}' and userName = {userName} order by WrongTime DESC"
                rows = execute_sql(cur2, sql)
                for row in rows:
                    sql = "SELECT ID from " + examTable + " where Question = '" + row[0] + "'"
                    if not execute_sql(cur2, sql):
                        sql = f"INSERT INTO {examTable}(Question, qOption, qAnswer, qType, qAnalysis, randomID, SourceType) VALUES('{row[0]}', '{row[1]}', '{row[2]}', '{row[3]}', '{row[4]}', {random.randint(int(1000 - 100 * chapterRatio), int(1100 - 100 * chapterRatio))}, '{row[5]}')"
                        execute_sql_and_commit(conn2, cur2, sql)
        if "关注题集" in qAffPack and examType == "training":
            chapterRatio = getChapterRatio(StationCN, "关注题集", examType)
            for k in quesType:
                sql = f"SELECT Question, qOption, qAnswer, qType, qAnalysis, SourceType from favques where qType = '{k[0]}' and userName = {userName} order by ID"
                rows = execute_sql(cur2, sql)
                for row in rows:
                    sql = "SELECT ID from " + examTable + " where Question = '" + row[0] + "'"
                    if not execute_sql(cur2, sql):
                        sql = f"INSERT INTO {examTable}(Question, qOption, qAnswer, qType, qAnalysis, randomID, SourceType) VALUES('{row[0]}', '{row[1]}', '{row[2]}', '{row[3]}', '{row[4]}', {random.randint(int(1000 - 100 * chapterRatio), int(1100 - 100 * chapterRatio))}, '{row[5]}')"
                        execute_sql_and_commit(conn2, cur2, sql)
        if '公共题库' in qAffPack:
            chapterRatio = getChapterRatio(StationCN, "公共题库", examType)
            for k in quesType:
                if flagNewOnly and examType == "training":
                    sql = f"SELECT Question, qOption, qAnswer, qType, qAnalysis, SourceType from commquestions where ID not in (SELECT cid from studyinfo where questable = 'commquestions' and userName = {userName}) and qType = '{k[0]}' order by ID"
                else:
                    sql = f"SELECT Question, qOption, qAnswer, qType, qAnalysis, SourceType from commquestions where qType = '{k[0]}' order by ID"
                rows = execute_sql(cur2, sql)
                for row in rows:
                    sql = "SELECT ID from " + examTable + " where Question = '" + row[0] + "'"
                    if not execute_sql(cur2, sql):
                        sql = f"INSERT INTO {examTable}(Question, qOption, qAnswer, qType, qAnalysis, randomID, SourceType) VALUES('{row[0]}', '{row[1]}', '{row[2]}', '{row[3]}', '{row[4]}', {random.randint(int(1000 - 100 * chapterRatio), int(1100 - 100 * chapterRatio))}, '{row[5]}')"
                        #sql = f"INSERT INTO {examTable}(Question, qOption, qAnswer, qType, qAnalysis, randomID, SourceType) VALUES('{row[0]}', '{row[1]}', '{row[2]}', '{row[3]}', '{row[4]}', {random.randint(1, 1100)}, '{row[5]}')"
                        execute_sql_and_commit(conn2, cur2, sql)
    CreateExamTable(examFinalTable, examRandom)
    for k in quesType:
        sql = f"INSERT INTO {examFinalTable}(Question, qOption, qAnswer, qType, qAnalysis, SourceType) SELECT Question, qOption, qAnswer, qType, qAnalysis, SourceType from {examTable} where qType = '{k[0]}' order by randomID limit 0, {k[1]}"
        execute_sql_and_commit(conn2, cur2, sql)
        sql = f"SELECT MAX(id) from {examFinalTable}"
        auto_id = execute_sql(cur2, sql)[0][0]
        execute_sql_and_commit(conn2, cur2, f"ALTER TABLE {examFinalTable} AUTO_INCREMENT = {auto_id + 1}")
    quesCS = getParam("考题总数", StationCN)
    sql = "SELECT Count(ID) from " + examFinalTable
    quesCount = execute_sql(cur2, sql)[0][0]
    if quesCount == quesCS or (examType == 'training' and quesCount > 0):
        return True, quesCount, examTable, examFinalTable
    else:
        return False, quesCount, examTable, examFinalTable


def updateActionUser(activeUser, actionUser, loginTime):
    sql = f"UPDATE users SET actionUser = '{actionUser}', activeTime_session = {int(time.time()) - loginTime} where userName = {activeUser}"
    execute_sql_and_commit(conn2, cur2, sql)


def updatePyFileinfo():
    for root, dirs, files in os.walk("./"):
        # 当遍历到根目录时
        if root == "./":
            for file in files:
                # 判断文件后缀是否为.py且文件名不以"test-"开头
                if os.path.splitext(file)[1].lower() == '.py' and not os.path.splitext(file)[0].lower().startswith("test-"):
                    # 获取文件的完整路径
                    pathIn = os.path.join(root, file)
                    # 获取文件名（不含后缀）
                    pyFile = os.path.splitext(file)[0]
                    # 获取文件的最后修改时间（时间戳）
                    file_mtime = int(os.path.getmtime(pathIn))
                    # 构造SQL查询语句，从verinfo表中查询当前文件的信息
                    sql = f"SELECT ID, pyLM from verinfo where pyFile = '{pyFile}'"
                    # 执行SQL查询语句
                    rows = execute_sql(cur2, sql)
                    # 如果查询结果为空，表示该文件在verinfo表中没有记录
                    if not rows:
                        # 构造SQL插入语句，将文件信息插入到verinfo表中
                        sql = f"INSERT INTO verinfo(pyFile, pyLM, pyMC) VALUES('{pyFile}', {int(time.time())}, 1)"
                        # 执行SQL插入语句并提交事务
                        execute_sql_and_commit(conn2, cur2, sql)
                    # 如果查询结果不为空，但文件的最后修改时间与verinfo表中记录的时间不一致
                    elif rows[0][1] != file_mtime:
                        # 构造SQL更新语句，更新verinfo表中该文件的信息
                        sql = f"UPDATE verinfo SET pyLM = {file_mtime}, pyMC = pyMC + 1 where pyFile = '{pyFile}'"
                        # 执行SQL更新语句并提交事务
                        execute_sql_and_commit(conn2, cur2, sql)


conn2 = pymysql.connect(
host='localhost',
port=3001,
user='root',
password='7745',
database='etest-mysql',
charset='utf8mb4',
autocommit=True
)
cur2 = conn2.cursor()
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
