# coding UTF-8
import time

import apsw
import pandas as pd
import streamlit as st

from commFunc import mdb_del, mdb_ins, mdb_modi, mdb_sel, updateActionUser

# cSpell:ignoreRegExp /[^\s]{16,}/
# cSpell:ignoreRegExp /\b[A-Z]{3,15}\b/g


def highlight_max(x, forecolor='black', backcolor='yellow'):
    is_max = x == x.max()

    return [f'color: {forecolor}; background-color: {backcolor}' if v else '' for v in is_max]


def queryExamAnswer(tablename):
    chosenType = []
    if tablename == "morepractise":
        chosenType = ["错题"]
    else:
        chosenType = ["对题", "错题"]
    options = st.multiselect(
        "查询类型",
        chosenType,
        ["错题"],
    )
    if options:
        searchButton = st.button("查询")
        if searchButton:
            if len(options) == 2:
                SQL = "SELECT Question, qOption, qAnswer, qType, qAnalysis, userAnswer, ID from " + tablename + " where userAnswer <> '' and userName = " + str(st.session_state.userName) + " order by ID"
            elif len(options) == 1:
                if options[0] == "对题":
                    SQL = "SELECT Question, qOption, qAnswer, qType, qAnalysis, userAnswer, ID from " + tablename + " where userAnswer <> '' and qAnswer = userAnswer and userName = " + str(st.session_state.userName) + " order by ID"
                elif options[0] == "错题":
                    SQL = "SELECT Question, qOption, qAnswer, qType, qAnalysis, userAnswer, ID from " + tablename + " where userAnswer <> '' and qAnswer <> userAnswer and userName = " + str(st.session_state.userName) + " order by ID"
            rows = mdb_sel(cur, SQL)
            if rows:
                for row in rows:
                    if row[2] != row[5]:
                        flagAnswer = "错误"
                        st.subheader("", divider="red")
                    else:
                        flagAnswer = "正确"
                        st.subheader("", divider="green")
                    st.subheader(f"题目: :grey[{row[0]}]")
                    if row[3] == "单选题":
                        st.write(":red[标准答案:]")
                        option, userAnswer = [], ["A", "B", "C", "D"]
                        tmp = row[1].replace("；", ";").split(";")
                        for index, each in enumerate(tmp):
                            each = each.replace("\n", "").replace("\t", "").strip()
                            option.append(f"{userAnswer[index]}. {each}")
                        st.radio(" ", option, key=f"compare_{row[6]}", index=int(row[2]), horizontal=True, label_visibility="collapsed", disabled=True)
                        st.write(f"你的答案: :red[{userAnswer[int(row[5])]}] 你的选择为: :blue[[{flagAnswer}]]")
                    elif row[3] == "多选题":
                        userOption = ["A", "B", "C", "D", "E", "F", "G", "H"]
                        st.write(":red[标准答案:]")
                        option = row[1].replace("；", ";").split(";")
                        orgOption = row[2].replace("；", ";").split(";")
                        for index, value in enumerate(option):
                            value = value.replace("\n", "").replace("\t", "").strip()
                            if str(index) in orgOption:
                                st.checkbox(f"{userOption[index]}. {value}:", value=True, disabled=True)
                            else:
                                st.checkbox(f"{userOption[index]}. {value}:", value=False, disabled=True)
                        userAnswer = row[5].replace("；", ";").split(";")
                        tmp = ""
                        for each in userAnswer:
                            tmp = tmp + userOption[int(each)] + ", "
                        st.write(f"你的答案: :red[{tmp[:-2]}] 你的选择为: :blue[[{flagAnswer}]]")
                    elif row[3] == "判断题":
                        st.write(":red[标准答案:]")
                        option = ["A. 正确", "B. 错误"]
                        tmp = int(row[2]) ^ 1
                        st.radio(" ", option, key=f"compare_{row[6]}", index=tmp, horizontal=True, label_visibility="collapsed", disabled=True)
                        tmp = int(row[5]) ^ 1
                        st.write(f"你的答案: :red[{option[tmp]}] 你的选择为: :blue[[{flagAnswer}]]")
                    elif row[3] == "填空题":
                        option = row[2].replace("；", ";").split(";")
                        userAnswer = row[5].replace("；", ";").split(";")
                        st.write(":red[标准答案:]")
                        for index, value in enumerate(option):
                            st.write(f"第{index + 1}个填空: :green[{value}]")
                        st.write("你的答案:")
                        for index, value in enumerate(userAnswer):
                            st.write(f"第{index + 1}个填空: :red[{value}]")
                        st.write(f"你的填写为: :blue[[{flagAnswer}]]")
                    if row[4] != "":
                        st.markdown(f"答案解析: :green[{row[4]}]")
            else:
                st.warning("暂无数据")
    else:
        st.warning("请设置查询类型")


def queryExamResult():
    searchOption = []
    SQL = f"SELECT ID, examName from examidd where StationCN = '{st.session_state.StationCN}' order by ID"
    rows = mdb_sel(cur, SQL)
    for row in rows:
        searchOption.append(row[1])
    searchExamName = st.selectbox("请选择考试场次", searchOption, index=None)
    options = st.multiselect(
        "查询类型",
        ["通过", "未通过"],
        ["通过", "未通过"],
    )
    if searchExamName:
        searchButton = st.button("查询")
    else:
        searchButton = st.button("查询", disabled=True)
    if searchButton and searchExamName:
        if options:
            tab1, tab2 = st.tabs(["简报", "详情"])
            SQL = "SELECT userName, userCName, examScore, examDate, examPass from examresult where examName = '" + searchExamName + "' and ("
            for each in options:
                if each == "通过":
                    SQL = SQL + " examPass = 1 or "
                elif each == "未通过":
                    SQL = SQL + " examPass = 0 or "
            if SQL.endswith(" or "):
                SQL = SQL[:-4] + ") order by ID DESC"
            rows = mdb_sel(cur, SQL)
            if rows:
                df = pd.DataFrame(rows, dtype=str)
                df.columns = ["编号", "姓名", "成绩", "考试日期", "考试结果"]
                for index, value in enumerate(rows):
                    df.loc[index, "考试日期"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(df["考试日期"][index])))
                    df.loc[index, "考试结果"] = "通过" if int(df["考试结果"][index]) == 1 else "未通过"
                tab2.dataframe(df.style.apply(highlight_max, backcolor='yellow', subset=["成绩", "考试结果"]))
            if rows:
                for row in rows:
                    tab1.markdown(f"考生ID:  :red[{row[0]}] 考生姓名: :red[{row[1]}] 考试时间: :red[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(row[3]))}]")
                    tab1.subheader(f"考试成绩: {row[2]} 分")
                    if row[4] == 1:
                        tab1.subheader("考试结果: :blue[通过] 👏")
                        tab1.subheader("", divider="orange")
                    else:
                        tab1.subheader("考试结果: :red[未通过] 😝")
                        tab1.subheader("", divider="red")
            else:
                st.warning("暂无数据")
        else:
            st.warning("请设置查询类型")


def queryExamResultUsers():
    ExamNamePack = []
    SQL = f"SELECT ID, examName from examidd where StationCN = '{st.session_state.StationCN}' order by ID"
    rows = mdb_sel(cur, SQL)
    for row in rows:
        ExamNamePack.append(row[1])
    searchExamName = st.selectbox("请选择考试场次", ExamNamePack, index=None)
    options = st.multiselect(
        "查询类型",
        ["已参加考试", "未参加考试"],
        ["未参加考试"],
    )
    searchButton = st.button("查询")
    if searchButton and searchExamName:
        if options:
            tab1, tab2 = st.tabs(["简报", "详情"])
            if len(options) == 2:
                SQL = "SELECT userName, userCName, StationCN from user where StationCN = '" + st.session_state.StationCN + "' order by ID"
            elif len(options) == 1:
                if options[0] == "已参加考试":
                    SQL = "SELECT user.userName, user.userCName, user.StationCN from user, examresult where examresult.examName = '" + searchExamName + "' and examresult.userName = user.userName and user.StationCN = '" + st.session_state.StationCN + "'"
                elif options[0] == "未参加考试":
                    SQL = "SELECT userName, userCName, StationCN from user where userName not in (SELECT user.userName from user, examresult where examresult.examName = '" + searchExamName + "' and examresult.userName = user.userName) and StationCN = '" + st.session_state.StationCN + "'"
            rows = mdb_sel(cur, SQL)
            if rows:
                df = pd.DataFrame(rows)
                df.columns = ["编号", "姓名", "站室"]
                tab2.dataframe(df)
            if rows:
                for row in rows:
                    SQL = "SELECT userName, userCName, examScore, examDate, examPass from examresult where examName = '" + searchExamName + "' and userName = " + str(row[0])
                    rows2 = mdb_sel(cur, SQL)
                    if rows2:
                        tab1.markdown(f"考生ID:  :red[{rows2[0][0]}] 考生姓名: :red[{rows2[0][1]}] 考试时间: :red[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(rows2[0][3]))}]")
                        tab1.subheader(f"考试成绩: {rows2[0][2]} 分")
                        if rows2[0][4] == 1:
                            tab1.subheader("考试结果: :blue[通过] 👏")
                            tab1.subheader("", divider="orange")
                        else:
                            tab1.subheader("考试结果: :red[未通过] 🤪")
                            tab1.subheader("", divider="red")
                    else:
                        tab1.subheader("未参加考试", divider="red")
                        tab1.markdown(f"考生ID:  :red[{row[0]}] 考生姓名: :red[{row[1]}] 站室: :red[{row[2]}]")
            else:
                st.warning("暂无数据")
        else:
            st.warning("请设置查询类型")


conn = apsw.Connection("./DB/ETest_enc.db")
cur = conn.cursor()
cur.execute("PRAGMA cipher = 'aes256cbc'")
cur.execute("PRAGMA key = '7745'")
cur.execute("PRAGMA journal_mode = WAL")

st.write("### :violet[信息查询]")
selectFunc = st.selectbox("查询项目", ["考试信息", "未参加考试人员", "答题解析"], index=None)
if selectFunc == "考试信息":
    queryExamResult()
elif selectFunc == "未参加考试人员":
    queryExamResultUsers()
elif selectFunc == "答题解析":
    queryExamName = st.selectbox("请选择考试场次", ["练习题库", "错题集"], index=0)
    if queryExamName:
        if queryExamName == "错题集":
            tablename = "morepractise"
        else:
            tablename = f"exam_final_{st.session_state.StationCN}_{st.session_state.userName}_{queryExamName}"
        SQL = "SELECT * from sqlite_master where type = 'table' and name = '" + tablename + "'"
        tempTable = mdb_sel(cur, SQL)
        if tempTable:
            queryExamAnswer(tablename)
        else:
            st.warning("暂无数据")
if selectFunc is not None:
    updateActionUser(st.session_state.userName, f"查询{selectFunc}", st.session_state.loginTime)
