# coding UTF-8
import datetime
import time

import apsw
import streamlit as st
import streamlit_antd_components as sac

from commFunc import mdb_del, mdb_ins, mdb_modi, mdb_sel, updateActionUser

# cSpell:ignoreRegExp /[^\s]{16,}/
# cSpell:ignoreRegExp /\b[A-Z]{3,15}\b/g


def ClearStr(strValue):
    strValue = strValue.replace("\n", "").replace("\t", "").strip()

    return strValue


@st.fragment
def addNewQues():
    flagSuccess = False
    qAnswer, qOption, qAnalysis, flag = "", "", "", True
    itemArea = st.empty()
    with itemArea.container():
        if qType == "单选题":
            qQuestion = st.text_input("题目", value="")
            qAnalysis = st.text_input("答案解析", value="")
            qQuestion = ClearStr(qQuestion)
            qAnalysis = ClearStr(qAnalysis)
            for i in range(0, 4):
                st.text_input(f"选项{i + 1}", key=f"qAddQues_{i}")
            qAddAnswer = st.radio("答案", ["A", "B", "C", "D"], index=None, horizontal=True)
            if qQuestion == "":
                flag = False
                st.warning("题目不能为空")
            if flag:
                qOption = ""
                for i in range(0, 4):
                    if st.session_state[f"qAddQues_{i}"] == "":
                        st.warning(f"选项{i+1} 不能为空")
                        flag = False
                        qOption = ""
                        break
                    else:
                        tmp = ClearStr(st.session_state[f"qAddQues_{i}"])
                        qOption = qOption + tmp + ";"
            if flag:
                if qAddAnswer is not None:
                    for index, value in enumerate(["A", "B", "C", "D"]):
                        if value == qAddAnswer:
                            qAnswer = index
                else:
                    st.warning("必须有一个答案")
                    flag = False
            if qOption != "":
                qOption = qOption[:-1]
        elif qType == "判断题":
            qQuestion = st.text_input("题目", value="")
            qAnalysis = st.text_input("答案解析", value="")
            qOption = ""
            st.radio("答案", ["正确", "错误"], key="qAddAnswer", index=None, horizontal=True)
            if qQuestion == "":
                st.warning("题目不能为空")
                flag = False
            if st.session_state.qAddAnswer != "":
                if st.session_state.qAddAnswer == "正确":
                    qAnswer = 1
                else:
                    qAnswer = 0
            else:
                st.warning("必须有一个答案")
                flag = False
        if qAnalysis == "":
            st.warning("建议填写答案解析, 本内容仅在练习中显示, 不会在考试中显示")
        if flag:
            buttonSubmit = st.button("添加题目")
            if buttonSubmit:
                if selectFunc == "站室专用题库":
                    SQL = "SELECT ID from questions where Question = '" + qQuestion + "' and StationCN = " + str(st.session_state.StationCN) + " and chapterName = '" + qAff + "'"
                    if not mdb_sel(cur, SQL):
                        SQL = f"INSERT INTO questions(Question, qOption, qAnswer, qType, qAnalysis, StationCN, chapterName, SourceType) VALUES('{qQuestion}', '{qOption}', '{qAnswer}', '{qType}', '{qAnalysis}', '{st.session_state.StationCN}', '{qAff}', '人工')"
                        mdb_ins(conn, cur, SQL)
                        flagSuccess = True
                        itemArea.empty()
                    else:
                        st.warning("考题已存在")
                elif selectFunc == "公共题库":
                    SQL = "SELECT ID from commquestions where Question = '" + qQuestion + "'"
                    if not mdb_sel(cur, SQL):
                        SQL = f"INSERT INTO commquestions(Question, qOption, qAnswer, qType, qAnalysis, SourceType) VALUES('{qQuestion}', '{qOption}', '{qAnswer}', '{qType}', '{qAnalysis}', '人工')"
                        mdb_ins(conn, cur, SQL)
                        flagSuccess = True
                        itemArea.empty()
                    else:
                        st.warning("考题已存在")
    if flagSuccess:
        if selectFunc == "站室专用题库":
            SQL = "SELECT ID from questions where Question = '" + qQuestion + "' and StationCN = " + str(st.session_state.StationCN) + " and chapterName = '" + qAff + "'"
        elif selectFunc == "公共题库":
            SQL = "SELECT ID from commquestions where Question = '" + qQuestion + "'"
        if mdb_sel(cur, SQL):
            st.success(f"考题: [{qQuestion}] 类型: [{qType}] 所属站室: [{st.session_state.StationCN}] 题库: [{selectFunc}] 已添加成功")
        else:
            st.warning(f"考题添加至 [{selectFunc}] 失败")


@st.fragment
def addChapter():
    flagSuccess = False
    itemArea = st.empty()
    with itemArea.container():
        chapter = st.text_input("章节名称")
        chapter = ClearStr(chapter)
        if chapter and chapterRatio:
            buttonSubmit = st.button("添加章节")
            if buttonSubmit:
                sc = st.session_state.StationCN
                cr = int(chapterRatio)
                SQL = "SELECT ID from questionaff where chapterName = '" + chapter + "' and StationCN = '" + sc + "'"
                if not mdb_sel(cur, SQL):
                    SQL = f"INSERT INTO questionaff(chapterName, StationCN, chapterRatio, examChapterRatio) VALUES('{chapter}', '{sc}', {cr}, {cr})"
                    mdb_ins(conn, cur, SQL)
                    flagSuccess = True
                    itemArea.empty()
                else:
                    st.warning(f"[{chapter}] 章节已存在")
        else:
            if not chapter:
                st.warning("请输入章节名称")
    if flagSuccess:
        SQL = "SELECT ID from questionaff where chapterName = '" + chapter + "' and StationCN = '" + sc + "'"
        if mdb_sel(cur, SQL):
            st.success(f"章节: [{chapter}] 所属站室: [{st.session_state.StationCN}] 权重: [{cr}] 添加成功")
        else:
            st.warning(f"[{chapter}] 章节添加失败")


@st.fragment
def addExamIDD():
    flagSuccess = False
    itemArea = st.empty()
    with itemArea.container():
        examName = st.text_input("考试名称", value="", help="名称不能设置为练习题库(此为保留题库)")
        examName = ClearStr(examName)
        examDate = st.date_input("请设置考试有效期", min_value=datetime.date.today() + datetime.timedelta(days=1), max_value=datetime.date.today() + datetime.timedelta(days=180), value=datetime.date.today() + datetime.timedelta(days=3), help="考试有效期最短1天, 最长180天, 默认3天")
        if examName and examDate and examName != "练习题库":
            buttonSubmit = st.button("添加考试场次")
            if buttonSubmit:
                examDateStr = examDate
                examDate = int(time.mktime(time.strptime(f"{examDate} 23:59:59", "%Y-%m-%d %H:%M:%S")))
                SQL = f"SELECT ID from examidd where examName = '{examName}' and StationCN = '{st.session_state.StationCN}'"
                if not mdb_sel(cur, SQL):
                    SQL = f"INSERT INTO examidd(examName, validDate, StationCN) VALUES('{examName}', {examDate}, '{st.session_state.StationCN}')"
                    mdb_ins(conn, cur, SQL)
                    flagSuccess = True
                    itemArea.empty()
                else:
                    st.warning(f"[{examName}] 考试场次已存在")
        else:
            if not examName:
                st.warning("请输入考试名称")
    if flagSuccess:
        SQL = f"SELECT ID from examidd where examName = '{examName}' and StationCN = '{st.session_state.StationCN}'"
        if mdb_sel(cur, SQL):
            st.success(f"考试场次: [{examName}] 有效期: [{examDateStr} 23:59:59] 添加成功")
            itemArea.empty()
        else:
            st.warning(f"考试场次 [{examName}] 添加失败")


@st.fragment
def addStation():
    flagSuccess = False
    itemArea = st.empty()
    with itemArea.container():
        sn = st.text_input("站室名称", value="")
        sn = ClearStr(sn)
        if sn:
            buttonSubmit = st.button("添加站室名称")
            if buttonSubmit:
                SQL = "SELECT ID from stations where Station = '" + sn + "'"
                if not mdb_sel(cur, SQL):
                    SQL = f"INSERT INTO stations(Station) VALUES('{sn}')"
                    mdb_ins(conn, cur, SQL)
                    flagSuccess = True
                    itemArea.empty()
                else:
                    st.warning(f"[{sn}] 已存在")
        else:
            if not sn:
                st.warning("请输入站室名称")
    if flagSuccess:
        SQL = "SELECT ID from stations where Station = '" + sn + "'"
        if mdb_sel(cur, SQL):
            SQL = f"SELECT * from sqlite_master where type = 'table' and name = 'setup_{sn}'"
            tempTable = mdb_sel(cur, SQL)
            if not tempTable:
                SQL = """CREATE TABLE exampleTable (
                            ID integer not null primary key autoincrement,
                            paramName text not null,
                            param integer,
                            paramType text not null
                        );"""
                SQL = SQL.replace("exampleTable", f"setup_{sn}")
                cur.execute(SQL)
                SQL = f"INSERT INTO setup_{sn}(paramName, param, paramType) SELECT paramName, param, paramType from setup_默认"
                mdb_ins(conn, cur, SQL)
            for each in ["公共题库", "错题集", "关注题集"]:
                SQL = f"SELECT ID from questionaff where chapterName = '{each}' and StationCN = '{sn}'"
                if not mdb_sel(cur, SQL):
                    SQL = f"INSERT INTO questionaff(chapterName, StationCN, chapterRatio, examChapterRatio) VALUES('{each}', '{sn}', 10, 10)"
                    mdb_ins(conn, cur, SQL)
            st.success(f"[{sn}] 站室添加成功")
            itemArea.empty()
        else:
            st.warning(f"[{sn}] 添加站室失败")


@st.fragment
def addUser():
    flagSuccess = False
    itemArea = st.empty()
    with itemArea.container():
        col1, col2 = st.columns(2)
        userName = col1.number_input("用户编码", min_value=1, max_value=999999, value=1, help="建议使用员工编码, 姓名和站室可以有重复, 但是编码必须具有唯一性")
        userCName = col2.text_input("用户姓名", max_chars=10, autocomplete="name", help="请输入用户中文姓名")
        station = st.select_slider("站室", stationCName, value=st.session_state.StationCN)
        userPassword1 = st.text_input("设置密码", max_chars=8, type="password", autocomplete="off", help="设置用户密码")
        userPassword2 = st.text_input("请再次输入密码", max_chars=8, type="password", placeholder="请与上一步输入的密码一致", autocomplete="off")
        userType = sac.switch(label="管理员", on_label="On", align='start', size='md', value=False)
        userCName = ClearStr(userCName)
        if userName and userCName and userPassword1 and userPassword2 and userPassword1 != "" and userPassword2 != "":
            buttonSubmit = st.button("添加用户")
            if buttonSubmit:
                if userPassword1 == userPassword2:
                    un = int(userName)
                    if userType:
                        ut = "admin"
                    else:
                        ut = "user"
                    st.write(station)
                    SQL = "SELECT ID from users where userName = " + str(un)
                    if not mdb_sel(cur, SQL):
                        SQL = f"INSERT INTO users(userName, userCName, userType, StationCN, userPassword) VALUES({un}, '{userCName}', '{ut}', '{station}', '{userPassword1}')"
                        mdb_ins(conn, cur, SQL)
                        flagSuccess = True
                        itemArea.empty()
                    else:
                        st.warning(f"ID: [{userName}] 姓名: [{userCName}] 用户已存在或用户编码重复")
                else:
                    st.warning("两次输入密码不一致")
        else:
            if not userCName:
                st.warning("请输入用户姓名")
            elif not userPassword1:
                st.warning("请输入密码")
            elif not userPassword2:
                st.warning("请确认密码")
    if flagSuccess:
        SQL = "SELECT ID from users where userName = " + str(un) + " and StationCN = '" + station + "' and userCName = '" + userCName + "'"
        if mdb_sel(cur, SQL):
            st.success(f"ID: [{userName}] 姓名: [{userCName}] 类型: [{ut}] 站室: [{station}] 用户添加成功")
            itemArea.empty()
        else:
            st.warning(f"ID: [{userName}] 姓名: [{userCName}] 类型: [{ut}] 站室: [{station}] 用户添加失败")


conn = apsw.Connection("./DB/ETest_enc.db")
cur = conn.cursor()
cur.execute("PRAGMA cipher = 'aes256cbc'")
cur.execute("PRAGMA key = '7745'")
cur.execute("PRAGMA journal_mode = WAL")

st.write("### :orange[基础数据录入]")
#selectFunc = st.selectbox("请选择数据表", ["章节信息", "站室专用题库", "公共题库", "考试场次", "站室", "用户"], index=None, help="请选择数据表")
selectFunc = st.selectbox("请选择数据表", ["考试场次", "站室", "用户"], index=None, help="请选择数据表")
stationCName = []
SQL = "SELECT Station from stations order by ID"
rows = mdb_sel(cur, SQL)
for row in rows:
    stationCName.append(row[0])
if selectFunc == "章节信息":
    chapterRatio = st.slider("章节权重", min_value=1, max_value=10, value=5, help="数值越高权重越大")
    buttonAdd = st.button("新增")
    if buttonAdd:
        addChapter()
elif selectFunc == "考试场次":
    buttonAdd = st.button("新增")
    if buttonAdd:
        addExamIDD()
elif selectFunc == "站室":
    buttonAdd = st.button("新增")
    if buttonAdd:
        addStation()
elif selectFunc == "用户":
    buttonAdd = st.button("新增")
    if buttonAdd:
        addUser()
elif selectFunc == "站室专用题库" or selectFunc == "公共题库":
    qTypeOption, chapterName = [], []
    SQL = f"SELECT paramName from setup_{st.session_state.StationCN} where paramType = 'questype' and param = 1"
    rows = mdb_sel(cur, SQL)
    for row in rows:
        qTypeOption.append(row[0])
    SQL = "SELECT chapterName from questionaff where StationCN = '" + st.session_state.StationCN + "' and chapterName <> '错题集' and chapterName <> '公共题库' and chapterName <> '关注题集' order by chapterName"
    rows = mdb_sel(cur, SQL)
    for row in rows:
        chapterName.append(row[0])
    if qTypeOption != [] and chapterName != []:
        qAff = st.select_slider("章节", chapterName, value=chapterName[0])
        qType = st.select_slider("题型", qTypeOption, value="单选题")
        buttonAdd = st.button("新增")
        if buttonAdd:
            addNewQues()
if selectFunc is not None:
    updateActionUser(st.session_state.userName, f"添加{selectFunc}", st.session_state.loginTime)
