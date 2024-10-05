# coding UTF-8
import base64
import os
import random
import time
from hashlib import md5

import apsw
import qianfan
from Crypto import Random
from Crypto.Cipher import AES
from openai import OpenAI

# cSpell:ignoreRegExp /[^\s]{16,}/
# cSpell:ignoreRegExp /\b[A-Z]{3,15}\b/g


def pad(data):
    length = 16 - (len(data) % 16)

    return data.encode(encoding="utf-8") + (chr(length) * length).encode(encoding="utf-8")


def unpad(data):
    return data[:-(data[-1] if type(data[-1]) == int else ord(data[-1]))]


def bytes_to_key(data, salt, output=48):
    data = data.encode(encoding="utf-8")
    assert len(salt) == 8, len(salt)
    data += salt
    key = md5(data).digest()
    final_key = key
    while len(final_key) < output:
        key = md5(key + data).digest()
        final_key += key

    return final_key[:output]


def encrypt(message, passphrase):
    salt = Random.new().read(8)
    key_iv = bytes_to_key(passphrase, salt, 32 + 16)
    key = key_iv[:32]
    iv = key_iv[32:]
    aes = AES.new(key, AES.MODE_CBC, iv)

    return base64.b64encode(b"Salted__" + salt + aes.encrypt(pad(message)))


def decrypt(encrypted, passphrase):
    encrypted = base64.b64decode(encrypted)
    assert encrypted[0:8] == b"Salted__"
    salt = encrypted[8:16]
    key_iv = bytes_to_key(passphrase, salt, 32 + 16)
    key = key_iv[:32]
    iv = key_iv[32:]
    aes = AES.new(key, AES.MODE_CBC, iv)

    return unpad(aes.decrypt(encrypted[16:]))


def getEncryptKeys(keyname):
    SQL = "SELECT aikey from aikeys where keyname = 'key_text'"
    key = mdb_sel(cur, SQL)[0][0]
    SQL = f"SELECT aikey from aikeys where keyname = '{keyname}'"
    encrypt_data = mdb_sel(cur, SQL)[0][0]
    #encrypt_data = encrypt(data, key).decode("utf-8")
    decrypt_data = decrypt(encrypt_data, key).decode("utf-8")

    return decrypt_data


def getKeys(keyname):
    SQL = f"SELECT aikey from aikeys where keyname = '{keyname}'"
    ai_key = mdb_sel(cur, SQL)[0][0]

    return ai_key


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


def deepseek_AI(ques, option, quesType):
    aikey = getEncryptKeys("deepseek")
    contentStr = generContent(ques, option, quesType)
    if contentStr != "":
        client = OpenAI(api_key=aikey, base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model="deepseek-chat",
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


def xunfei_xh_AI_fib(ques, ques2):
    aikey = getEncryptKeys("xfxh")
    prompt = "我会给你一行话，请根据我给你的参考资料结合上下文判断()中的内容是否正确，不做推导过程，只输出正确还是错误，格式如下:<参考资料>:\n\n<判断内容>:\n\n"
    client = OpenAI(api_key=aikey, base_url='https://spark-api-open.xf-yun.com/v1')
    completion = client.chat.completions.create(
        model='4.0Ultra',
        messages=[
            {
                "role": "user",
                "content": f"{prompt}\n<参考资料>:\n\n{ques2}\n\n<判断内容>:\n\n{ques}"
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
    prompt = f"您是一名老师，需要出{quesCount}道{quesType}类型的试题，请按照以下要求进行：\n1. 依据参考资料给出的内容出题\n2. 基于生成的试题和标准答案逐步推导，输出相应的试题解答，尽可能简明扼要\n3. 填空题没有选项\n4. 判断题选项为A. 正确和B. 错误\n5. 结尾有分割线，同一道题内没有分割线\n6. 单选题和多选题标准答案只含选项，不含内容\n7. 必须是特定题型的试题"
    prompt = prompt + "\n请按照以下格式出题\n题型: \n试题: \n选项: \n标准答案: \n试题解析: \n\n按以下内容出题\n参考资料:\n"
    chat_comp = qianfan.ChatCompletion()
    resp = chat_comp.do(model=f"{AImodel}", messages=[{
        "role": "user",
        "content": f"{prompt}{reference}"
    }])

    return resp["body"]["result"]


def outputErrorInfo(SQL):
    print(f"SQL:[{SQL} ERROR! Please Check It!")


def CreateExamTable(tablename, examRandom):
    SQL = "SELECT * from sqlite_master where type = 'table' and name = '" + tablename + "'"
    tempTable = mdb_sel(cur, SQL)
    if tempTable:
        if tablename.find("exam_final_") != -1 or examRandom:
            mdb_del(conn, cur, SQL=f"DROP TABLE {tablename}")
            flagTableExist = False
        else:
            flagTableExist = True
    else:
        flagTableExist = False
    if not flagTableExist:
        if tablename.find("exam_final_") != -1:
            SQL = """CREATE TABLE exampleTable (
                        ID integer not null primary key autoincrement,
                        Question text not null,
                        qOption text default '',
                        qAnswer text not null,
                        qType text not null,
                        qAnalysis text default '',
                        userAnswer text default '',
                        userName integer default 0,
                        SourceType text default '人工'
                    );"""
        elif tablename.find("exam_") != -1:
            SQL = """CREATE TABLE exampleTable (
                        ID integer not null primary key autoincrement,
                        Question text not null,
                        qOption text default '',
                        qAnswer text not null,
                        qType text not null,
                        qAnalysis text default '',
                        randomID integer not null,
                        SourceType text default '人工'
                    );"""
        SQL = SQL.replace("exampleTable", tablename)
        cur.execute(SQL)

    return flagTableExist


def mdb_ins(conn, cur, SQL):
    try:
        cur.execute(SQL)
        return True
    except:
        outputErrorInfo(SQL)
        return False


def mdb_modi(conn, cur, SQL):
    try:
        cur.execute(SQL)
        return True
    except:
        outputErrorInfo(SQL)
        return False


def mdb_sel(cur, SQL):
    try:
        cur.execute(SQL)
        return cur.fetchall()
    except:
        return []


def mdb_del(conn, cur, SQL):
    try:
        cur.execute(SQL)
        return True
    except:
        outputErrorInfo(SQL)
        return False


def getParam(paramName, StationCN):
    SQL = f"SELECT param from Setup_{StationCN} where paramName = '{paramName}'"
    cur.execute(SQL)
    table = cur.fetchone()
    if table:
        param = table[0]
    else:
        param = 0

    return param


def getChapterRatio(StationCN, qAff):
    SQL = "SELECT chapterRatio from questionAff where StationCN = '" + StationCN + "' and chapterName = '" + qAff + "'"
    quesCRTable = mdb_sel(cur, SQL)
    if quesCRTable:
        cr = quesCRTable[0][0]
    else:
        cr = 5

    return cr


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
                SQL = f"SELECT Question, qOption, qAnswer, qType, qAnalysis, chapterName, SourceType from questions where (ID not in (SELECT cid from studyinfo where questable = 'questions' and userName = {userName}) and StationCN = '{StationCN}' and qType = '{k[0]}') and (chapterName = '"
            else:
                SQL = f"SELECT Question, qOption, qAnswer, qType, qAnalysis, chapterName, SourceType from questions where (StationCN = '{StationCN}' and qType = '{k[0]}') and (chapterName = '"
            for each in qAffPack:
                if each != "错题集" and each != "公共题库":
                    SQL = SQL + each + "' or chapterName = '"
            SQL = SQL[:-20] + "')"
            rows = mdb_sel(cur, SQL)
            for row in rows:
                chapterRatio = getChapterRatio(StationCN, row[5])
                SQL = f"INSERT INTO {examTable}(Question, qOption, qAnswer, qType, qAnalysis, randomID, SourceType) VALUES('{row[0]}', '{row[1]}', '{row[2]}', '{row[3]}', '{row[4]}', {random.randint(int(1000 - 100 * chapterRatio), int(1100 - 100 * chapterRatio))}, '{row[6]}')"
                mdb_ins(conn, cur, SQL)
        if "错题集" in qAffPack and examType == "training":
            chapterRatio = getChapterRatio(StationCN, "错题集")
            for k in quesType:
                SQL = f"SELECT Question, qOption, qAnswer, qType, qAnalysis, SourceType from morepractise where qType = '{k[0]}' and userName = {userName} order by WrongTime DESC"
                rows = mdb_sel(cur, SQL)
                for row in rows:
                    SQL = "SELECT ID from " + examTable + " where Question = '" + row[0] + "'"
                    if not mdb_sel(cur, SQL):
                        SQL = f"INSERT INTO {examTable}(Question, qOption, qAnswer, qType, qAnalysis, randomID, SourceType) VALUES('{row[0]}', '{row[1]}', '{row[2]}', '{row[3]}', '{row[4]}', {random.randint(int(1000 - 100 * chapterRatio), int(1100 - 100 * chapterRatio))}, '{row[5]}')"
                        mdb_ins(conn, cur, SQL)
        if '公共题库' in qAffPack:
            chapterRatio = getChapterRatio(StationCN, '公共题库')
            for k in quesType:
                if flagNewOnly and examType == "training":
                    SQL = f"SELECT Question, qOption, qAnswer, qType, qAnalysis, SourceType from commquestions where ID not in (SELECT cid from studyinfo where questable = 'commquestions' and userName = {userName}) and qType = '{k[0]}' order by ID"
                else:
                    SQL = f"SELECT Question, qOption, qAnswer, qType, qAnalysis, SourceType from commquestions where qType = '{k[0]}' order by ID"
                rows = mdb_sel(cur, SQL)
                for row in rows:
                    SQL = "SELECT ID from " + examTable + " where Question = '" + row[0] + "'"
                    if not mdb_sel(cur, SQL):
                        SQL = f"INSERT INTO {examTable}(Question, qOption, qAnswer, qType, qAnalysis, randomID, SourceType) VALUES('{row[0]}', '{row[1]}', '{row[2]}', '{row[3]}', '{row[4]}', {random.randint(int(1000 - 100 * chapterRatio), int(1100 - 100 * chapterRatio))}, '{row[5]}')"
                        mdb_ins(conn, cur, SQL)
    CreateExamTable(examFinalTable, examRandom)
    for k in quesType:
        SQL = f"INSERT INTO {examFinalTable}(Question, qOption, qAnswer, qType, qAnalysis, SourceType) SELECT Question, qOption, qAnswer, qType, qAnalysis, SourceType from {examTable} where qType = '{k[0]}' order by randomID limit 0, {k[1]}"
        mdb_ins(conn, cur, SQL)
    quesCount, quesCS = 0, 0
    SQL = "SELECT Count(ID) from " + examFinalTable
    quesCount = mdb_sel(cur, SQL)[0][0]
    for k in quesType:
        quesCS += k[1]
    if quesCount == quesCS or (examType == 'training' and quesCount > 0):
        return True, quesCount, examTable, examFinalTable
    else:
        return False, quesCount, examTable, examFinalTable


def updatePyFileinfo():
    for root, dirs, files in os.walk("./"):
        for file in files:
            if os.path.splitext(file)[1].lower() == '.py':
                pathIn = os.path.join(root, file)
                pyFile = os.path.splitext(file)[0]
                SQL = f"SELECT ID from verinfo where pyFile = '{pyFile}'"
                if not mdb_sel(cur, SQL):
                    SQL = f"INSERT INTO verinfo(pyFile, pyLM, pyMC) VALUES('{pyFile}', {int(time.time())}, 1)"
                    mdb_ins(conn, cur, SQL)
                else:
                    SQL = f"SELECT ID from verinfo where pyFile = '{pyFile}' and pyLM = {int(os.path.getmtime(pathIn))}"
                    if not mdb_sel(cur, SQL):
                        SQL = f"UPDATE verinfo SET pyLM = {int(os.path.getmtime(pathIn))}, pyMC = pyMC + 1 where pyFile = '{pyFile}'"
                        mdb_modi(conn, cur, SQL)


conn = apsw.Connection("./DB/ETest_enc.db")
cur = conn.cursor()
cur.execute("PRAGMA cipher = 'aes256cbc'")
cur.execute("PRAGMA key = '7745'")
cur.execute("PRAGMA journal_mode = WAL")
