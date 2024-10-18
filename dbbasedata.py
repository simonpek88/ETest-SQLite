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
def addExamIDD():
    flagSuccess, examDateStr = False, ""
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
if selectFunc == "考试场次":
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
if selectFunc is not None:
    updateActionUser(st.session_state.userName, f"添加{selectFunc}", st.session_state.loginTime)
