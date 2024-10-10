# coding UTF-8
import os
import re
import time

import apsw
import streamlit as st
import streamlit_antd_components as sac
from streamlit_modal import Modal

from commFunc import (deepseek_AI, getParam, mdb_del, mdb_ins, mdb_modi,
                      mdb_sel, qianfan_AI, updateActionUser, xunfei_xh_AI,
                      xunfei_xh_AI_fib)

# cSpell:ignoreRegExp /[^\s]{16,}/
# cSpell:ignoreRegExp /\b[A-Z]{3,15}\b/g


@st.fragment
def updateAnswer(userQuesID):
    SQL = f"UPDATE {st.session_state.examFinalTable} set userAnswer = '{st.session_state.answer}', userName = {st.session_state.userName} where ID = {userQuesID}"
    mdb_modi(conn, cur, SQL)


def calcScore():
    st.session_state.examStartTime = int(time.time())
    st.session_state.confirmSubmit = True
    st.session_state.curQues = 0
    st.session_state.flagCompleted = False
    if "confirmSubmit-close" in st.session_state:
        del st.session_state["confirmSubmit-close"]
    flagUseAIFIB = bool(getParam("使用大模型评判错误的填空题答案", st.session_state.StationCN))
    opScore = getParam("单选题单题分值", st.session_state.StationCN)
    opmScore = getParam("多选题单题分值", st.session_state.StationCN)
    rdScore = getParam("判断题单题分值", st.session_state.StationCN)
    wrScore = getParam("填空题单题分值", st.session_state.StationCN)
    passScore = getParam("合格分数线", st.session_state.StationCN)
    userScore = 0
    SQL = f"SELECT qAnswer, qType, userAnswer, Question, qOption, qAnalysis, userName, SourceType from {st.session_state.examFinalTable} where userName = {st.session_state.userName} order by ID"
    rows = mdb_sel(cur, SQL)
    for row in rows:
        flagAIScore = False
        if row[0].replace(" ", "").lower() == row[2].replace(" ", "").lower():
            if row[1] == "单选题":
                userScore += opScore
            elif row[1] == "多选题":
                userScore += opmScore
            elif row[1] == "判断题":
                userScore += rdScore
            elif row[1] == "填空题":
                userScore += wrScore
            SQL = f"SELECT ID from morepractise where Question = '{row[3]}' and qType = '{row[1]}' and userName = {row[6]}"
            if mdb_sel(cur, SQL):
                SQL = f"UPDATE morepractise set WrongTime = WrongTime - 1 where Question = '{row[3]}' and qType = '{row[1]}' and userName = {row[6]}"
                mdb_modi(conn, cur, SQL)
            mdb_del(conn, cur, SQL="DELETE from morepractise where WrongTime < 1")
        else:
            if row[1] == "填空题":
                if flagUseAIFIB:
                    fibQues = row[3]
                    fibQues2 = row[3]
                    userAP = row[2].split(";")
                    quesAP = row[0].split(";")
                    if fibQues.count("()") == len(userAP):
                        st.toast("正在使用:red[讯飞星火大模型]对答案进行分析, 请稍等...")
                        for index, value in enumerate(userAP):
                            b1 = fibQues.find("()")
                            c1 = fibQues2.find("()")
                            if b1 != -1:
                                fibQues = f"{fibQues[:b1]}({value}){fibQues[b1 + 2:]}"
                                fibQues2 = f"{fibQues2[:c1]}({quesAP[index]}){fibQues2[c1 + 2:]}"
                        fibAI = xunfei_xh_AI_fib(fibQues, fibQues2)
                        if fibAI != "" and fibAI.find("无法直接回答") == -1 and fibAI.find("尚未查询") == -1 and fibAI.find("我不确定您想要表达什么意思") == -1 and fibAI.find("由于信息不足，无法给出准确答案") == -1 and fibAI.find("无法确定正确答案") == -1 and fibAI.find("无法提供准确答案") == -1:
                            if st.session_state.debug:
                                print(f"debug: [{row[3]}] [Q:{row[0]} / A:{row[2]}] / A.I.判断: [{fibAI}]")
                            if fibAI == "正确":
                                userScore += wrScore
                                flagAIScore = True
                            else:
                                flagAIScore = False
                    else:
                        st.warning("⚠️ 试题或是答案数量不匹配, 请检查")
            if not flagAIScore:
                SQL = f"SELECT ID from morepractise where Question = '{row[3]}' and qType = '{row[1]}' and userName = {row[6]}"
                if not mdb_sel(cur, SQL):
                    SQL = f"INSERT INTO morepractise(Question, qOption, qAnswer, qType, qAnalysis, userAnswer, userName, WrongTime, StationCN, SourceType) VALUES('{row[3]}', '{row[4]}', '{row[0]}', '{row[1]}', '{row[5]}', '{row[2]}', {row[6]}, 1, '{st.session_state.StationCN}', '{row[7]}')"
                    mdb_ins(conn, cur, SQL)
                else:
                    SQL = f"UPDATE morepractise set WrongTime = WrongTime + 1, userAnswer = '{row[2]}' where Question = '{row[3]}' and qType = '{row[1]}' and userName = {row[6]}"
                    mdb_modi(conn, cur, SQL)
    examDate = int(time.mktime(time.strptime(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "%Y-%m-%d %H:%M:%S")))
    if userScore >= passScore:
        flagPass = 1
    else:
        flagPass = 0
    confirm_modal = Modal(title=f"{st.session_state.examName} 考试结果", key="examResult", max_width=500)
    with confirm_modal.container():
        st.write(f"考生ID:  {st.session_state.userName}")
        st.write(f"考生姓名: {st.session_state.userCName}")
        st.write(f"考试时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(examDate))}")
        st.subheader(f"考试成绩: {userScore} 分 / 合格分数线为 {passScore} 分")
        if flagPass == 1:
            st.subheader("考试结果: :blue[通过] 👏")
            st.balloons()
        else:
            st.subheader("考试结果: :red[未通过] 🤪")
            #st.snow()
        if st.session_state.examType == "training":
            st.write("练习模式成绩不计入记录")
        st.button("确定")
    if st.session_state.examType == "exam":
        SQL = "INSERT INTO examresult(userName, userCName, examScore, examDate, examPass, examName) VALUES(" + str(st.session_state.userName) + ", '" + st.session_state.userCName + "', " + str(userScore) + ", " + str(examDate) + ", " + str(flagPass) + ", '" + st.session_state.examName + "')"
        mdb_ins(conn, cur, SQL)


@st.fragment
def updateOptionAnswer(chosenID, chosen, option):
    for index, value in enumerate(option):
        if chosen == value:
            st.session_state.answer = index
    updateAnswer(chosenID)


@st.fragment
def updateRadioAnswer(chosenID, chosen):
    if "正确" in chosen:
        st.session_state.answer = 1
    else:
        st.session_state.answer = 0
    updateAnswer(chosenID)


@st.fragment
def updateMOptionAnswer(row):
    mpAnswerPack = []
    for key in st.session_state.keys():
        if key.startswith("moption_"):
            if st.session_state[key]:
                mpAnswerPack.append(int(key.replace("moption_", "")))
    mpAnswerPack.sort()
    st.session_state.answer = ""
    for each in mpAnswerPack:
        st.session_state.answer = st.session_state.answer + str(each) + ";"
    if st.session_state.answer.endswith(";"):
        st.session_state.answer = st.session_state.answer[:-1]
    updateAnswer(row[0])


def delQuestion(delQuesRow):
    delTablePack = ["questions", "commquestions", "morepractise"]
    for delTable in delTablePack:
        SQL = f"DELETE from {delTable} where Question = '{delQuesRow[1]}' and qType = '{delQuesRow[4]}'"
        mdb_del(conn, cur, SQL)


@st.fragment
def updateStudyInfo(studyRow):
    for each in ["questions", "commquestions"]:
        if each == "questions":
            SQL = f"SELECT ID, chapterName from {each} where Question = '{studyRow[1]}' and qType = '{studyRow[4]}' and StationCN = '{st.session_state.StationCN}'"
        elif each == "commquestions":
            SQL = f"SELECT ID, '公共题库' from {each} where Question = '{studyRow[1]}' and qType = '{studyRow[4]}'"
        studyResult = mdb_sel(cur, SQL)
        if studyResult:
            SQL = f"SELECT ID from studyinfo where cid = {studyResult[0][0]} and questable = '{each}' and userName = {st.session_state.userName} and chapterName = '{studyResult[0][1]}'"
            if not mdb_sel(cur, SQL):
                SQL = f"INSERT INTO studyinfo(cid, questable, userName, userCName, chapterName, startTime) VALUES({studyResult[0][0]}, '{each}', {st.session_state.userName}, '{st.session_state.userCName}', '{studyResult[0][1]}', {int(time.time())})"
                mdb_ins(conn, cur, SQL)


@st.fragment
def delFavQues(favRow):
    SQL = f"DELETE from favques where Question = '{favRow[1]}' and userName = {st.session_state.userName} and qType = '{favRow[4]}' and StationCN = '{st.session_state.StationCN}'"
    mdb_del(conn, cur, SQL)
    st.toast("已从关注题集中删除")


@st.fragment
def addFavQues(favRow):
    SQL = f"SELECT ID from favques where Question = '{favRow[1]}' and userName = {st.session_state.userName} and StationCN = '{st.session_state.StationCN}'"
    if not mdb_sel(cur, SQL):
        SQL = f"INSERT INTO favques(Question, qOption, qAnswer, qType, qAnalysis, userName, StationCN, SourceType) VALUES('{favRow[1]}', '{favRow[2]}', '{favRow[3]}', '{favRow[4]}', '{favRow[5]}', {st.session_state.userName}, '{st.session_state.StationCN}', '{favRow[8]}')"
        mdb_ins(conn, cur, SQL)
        st.toast("已添加到关注题集")


@st.fragment
def exam(row):
    option, AIModelName, AIOption, AIOptionIndex = [], "", [], 0
    st.session_state.answer = ""
    flagAIUpdate = bool(getParam("A.I.答案解析更新至题库", st.session_state.StationCN))
    SQL = f"SELECT paramName, param from setup_{st.session_state.StationCN} where paramType = 'others' and paramName like '%大模型' order by ID"
    tempTable = mdb_sel(cur, SQL)
    for index, value in enumerate(tempTable):
        AIOption.append(value[0])
        if value[1] == 1:
            AIModelName = value[0]
            AIOptionIndex = index
    if row[4] == "填空题":
        reviseQues = row[1].replace("(", ":red[( _ ]").replace(")", ":red[ _ _ )]")
    else:
        reviseQues = row[1]
    standardAnswer = getStandardAnswer(row)
    if st.session_state.examType != "exam":
        updateStudyInfo(row)
    st.write(f"##### 第{row[0]}题 :green[{reviseQues}]")
    acol1, acol2 = st.columns(2)
    if st.session_state.debug and st.session_state.userType == "admin":
        buttonConfirm = acol1.button("⚠️ 从所有题库中删除此题", type="primary")
        if buttonConfirm:
            st.button("确认删除", type="secondary", on_click=delQuestion, args=(row,))
    if st.session_state.examType == "training":
        SQL = f"SELECT ID from favques where Question = '{row[1]}' and userName = {st.session_state.userName} and StationCN = '{st.session_state.StationCN}'"
        if mdb_sel(cur, SQL):
            acol2.button(label="", icon=":material/heart_minus:", on_click=delFavQues, args=(row,), help="从关注题集中删除")
        else:
            acol2.button(label="", icon=":material/heart_plus:", on_click=addFavQues, args=(row,), help="添加到关注题集")
    st.write(f":red[本题为{row[4]}]:")
    if row[4] == '单选题':
        for index, value in enumerate(row[2].replace("；", ";").split(";")):
            value = value.replace("\n", "").replace("\t", "").strip()
            option.append(f"{chr(65 + index)}. {value}")
        if row[6] == "":
            chosen = st.radio(" ", option, index=None, label_visibility="collapsed", horizontal=True)
        else:
            chosen = st.radio(" ", option, index=int(row[6]), label_visibility="collapsed", horizontal=True)
            #st.write(f":red[你已选择: ] :blue[{option[int(row[6])]}]")
        if chosen is not None:
            updateOptionAnswer(row[0], chosen, option)
    elif row[4] == '多选题':
        #st.session_state.answer = ""
        for index, value in enumerate(row[2].replace("；", ";").split(";")):
            value = value.replace("\n", "").replace("\t", "").strip()
            option.append(f"{chr(65 + index)}. {value}")
        if row[6] != "":
            orgOption = row[6].replace("；", ";").split(";")
        else:
            orgOption = []
        for index, value in enumerate(option):
            if str(index) in orgOption:
                st.checkbox(f"{value}:", value=True, key=f"moption_{index}", on_change=updateMOptionAnswer, args=(row,))
            else:
                st.checkbox(f"{value}:", value=False, key=f"moption_{index}", on_change=updateMOptionAnswer, args=(row,))
    elif row[4] == '判断题':
        option = ["A. 正确", "B. 错误"]
        if row[6] == "":
            chosen = st.radio(" ", option, index=None, label_visibility="collapsed", horizontal=True)
            #print(f"Chosen:[{chosen}], {row[0]}, [{row[6]}]")
        else:
            chosen = st.radio(" ", option, index=int(row[6]) ^ 1, label_visibility="collapsed", horizontal=True)
        #st.write(f":red[你已选择: ] :blue[{option[int(row[6]) ^ 1]}")
        if chosen is not None:
            updateRadioAnswer(row[0], chosen)
    elif row[4] == '填空题':
        st.session_state.answer = ""
        orgOption = row[6].replace("；", ";").split(";")
        textAnswerArea = st.empty()
        with textAnswerArea.container():
            for i in range(row[1].count("()")):
                if row[6] == "":
                    st.text_input(label=" ", key=f"textAnswer_{i}", placeholder=f"请输入第{i + 1}个括号内的内容", label_visibility="collapsed")
                else:
                    st.text_input(label=" ", value=orgOption[i], key=f"textAnswer_{i}", placeholder=f"请输入第{i + 1}个括号内的内容", label_visibility="collapsed")
            buttonTA = st.button("确定")
            if buttonTA:
                updateTA()
                textAnswerArea.empty()
                st.toast(f"第{row[0]}题答案已更新, 请点击上方按钮继续答题或交卷")
    if st.session_state.examType == "training":
        col1, col2, col3 = st.columns(3)
        with col3:
            AIOptionIndex = sac.segmented(
                items=[
                    sac.SegmentedItem(label="讯飞"),
                    sac.SegmentedItem(label="百度"),
                    sac.SegmentedItem(label="深索"),
                ], label="可选LLM大模型", index=AIOptionIndex, align="start", color="red", return_index=True
            )
        AIModelName = AIOption[AIOptionIndex]
        updateAIModel(AIOption, AIOptionIndex)
        if row[5] != "":
            with col1:
                buttonAnalysis = st.button("显示答案解析")
            with col2:
                buttonDelAnalysis = st.button("删除本题答案解析")
            if buttonAnalysis:
                st.subheader(f":orange[解析 标准答案: :green[[{standardAnswer}]]]\n{row[5]}", divider="gray")
            if buttonDelAnalysis:
                delAnalysis(row)
        else:
            if AIModelName != "":
                with col1:
                    buttonAnalysis = st.button(f"A.I.答案解析 使用:green[[{AIModelName.replace('大模型', '')}]]")
                with col2:
                    buttonDelAnalysis = st.button("删除本题答案解析")
                if AIModelName == "文心千帆大模型":
                    AIModelType = st.radio(label="请设置生成内容类型", options=("简洁", "详细"), index=0, horizontal=True, help="返回结果类型, 详细型附加了很多解释内容")
                    if AIModelType == "简洁":
                        AIModel = "ERNIE Speed-AppBuilder"
                    elif AIModelType == "详细":
                        AIModel = "ERNIE-Speed-8K"
                if buttonAnalysis:
                    AIAnswerInfo = st.empty()
                    with AIAnswerInfo.container():
                        st.info(f"正在使用:red[[{AIModelName.replace('大模型', '')}]]获取答案解析, 内容不能保证正确, 仅供参考! 请稍等...")
                    if AIModelName == "文心千帆大模型":
                        AIAnswer = qianfan_AI(row[1], AIModel, option, row[4])
                    elif AIModelName == "讯飞星火大模型":
                        AIAnswer = xunfei_xh_AI(row[1], option, row[4])
                    elif AIModelName == "DeepSeek大模型":
                        AIAnswer = deepseek_AI(row[1], option, row[4])
                    AIAnswerInfo.empty()
                    if AIAnswer != "" and AIAnswer.find("无法直接回答") == -1 and AIAnswer.find("尚未查询") == -1 and AIAnswer.find("我不确定您想要表达什么意思") == -1 and AIAnswer.find("由于信息不足，无法给出准确答案") == -1 and AIAnswer.find("无法确定正确答案") == -1 and AIAnswer.find("无法提供准确答案") == -1:
                        if AIAnswer.startswith(":"):
                            AIAnswer = AIAnswer[1:]
                        AIAnswer = AIAnswer + f"\n\n:red[答案解析来自[{AIModelName}], 非人工解析内容, 仅供参考!]"
                        st.subheader(f":orange[解析 标准答案: :green[[{standardAnswer}]]]\n{AIAnswer}", divider="gray")
                        if flagAIUpdate:
                            AIAnswer = AIAnswer.replace('"', '""').replace("'", "''")
                            for each in ["questions", "commquestions", "morepractise", st.session_state.examTable, st.session_state.examFinalTable]:
                                SQL = f"UPDATE {each} set qAnalysis = '{AIAnswer}' where Question = '{row[1]}' and qType = '{row[4]}'"
                                mdb_modi(conn, cur, SQL)
                            st.toast("A.I.答案解析内容已更新至题库")
                    else:
                        st.info("A.I.获取答案解析失败")
                if buttonDelAnalysis:
                    delAnalysis(row)
            else:
                st.info("没有设置A.I.大模型")
    st.session_state.curQues = row[0]


@st.fragment
def updateAIModel(AIOption, AIOptionIndex):
    SQL = f"UPDATE setup_{st.session_state.StationCN} set param = 0 where paramType = 'others' and paramName like '%大模型'"
    mdb_modi(conn, cur, SQL)
    SQL = f"UPDATE setup_{st.session_state.StationCN} set param = 1 where paramType = 'others' and paramName = '{AIOption[AIOptionIndex]}'"
    mdb_modi(conn, cur, SQL)


@st.fragment
def delAnalysis(row):
    for each in ["questions", "commquestions", "morepractise", st.session_state.examTable, st.session_state.examFinalTable]:
        SQL = f"UPDATE {each} set qAnalysis = '' where Question = '{row[1]}' and qType = '{row[4]}'"
        mdb_modi(conn, cur, SQL)
    st.info("本题解析已删除")


@st.fragment
def manualFIB(rowID):
    fibAI = ""
    SQL = f"SELECT Question, qAnswer, userAnswer from {st.session_state.examFinalTable} where ID = {rowID}"
    fibRow = mdb_sel(cur, SQL)[0]
    fibQues = fibRow[0]
    userAP = fibRow[2].split(";")
    if fibQues.count("()") == len(userAP):
        for each in userAP:
            b1 = fibQues.find("()")
            if b1 != -1:
                fibQues = f"{fibQues[:b1]}({each}){fibQues[b1 + 2:]}"
        fibAI = xunfei_xh_AI_fib(fibQues)
    else:
        st.warning("⚠️ 试题或是答案数量不匹配, 请检查")

    return fibAI


@st.fragment
def getStandardAnswer(qRow):
    radioOption, standardAnswer = ["A", "B", "C", "D", "E", "F", "G", "H"], ""
    if qRow[4] == "单选题" or qRow[4] == "多选题":
        orgOption = qRow[3].replace("；", ";").split(";")
        for value in orgOption:
            standardAnswer = standardAnswer + radioOption[int(value)] + ", "
    elif qRow[4] == "判断题":
        if qRow[3] == "1":
            standardAnswer = "正确"
        else:
            standardAnswer = "错误"
    elif qRow[4] == "填空题":
        standardAnswer = qRow[3].replace("；", ";").replace(";", ", ")
    if standardAnswer.endswith(", "):
        standardAnswer = standardAnswer[:-2]

    return standardAnswer


@st.fragment
def updateTA():
    textAnswerPack = []
    for key in st.session_state.keys():
        if "textAnswer_" in key:
            textAnswerPack.append([int(key.replace("textAnswer_", "")), st.session_state[key]])
    textAnswerPack.sort()
    st.session_state.answer = ""
    for each in textAnswerPack:
        st.session_state.answer += each[1] + ";"
    if st.session_state.answer.endswith(";"):
        st.session_state.answer = st.session_state.answer[:-1]
    updateAnswer(st.session_state.curQues)


def changeCurQues(step):
    st.session_state.curQues += step
    if st.session_state.curQues < 1:
        st.session_state.curQues = 1
    elif st.session_state.curQues > quesCount:
        st.session_state.curQues = quesCount


@st.fragment
def quesGoto():
    if st.session_state.chosenID is not None:
        st.session_state.goto = True
        cop = re.compile('[^0-9^.]')
        st.session_state.curQues = int(cop.sub('', st.session_state.chosenID))


conn = apsw.Connection("./DB/ETest_enc.db")
cur = conn.cursor()
cur.execute("PRAGMA cipher = 'aes256cbc'")
cur.execute("PRAGMA key = '7745'")
cur.execute("PRAGMA journal_mode = WAL")

if st.session_state.examType == "exam":
    updateActionUser(st.session_stateuserName, "考试", st.session_state.loginTime)
elif st.session_state.examType == "training":
    updateActionUser(st.session_state.userName, "练习", st.session_state.loginTime)
if "confirmSubmit" not in st.session_state:
    st.session_state.confirmSubmit = False
if "examFinalTable" in st.session_state and "examName" in st.session_state and not st.session_state.confirmSubmit:
    #st.write(f"## :red[{st.session_state.examName}]")
    st.markdown(f"<font face='微软雅黑' color=red size=16><center>**{st.session_state.examName}**</center></font>", unsafe_allow_html=True)
    flagTime = bool(getParam("显示考试时间", st.session_state.StationCN))
    SQL = f"SELECT userName, examName from examresult GROUP BY userName, examName HAVING count(userName) < {st.session_state.examLimit} and count(examName) < {st.session_state.examLimit} and userName = {st.session_state.userName} and examName = '{st.session_state.examName}'"
    if mdb_sel(cur, SQL) or st.session_state.examType == "training":
        for key in st.session_state.keys():
            if key.startswith("moption_") or key.startswith("textAnswer_"):
                del st.session_state[key]
        if st.session_state.examType == "exam" or flagTime:
            examTimeLimit = int(getParam("考试时间", st.session_state.StationCN) * 60)
            remainingTime = examTimeLimit - (int(time.time()) - st.session_state.examStartTime)
            hTime = "0" + str(int(remainingTime / 3600))
            mTime = int((remainingTime % 3600) / 60)
            if mTime < 10:
                mTime = "0" + str(mTime)
            sTime = int(remainingTime % 60)
            if sTime < 10:
                sTime = "0" + str(sTime)
            SQL = f"SELECT count(ID) from {st.session_state.examFinalTable} where userAnswer <> ''"
            acAnswer1 = mdb_sel(cur, SQL)[0][0]
            SQL = f"SELECT count(ID) from {st.session_state.examFinalTable} where userAnswer = ''"
            acAnswer2 = mdb_sel(cur, SQL)[0][0]
            info1, info2, info3, info4 = st.columns(4)
            info1.metric(label="考试剩余时间", value=f"{hTime}:{mTime}:{sTime}")
            info2.metric(label="已答题", value=acAnswer1)
            info3.metric(label="未答题", value=acAnswer2)
            info4.metric(label="总题数", value=acAnswer1 + acAnswer2)
            if remainingTime < 0:
                if st.session_state.examType == "exam":
                    st.warning("⚠️ 考试已结束, 将强制交卷!")
                    calcScore()
                else:
                    st.session_state.examStartTime = int(time.time())
            elif remainingTime < 900:
                st.warning(f"⚠️ :red[考试剩余时间已不足{int(remainingTime / 60) + 1}分钟, 请抓紧时间完成考试!]")
        qcol1, qcol2, qcol3, qcol4 = st.columns(4)
        examCon = st.empty()
        with examCon.container():
            SQL = "SELECT * from " + st.session_state.examFinalTable + " order by ID"
            rows = mdb_sel(cur, SQL)
            quesCount = len(rows)
            #st.write(f"Cur:{st.session_state.curQues} Comp:{st.session_state.flagCompleted}")
            if st.session_state.flagCompleted:
                if st.session_state.curQues == 1:
                    preButton = qcol3.button("上题", icon=":material/arrow_back_ios:", disabled=True)
                else:
                    preButton = qcol3.button("上题", icon=":material/arrow_back_ios:", on_click=changeCurQues, args=(-1,))
                if st.session_state.curQues == quesCount:
                    nextButton = qcol4.button("下题", icon=":material/arrow_forward_ios:", disabled=True)
                else:
                    nextButton = qcol4.button("下题", icon=":material/arrow_forward_ios:", on_click=changeCurQues, args=(1,))
                submitButton = qcol1.button("交卷", icon=":material/publish:")
            elif st.session_state.confirmSubmit:
                preButton = qcol3.button("上题", icon=":material/arrow_back_ios:", disabled=True)
                nextButton = qcol4.button("下题", icon=":material/arrow_forward_ios:", disabled=True)
                submitButton = qcol1.button("交卷", icon=":material/publish:", disabled=True)
            elif st.session_state.curQues == 0:
                preButton = qcol3.button("上题", icon=":material/arrow_back_ios:", disabled=True)
                nextButton = qcol4.button("下题", icon=":material/arrow_forward_ios:", on_click=changeCurQues, args=(1,))
                submitButton = qcol1.button("交卷", icon=":material/publish:", disabled=True)
                exam(rows[0])
            elif st.session_state.curQues == 1:
                preButton = qcol3.button("上题", icon=":material/arrow_back_ios:", disabled=True)
                nextButton = qcol4.button("下题", icon=":material/arrow_forward_ios:", on_click=changeCurQues, args=(1,))
                submitButton = qcol1.button("交卷", icon=":material/publish:", disabled=True)
            elif st.session_state.curQues == quesCount:
                preButton = qcol3.button("上题", icon=":material/arrow_back_ios:", on_click=changeCurQues, args=(-1,))
                nextButton = qcol4.button("下题", icon=":material/arrow_forward_ios:", disabled=True)
                submitButton = qcol1.button("交卷", icon=":material/publish:")
                st.session_state.flagCompleted = True
            elif st.session_state.curQues > 1 and st.session_state.curQues < quesCount:
                preButton = qcol3.button("上题", icon=":material/arrow_back_ios:", on_click=changeCurQues, args=(-1,))
                nextButton = qcol4.button("下题", icon=":material/arrow_forward_ios:", on_click=changeCurQues, args=(1,))
                submitButton = qcol1.button("交卷", icon=":material/publish:", disabled=True)
            iCol1, iCol2 = st.columns(2)
            completedPack, cpStr, cpCount = [], "", 0
            SQL = f"SELECT ID, userAnswer, qType from {st.session_state.examFinalTable} order by ID"
            rows3 = mdb_sel(cur, SQL)
            for row3 in rows3:
                if row3[1] == "":
                    completedPack.append(f"第{row3[0]}题 [{row3[2]}] 未作答")
                    cpStr = cpStr + str(row3[0]) + "/"
                else:
                    completedPack.append(f"第{row3[0]}题 [{row3[2]}] 已作答")
                    cpCount += 1
            if cpCount == quesCount:
                iCol1.caption(":orange[作答提示: 全部题目已作答]")
            elif quesCount - cpCount > 40:
                iCol1.caption(f":blue[作答提示:] :red[你还有{quesCount - cpCount}道题未作答, 请尽快完成]")
            elif quesCount - cpCount > 0:
                iCol1.caption(f":blue[作答提示:] :red[{cpStr[:-1]}] :blue[题还未作答, 可以在👉右测下拉列表中跳转]")
            else:
                iCol1.caption(":red[你还未开始答题]")
            iCol2.selectbox(":green[试卷全部题目]", completedPack, index=None, on_change=quesGoto, key="chosenID")
            st.divider()
            if (preButton or nextButton or submitButton or st.session_state.goto) and not st.session_state.confirmSubmit:
                SQL = f"SELECT * from {st.session_state.examFinalTable} where ID = {st.session_state.curQues}"
                row = mdb_sel(cur, SQL)[0]
                if preButton or nextButton or st.session_state.goto:
                    if st.session_state.goto:
                        st.session_state.goto = False
                        st.write("#### :blue[跳转到指定题号: ]")
                    exam(row)
                if submitButton:
                    emptyAnswer = "你没有作答的题为:第["
                    SQL = f"SELECT ID from {st.session_state.examFinalTable} where userAnswer == '' order by ID"
                    rows2 = mdb_sel(cur, SQL)
                    for row2 in rows2:
                        emptyAnswer = emptyAnswer + str(row2[0]) + ", "
                    if emptyAnswer.endswith(", "):
                        emptyAnswer = emptyAnswer[:-2] + "]题, 请检查或直接交卷!"
                    else:
                        emptyAnswer = "你的所有题目均已作答, 确认交卷吗?"
                    confirm_modal = Modal(title=emptyAnswer, key="confirmSubmit", max_width=500)
                    with confirm_modal.container():
                        st.button("确定", on_click=calcScore)
                        st.button("取消")
                preButton, nextButton, submitButton = False, False, False
        if st.session_state.confirmSubmit:
            examCon.empty()
    elif st.session_state.examType == "exam":
        st.info("你已达到本场考试的最大限制, 无法再次进行, 如有疑问请向管理员咨询", icon="ℹ️")
else:
    if st.session_state.examType == "training":
        st.info("请先生成新的题库", icon="ℹ️")
    elif st.session_state.examType == "exam":
        st.info("请先选择考试场次和点击开始考试", icon="ℹ️")
