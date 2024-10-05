# coding UTF-8
import os
import re
import time

import apsw
import openpyxl
import pandas as pd
import streamlit as st
import streamlit_antd_components as sac
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor
from streamlit_extras.badges import badge
from xlsxwriter.workbook import Workbook

from commFunc import (getParam, mdb_del, mdb_ins, mdb_modi, mdb_sel,
                      qianfan_AI_GenerQues, updatePyFileinfo)
from streamlit_extras.metric_cards import style_metric_cards

# cSpell:ignoreRegExp /[^\s]{16,}/
# cSpell:ignoreRegExp /\b[A-Z]{3,15}\b/g


def getUserCName(userName):
    SQL = "SELECT userCName, StationCN from user where userName = " + str(userName)
    rows = mdb_sel(cur, SQL)
    if rows:
        st.session_state.userCName = rows[0][0]
        st.session_state.StationCN = rows[0][1]
    else:
        st.session_state.userCName = "未找到"
        st.session_state.StationCN = "未找到"


def delOutdatedTable():
    if st.session_state.examRandom and "examTable" in st.session_state:
        mdb_del(conn, cur, SQL=f"DROP TABLE IF EXISTS {st.session_state.examTable}")
    if "examFinalTable" in st.session_state:
        mdb_del(conn, cur, SQL=f"DROP TABLE IF EXISTS {st.session_state.examFinalTable}")


def changePassword():
    st.write("### :red[修改密码]")
    changePW = st.empty()
    with changePW.container(border=True):
        oldPassword = st.text_input("请输入原密码", max_chars=8, type="password", autocomplete="off")
        newPassword = st.text_input("请输入新密码", max_chars=8, type="password", autocomplete="off")
        confirmPassword = st.text_input("请再次输入新密码", max_chars=8, placeholder="请与上一步输入的密码一致", type="password", autocomplete="off")
        if oldPassword:
            SQL = "SELECT ID from user where userName = " + str(st.session_state.userName) + " and userPassword = '" + oldPassword + "'"
            if mdb_sel(cur, SQL):
                if newPassword and confirmPassword and newPassword != "":
                    if newPassword == confirmPassword:
                        buttonSubmit = st.button("确认修改")
                        if buttonSubmit:
                            SQL = f"UPDATE user set userPassword = '{newPassword}' where userName = {st.session_state.userName}"
                            mdb_modi(conn, cur, SQL)
                            st.toast("密码修改成功, 请重新登录")
                            logout()
                    else:
                        st.warning("两次输入的密码不一致")
                else:
                    st.warning("请检查新密码")
            else:
                st.warning("原密码不正确")
        else:
            st.warning("原密码不能为空")


def login():
    st.write("## :blue[专业技能考试系统 - 离线版]")
    login = st.empty()
    with login.container(border=True):
        userName = st.text_input("请输入用户名", max_chars=8, placeholder="员工编码")
        if userName != "":
            getUserCName(userName)
            st.caption(f"用户名: :blue[{st.session_state.userCName}] 站室: :red[{st.session_state.StationCN}]")
        userPassword = st.text_input("请输入密码", max_chars=8, placeholder="用户初始密码为1234", type="password", autocomplete="off")
        examType = st.selectbox("请选择功能类型", ("练习", "考试"), index=0)
        buttonLogin = st.button("登录")
    if buttonLogin:
        if userName != "" and userPassword != "":
            SQL = "SELECT userName, userCName, userType, StationCN from user where userName = " + str(userName) + " and userPassword = '" + userPassword + "'"
            result = mdb_sel(cur, SQL)
            if result:
                st.toast(f"用户: {result[0][0]} 姓名: {result[0][1]} 登录成功, 欢迎回来")
                login.empty()
                st.session_state.logged_in = True
                st.session_state.userName = result[0][0]
                st.session_state.userCName = result[0][1]
                st.session_state.userType = result[0][2]
                st.session_state.StationCN = result[0][3]
                st.session_state.examLimit = getParam("同场考试次数限制", st.session_state.StationCN)
                st.session_state.debug = bool(getParam("测试模式", st.session_state.StationCN))
                st.session_state.curQues = 0
                st.session_state.examChosen = False
                ClearTables()
                if examType == "练习":
                    st.session_state.examType = "training"
                    st.session_state.examName = "练习题库"
                    st.session_state.examRandom = True
                elif examType == "考试":
                    st.session_state.examType = "exam"
                    st.session_state.examRandom = bool(getParam("考试题库每次随机生成", st.session_state.StationCN))
                st.rerun()
            else:
                st.warning("登录失败, 请检查用户名和密码")


def logout():
    delOutdatedTable()
    for key in st.session_state.keys():
        del st.session_state[key]
    st.session_state.logged_in = False

    cur.close()
    conn.close()

    st.rerun()


def todo():
    st.subheader("完善查询功能", divider='green')
    st.subheader("题库录入模块", divider='rainbow')


def aboutInfo():
    emoji = [["🥺", "very sad!"], ["😣", "bad!"], ["😏", "not bad!"], ["😋", "happy!"], ["😊", "fab, thank u so much!"]]
    st.subheader("关于本软件", divider="rainbow")
    st.subheader(":blue[Powered by Python and Streamlit]")
    logo1, logo2, logo3, logo4, logo5, logo6 = st.columns(6)
    logo7, logo8, logo9, logo10, logo11, logo12 = st.columns(6)
    with logo1:
        st.caption("Python")
        st.image("./Images/logos/python.png")
    with logo2:
        st.caption("Streamlit")
        st.image("./Images/logos/streamlit.png")
    with logo3:
        st.caption("SQLite")
        st.image("./Images/logos/sqlite.png")
    with logo4:
        st.caption("APSW")
        st.image("./Images/logos/apsw.png")
    with logo5:
        st.caption("Pandas")
        st.image("./Images/logos/pandas.png")
    with logo6:
        st.caption("Ant Design")
        st.image("./Images/logos/antd.png")
    with logo7:
        st.caption("iFlytek Spark")
        st.image("./Images/logos/xfxh.png")
    with logo8:
        st.caption("ERNIE Qianfan")
        st.image("./Images/logos/qianfan.png")
    with logo9:
        st.caption("DeepSeek")
        st.image("./Images/logos/deepseek.png")
    display_pypi()
    st.write("###### :violet[为了获得更好的使用体验, 请使用浅色主题]")
    SQL = "SELECT Sum(pyMC) from verinfo"
    verinfo = mdb_sel(cur, SQL)[0][0]
    SQL = "SELECT Max(pyLM) from verinfo"
    verLM = mdb_sel(cur, SQL)[0][0]
    SQL = "SELECT CAST(Sum(pyLM * pyMC) / Sum(pyMC) as FLOAT) from verinfo where pyFile = 'thumbs-up-stars'"
    likeCM = round(mdb_sel(cur, SQL)[0][0], 1)
    st.caption(f"{int(verinfo / 10000)}.{int((verinfo % 10000) / 100)}.{int(verinfo / 10)} building {verinfo} Last Modified: {time.strftime('%Y-%m-%d %H:%M', time.localtime(verLM))} 😍 {likeCM}")
    sac.divider(align="center", color="blue")
    stars = sac.rate(label='Please give me a star if you like it!', align='start')
    if stars > 0:
        st.write(f"I feel {emoji[stars - 1][1]} {emoji[stars - 1][0]}")
    SQL = f"UPDATE verinfo set pyMC = pyMC + 1 where pyFile = 'thumbs-up-stars' and pyLM = {stars}"
    mdb_modi(conn, cur, SQL)


def display_pypi():
    #st.write(":hotsprings: streamlit/apsw/pandas/streamlit-antd-components")
    pypi1, pypi2, pypi3, pypi4, pypi5, pypi6 = st.columns(6)
    with pypi1:
        badge(type="pypi", name="streamlit")
    with pypi2:
        badge(type="pypi", name="apsw")
    with pypi3:
        badge(type="pypi", name="pandas")
    with pypi4:
        badge(type="pypi", name="streamlit_antd_components")
    with pypi5:
        badge(type="pypi", name="spark_ai_python")
    with pypi6:
        badge(type="pypi", name="qianfan")
    #badge(type="github", name="simonpek88/ETest-SQLite ")


def aboutLicense():
    st.subheader("License", divider="green")
    st.markdown('''
        MIT License

        Copyright (c) 2024 :blue[Simon Lau] TradeMark :rainbow[Enjoy for AP] ™

        Permission is hereby granted, free of charge, to any person obtaining a copy
        of this software and associated documentation files (the "Software"), to deal
        in the Software without restriction, including without limitation the rights
        to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
        copies of the Software, and to permit persons to whom the Software is
        furnished to do so, subject to the following conditions:

        The above copyright notice and this permission notice shall be included in all
        copies or substantial portions of the Software.

        THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
        IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
        FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
        AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
        LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
        OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
        SOFTWARE.
        ''')


def actDelTable():
    for each in st.session_state.keys():
        if each.startswith("delStaticExamTable_"):
            if st.session_state[each]:
                each = each.replace("delStaticExamTable_", "")
                mdb_del(conn, cur, SQL=f"DROP TABLE IF EXISTS {each}")
                st.info(f"{each} 静态题库删除成功")


def delStaticExamTable():
    flagExistTable = False
    SQL = "SELECT name from sqlite_master where type = 'table' and name like 'exam_%'"
    tempTable = mdb_sel(cur, SQL)
    if tempTable:
        st.subheader("删除静态题库", divider="red")
        for row in tempTable:
            if row[0].count("_") == 2:
                st.checkbox(f"{row[0]}", key=f"delStaticExamTable_{row[0]}")
                flagExistTable = True
    if flagExistTable:
        st.button("确认删除", on_click=actDelTable)
    else:
        st.info("暂无静态题库")


def resultExcel():
    st.subheader("试卷导出", divider="blue")
    examResultPack, examResultPack2 = [], []
    SQL = "SELECT name from sqlite_master where type = 'table' and name like 'exam_final_%'"
    tempTable = mdb_sel(cur, SQL)
    if tempTable:
        for row in tempTable:
            examResultPack2.append(row[0])
            tmp = row[0][:row[0].rfind("_")]
            tmp = tmp[tmp.rfind("_") + 1:]
            SQL = "SELECT userCName from user where userName = " + str(tmp)
            tempTable = mdb_sel(cur, SQL)
            if tempTable:
                tempUserCName = tempTable[0][0]
                examResultPack.append(row[0].replace("exam_final_", "").replace(tmp, tempUserCName))
            else:
                examResultPack.append(row[0].replace("exam_final_", ""))
        examResult = st.selectbox(" ", examResultPack, index=None, label_visibility="collapsed")

        if examResult:
            for index, value in enumerate(examResultPack):
                if value == examResult:
                    examResult = examResultPack2[index]
                    break
            SQL = f"SELECT Question, qOption, qAnswer, qType, qAnalysis, userAnswer from {examResult} order by ID"
            rows = mdb_sel(cur, SQL)
            if rows:
                df = pd.DataFrame(rows)
                df.columns = ["题目", "选项", "标准答案", "类型", "解析", "你的答案"]
                st.dataframe(df)
    else:
        st.info("暂无试卷")


def examResulttoExcel():
    searchOption = []
    SQL = f"SELECT ID, examName from examidd where StationCN = '{st.session_state.StationCN}' order by ID"
    rows = mdb_sel(cur, SQL)
    for row in rows:
        searchOption.append(row[1])
    searchExamName = st.selectbox("请选择考试场次", searchOption, index=None)
    options = st.multiselect("查询类型", ["通过", "未通过"], default=["通过", "未通过"])
    if searchExamName:
        searchButton = st.button("导出为Excel文件")
        if searchButton and searchExamName:
            if options:
                SQL = "SELECT ID, userName, userCName, examScore, examDate, examPass from examresult where examName = '" + searchExamName + "' and ("
                for each in options:
                    if each == "通过":
                        SQL = SQL + " examPass = 1 or "
                    elif each == "未通过":
                        SQL = SQL + " examPass = 0 or "
                if SQL.endswith(" or "):
                    SQL = SQL[:-4] + ") order by ID"
                rows = mdb_sel(cur, SQL)
                outputFile = f"./ExamResult/{searchExamName}_{time.strftime('%Y%m%d%H%M%S', time.localtime(int(time.time())))}.xlsx"
                if os.path.exists(outputFile):
                    os.remove(outputFile)
                workbook = Workbook(outputFile)
                worksheet = workbook.add_worksheet(f"{searchExamName}考试成绩")
                k = 1
                title = ["ID", "编码", "姓名", "成绩", "考试时间", "考试结果"]
                for index, value in enumerate(title):
                    worksheet.write(0, index, value)
                k = 1
                for i, row in enumerate(rows):
                    for j, value in enumerate(row):
                        if j == 0:
                            value = k
                        if j == 4:
                            value = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(value)))
                        elif j == 5:
                            value = "通过" if value == 1 else "未通过"
                        worksheet.write(i + 1, j, value)
                    k = k + 1
                workbook.close()
                if os.path.exists(outputFile):
                    st.success(f":green[[{searchExamName}]] :gray[考试成绩成功导出至程序目录下] :orange[{outputFile[2:]}]")
                else:
                    st.warning(f":red[[{searchExamName}]] 考试成绩导出失败")


def ClearTables():
    SQL = "DELETE from questions where rowid NOT IN (SELECT Min(rowid) from questions GROUP BY Question, qType, StationCN, chapterName)"
    mdb_del(conn, cur, SQL)
    SQL = "DELETE from commquestions where rowid NOT IN (SELECT Min(rowid) from commquestions GROUP BY Question, qType)"
    mdb_del(conn, cur, SQL)
    SQL = "DELETE from morepractise where rowid NOT IN (SELECT Min(rowid) from morepractise GROUP BY Question, qType, userName)"
    mdb_del(conn, cur, SQL)
    SQL = "DELETE from questionaff where rowid NOT IN (SELECT Min(rowid) from questionaff GROUP BY chapterName, StationCN)"
    mdb_del(conn, cur, SQL)
    SQL = "DELETE from questionaff where chapterName <> '公共题库' and chapterName <> '错题集' and chapterName not in (SELECT DISTINCT(chapterName) from questions)"
    mdb_del(conn, cur, SQL)
    for each in ["questions", "commquestions", "morepractise"]:
        mdb_modi(conn, cur, SQL=f"update {each} set Question = REPLACE(Question,'\n', '')")
    st.toast("站室题库/公共题库/错题集/章节信息库 记录清理完成")


def questoWord():
    allType, validType, stationCName = [], [], []
    st.subheader("题库导出", divider="blue")
    SQL = f"SELECT paramName, param from setup_{st.session_state.StationCN} where paramType = 'questype'"
    rows = mdb_sel(cur, SQL)
    for row in rows:
        allType.append(row[0])
        if row[1] == 1:
            validType.append(row[0])
    quesTable = st.selectbox("请选择功能类型", ("站室题库", "公共题库", "试卷", "错题集"), index=None)
    quesType = st.multiselect("题型", allType, default=allType)
    stationCN, headerExamName = "全站", ""
    if quesTable == "站室题库" or quesTable == "错题集":
        stationCName.append("全站")
        SQL = "SELECT Station from stations order by ID"
        rows = mdb_sel(cur, SQL)
        for row in rows:
            stationCName.append(row[0])
        stationCN = st.select_slider("站室", stationCName, value=st.session_state.StationCN)
    elif quesTable == "试卷":
        headerExamName = st.text_input("请设置试卷名称", max_chars=20, help="文件抬头显示的试卷名称, 不填则使用默认名称")
        if "examFinalTable" in st.session_state:
            stationCN = st.session_state.StationCN
            tablename = st.session_state.examFinalTable
            st.write("📢:red[试卷题库如果导出文件中不包含设置的题型, 请在功能👉参数设置👉题型设置👉重新设置后再生成题库后导出, 其他类型题库没有此限制. 下面的设置是个展示, 无法点击和修改]😊")
            st.image("./Images/dbsetup.png", caption="更改设置示例")
        else:
            st.warning("请先生成题库")
            quesTable = ""
    sac.switch(label="复核模式", on_label="On", align='start', size='md', value=False, key="sac_recheck")
    if quesTable and quesType:
        buttonSubmit = st.button("导出为Word文件")
        if buttonSubmit:
            if quesTable == "站室题库":
                tablename = "questions"
            elif quesTable == "公共题库":
                tablename = "commquestions"
            elif quesTable == "试卷":
                tablename = st.session_state.examFinalTable
            elif quesTable == "错题集":
                tablename = "morepractise"
            headerFS = getParam("抬头字体大小", st.session_state.StationCN)
            titleFS = getParam("题型字体大小", st.session_state.StationCN)
            quesFS = getParam("题目字体大小", st.session_state.StationCN)
            optionFS = getParam("选项字体大小", st.session_state.StationCN)
            answerFS = getParam("复核信息字体大小", st.session_state.StationCN)
            quesDOC = Document()
            quesDOC.styles["Normal"].font.name = "Microsoft YaHei"
            quesDOC.styles["Normal"]._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
            option, radioOption = ["A", "B", "C", "D", "E", "F", "G", "H"], ["正确", "错误"]
            blank = f"({' ' * 20})"
            pHeader = quesDOC.add_paragraph()
            pHeader.alignment = WD_ALIGN_PARAGRAPH.CENTER
            textHeader = pHeader.add_run(f"{st.session_state.StationCN} {headerExamName} {quesTable}", 0)
            #textHeader.font.name = "Microsoft YaHei"
            #textHeader.element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
            textHeader.font.size = Pt(headerFS)
            textHeader.font.bold = True
            textHeader.font.color.rgb = RGBColor(40, 106, 205)
            for each in quesType:
                if quesTable == "站室题库" or quesTable == "错题集":
                    if stationCN == "全站":
                        SQL = f"SELECT Question, qOption, qAnswer, qType, ID, SourceType from {tablename} where qType = '{each}' order by ID"
                    else:
                        SQL = f"SELECT Question, qOption, qAnswer, qType, ID, SourceType from {tablename} where qType = '{each}' and StationCN = '{stationCN}' order by ID"
                else:
                    SQL = f"SELECT Question, qOption, qAnswer, qType, ID, SourceType from {tablename} where qType = '{each}' order by ID"
                rows = mdb_sel(cur, SQL)
                #st.write(f"{each} 共 {len(rows)}")
                i = 1
                if rows:
                    pTitle = quesDOC.add_paragraph()
                    textTitle = pTitle.add_run(f"{each}", 0)
                    #textTitle.font.name = "Microsoft YaHei"
                    #textTitle.element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
                    textTitle.font.size = Pt(titleFS)
                    textTitle.bold = True
                    for row in rows:
                        tmp, answer, qa, aa = "", "", [], []
                        pQues = quesDOC.add_paragraph()
                        if each == "填空题":
                            textQues = pQues.add_run(f"第{i}题   {row[0].replace('()', blank).replace('（）', blank)}", 0)
                        else:
                            textQues = pQues.add_run(f"第{i}题   {row[0]}   ({' ' * 8})", 0)
                        #textQues.font.name = "Microsoft YaHei"
                        #textQues.element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
                        textQues.font.size = Pt(quesFS)
                        #if st.session_state.sac_recheck and row[5] == "AI-LLM":
                        #textQues.font.color.rgb = RGBColor(155, 17, 30)
                        aa = row[2].replace("；", ";").split(";")
                        if each != "填空题":
                            pOption = quesDOC.add_paragraph()
                        if each == "单选题" or each == "多选题":
                            qa = row[1].replace("；", ";").split(";")
                            for each2 in qa:
                                tmp = tmp + f"{option[qa.index(each2)]}. {each2}{' ' * 8}"
                            textOption = pOption.add_run(tmp)
                        elif each == "判断题":
                            textOption = pOption.add_run(f"A. 正确{' ' * 15}B. 错误{' ' * 15}")
                        #textOption.font.name = "Microsoft YaHei"
                        #textOption.element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
                        textOption.font.size = Pt(optionFS)
                        #textOption.italic = True
                        if st.session_state.sac_recheck:
                            if each == "单选题" or each == "多选题":
                                for each3 in aa:
                                    answer = answer + f"{option[int(each3)]}" + ", "
                            elif each == "判断题":
                                answer = radioOption[int(aa[0]) ^ 1]
                            elif each == "填空题":
                                for index, value in enumerate(aa):
                                    answer = answer + f"{chr(49 + index)}.  [{value}]" + " "
                            if answer.endswith(", "):
                                answer = answer[:-2]
                            elif answer.endswith(" "):
                                answer = answer[:-1]
                            pAnswer = quesDOC.add_paragraph()
                            textAnswer = pAnswer.add_run(f"复核模式 ID: {row[4]} 正确答案: {answer}")
                            textAnswer.font.size = Pt(answerFS)
                            textAnswer.font.bold = True
                            textAnswer.font.color.rgb = RGBColor(155, 17, 30)
                            if stationCN != "全站":
                                SQL = f"SELECT chapterName from questions where Question = '{row[0]}'"
                            else:
                                SQL = f"SELECT chapterName from questions where Question = '{row[0]}' and StationCN = '{stationCN}'"
                            tempTable = mdb_sel(cur, SQL)
                            if tempTable:
                                fhQT = tempTable[0][0]
                            else:
                                SQL = f"SELECT ID from commquestions where Question = '{row[0]}'"
                                if mdb_sel(cur, SQL):
                                    fhQT = "公共题库"
                            pSource = quesDOC.add_paragraph()
                            if row[5] != "AI-LLM":
                                textSource = pSource.add_run(f"试题来源: [{stationCN}] 章节名称: [{fhQT}] 试题生成类别: [{row[5]}]")
                            else:
                                textSource = pSource.add_run(f"请特别注意 试题来源: [{stationCN}] 章节名称: [{fhQT}] 试题生成类别: [{row[5]}]")
                            textSource.font.bold = True
                            textSource.font.size = Pt(answerFS)
                            if row[5] == "AI-LLM":
                                textSource.font.color.rgb = RGBColor(155, 17, 30)
                                textSource.font.underline = True
                            #textSource.font.italic = True
                        i += 1
            if headerExamName != "":
                outputFile = f"./QuesDoc/{st.session_state.StationCN}-{headerExamName}-{quesTable}_{time.strftime('%Y%m%d%H%M%S', time.localtime(int(time.time())))}.docx"
            else:
                outputFile = f"./QuesDoc/{st.session_state.StationCN}-{quesTable}_{time.strftime('%Y%m%d%H%M%S', time.localtime(int(time.time())))}.docx"
            if os.path.exists(outputFile):
                os.remove(outputFile)
            quesDOC.save(outputFile)
            if os.path.exists(outputFile):
                st.success(f":green[[{quesTable}]] :gray[题库成功导出至程序目录下] :orange[{outputFile[2:]}]")
            else:
                st.warning(f":red[[{quesTable}]] 题库导出失败")


def dboutput():
    bc = sac.segmented(
        items=[
            sac.SegmentedItem(label="题库导出(Word格式)", icon="database-down"),
            sac.SegmentedItem(label="试卷导出(DF格式)", icon="journal-arrow-down"),
            sac.SegmentedItem(label="考试成绩导出(Excel格式)", icon="layout-text-sidebar-reverse"),
        ], color="green", align="center"
    )
    if bc == "题库导出(Word格式)":
        questoWord()
    elif bc == "试卷导出(DF格式)":
        resultExcel()
    elif bc == "考试成绩导出(Excel格式)":
        examResulttoExcel()


def dbinputSubmit(tarTable, orgTable):
    tmpTable = ""
    if tarTable == "站室题库":
        tablename = "questions"
        SQL = f"INSERT INTO {tablename}(Question, qOption, qAnswer, qType, qAnalysis, StationCN, chapterName, SourceType) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        maxcol = 8
    elif tarTable == "公共题库":
        tablename = "commquestions"
        SQL = f"INSERT INTO {tablename}(Question, qOption, qAnswer, qType, qAnalysis, SourceType) VALUES (?, ?, ?, ?, ?, ?)"
        maxcol = 6
    st.spinner(f"正在向 [{tarTable}] 导入题库...")
    for each in orgTable:
        listinsheet = openpyxl.load_workbook(f"./InputQues/{each}.xlsx")
        datainlist = listinsheet.active
        for row in datainlist.iter_rows(min_row=2, max_col=maxcol, max_row=datainlist.max_row):
            singleQues = [cell.value for cell in row]
            cur.execute(SQL, singleQues)
        listinsheet.close()
        tmpTable = tmpTable + each + ", "
    SQL = f"UPDATE {tablename} set qOption = '' where qOption is Null"
    mdb_modi(conn, cur, SQL)
    SQL = f"UPDATE {tablename} set qAnalysis = '' where qAnalysis is Null"
    mdb_modi(conn, cur, SQL)
    SQL = f"UPDATE {tablename} set SourceType = '人工' where SourceType is Null"
    mdb_modi(conn, cur, SQL)
    SQL = "INSERT INTO questionaff(chapterName, StationCN, chapterRatio) SELECT DISTINCT chapterName, StationCN, 5 FROM questions"
    mdb_ins(conn, cur, SQL)
    ClearTables()
    st.success(f":green[[{tmpTable[:-2]}] 向 [{tarTable}]] :gray[导入成功]")


def dbinput():
    inputOption = []
    targetTable = st.radio("导入至:", ("站室题库", "公共题库"), index=None, horizontal=True)
    if targetTable:
        for root, dirs, files in os.walk("./InputQues"):
            for file in files:
                if os.path.splitext(file)[1].lower() == '.xlsx' and os.path.splitext(file)[0].endswith(f"_{targetTable}"):
                    inputOption.append(os.path.splitext(file)[0])
        if inputOption:
            orgTable = st.multiselect("请选择导入文件", inputOption, default=None)
            if orgTable:
                st.button("导入", on_click=dbinputSubmit, args=(targetTable, orgTable))
            else:
                st.warning("请选择要导入的文件")
        else:
            st.warning("没有可导入的文件")
    else:
        st.write("请选择要导入的题库")


def dbfunc():
    bc = sac.segmented(
        items=[
            sac.SegmentedItem(label="A.I.出题", icon="robot"),
            sac.SegmentedItem(label="题库导入", icon="database-up"),
            #sac.SegmentedItem(label="Word文件导入", icon="text-wrap", disabled=st.session_state.debug ^ True),
            sac.SegmentedItem(label="删除单个试题", icon="x-circle"),
            sac.SegmentedItem(label="错题集重置", icon="journal-x"),
            sac.SegmentedItem(label="删除静态题库", icon="trash3"),
            #sac.SegmentedItem(label="重置题库ID", icon="bootstrap-reboot", disabled=st.session_state.debug ^ True),
        ], align="start", color="red"
    )
    if bc == "A.I.出题":
        AIGenerQues()
    elif bc == "题库导入":
        dbinput()
    elif bc == "Word文件导入":
        inputWord()
    elif bc == "删除单个试题":
        deleteSingleQues()
    elif bc == "清空错题集":
        ClearMP()
    elif bc == "删除静态题库":
        delStaticExamTable()
    elif bc == "重置题库ID":
        buttonReset = st.button("重置ID", type="primary")
        if buttonReset:
            st.button("确认重置", type="secondary", on_click=resetTableID)


def deleteSingleQues():
    tablename = st.selectbox("请选择要删除:red[单个试题]所在的题库", ("站室题库", "公共题库", "错题集"), index=None)
    if tablename:
        st.number_input("请输入要删除的试题ID", min_value=1, max_value=999999, placeholder="每个题库试题的ID都不一样, 相同ID可以在不同题库, 一定要检查题库和ID是否一致", key="delQuesID")
        buttonConfirm = st.button("删除", type="primary")
        if buttonConfirm:
            st.button("确认删除", type="secondary", on_click=deleteQues, args=(tablename,))


def deleteQues(tablename):
    if tablename == "站室题库":
        targetTable = "questions"
    elif tablename == "公共题库":
        targetTable = "commquestions"
    elif tablename == "错题集":
        targetTable = "morepractise"
    SQL = f"DELETE from {targetTable} where ID = {st.session_state.delQuesID}"
    mdb_modi(conn, cur, SQL)
    st.success(f"已 :red[删除] {tablename} 中ID为 {st.session_state.delQuesID} 的试题")


def inputWord():
    #doc = Document("./QuesRefer/特种设备安全管理员考试题库精选全文.docx")
    #doc = Document("./QuesRefer/(新版)特种设备安全管理人员(特种作业)考试题库.docx")
    #doc = Document("./QuesRefer/(新版)特种设备安全管理人员资格(特种作业)考试题库(全真题库).docx")
    #doc = Document("./QuesRefer/2023年全国特种设备作业人员考试题库附答案.docx")
    doc = Document("./QuesRefer/2023年特种设备作业安全管理人员证考试题库(通用版).docx")
    chapter = "特种设备安全管理员"
    #title_rule = re.compile("\\d+、")
    title_rule = re.compile("\\d+.")
    option_rule = re.compile("\\w+、")
    ques, qAnswer, temp2, generQuesCount, qType = "", "", "", 0, ""
    if st.session_state.debug:
        os.system("cls")
    st.spinner("正在导入Word文件...")
    for i, paragraph in enumerate(doc.paragraphs[:]):
        line = paragraph.text.replace('\n', '').replace('\r', '').replace("（", "(").replace("）", ")").strip()
        if line:
            #if title_rule.search(line):
            if line[:7].find(".") != -1:
                if temp2.endswith(";"):
                    temp2 = temp2[:-1]
                    qOption = temp2
                    temp2 = ""
                if ques != "" and qAnswer != "" and qOption != "":
                    if qOption.find("正确;错误") != -1:
                        qType = "判断题"
                        qAnswer = int(qAnswer) ^ 1
                        qOption = ""
                    elif len(qAnswer) == 1:
                        qType = "单选题"
                    elif len(qAnswer) > 1:
                        qType = "多选题"
                    if st.session_state.debug:
                        print(f"Record: Q: {ques} T: {qType} O: {qOption} A: {qAnswer}")
                    SQL = f"SELECT ID from questions where Question = '{ques}' and qType = '{qType}' and StationCN = '{st.session_state.StationCN}' and chapterName = '{chapter}'"
                    if not mdb_sel(cur, SQL):
                        SQL = f"INSERT INTO questions(Question, qOption, qAnswer, qType, StationCN, chapterName, SourceType) VALUES ('{ques}', '{qOption}', '{qAnswer}', '{qType}', '{st.session_state.StationCN}', '{chapter}', '人工')"
                        mdb_ins(conn, cur, SQL)
                        generQuesCount += 1
                    ques, qAnswer, qOption = "", "", ""
                temp = ""
                if st.session_state.debug:
                    print(f"Ques:{line}")
                if line[:7].find("、") != -1:
                    ques = line[line.find("、") + 1:]
                elif line[:7].find(".") != -1:
                    ques = line[line.find(".") + 1:]
                if ques.startswith("."):
                    ques = ques[1:]
                qAnswer = ""
                while True:
                    b1 = line.find('(')
                    b2 = line.find(')')
                    if b1 != -1 and b2 != -1 and line[b1 + 1:b1 + 2] in ["A", "B", "C", "D", "E", "F"]:
                        temp = line[b1 + 1:b2]
                        ques = ques.replace(temp, " " * len(temp))
                        temp = temp.replace("、", "")
                        for each in temp:
                            qAnswer = qAnswer + str(ord(each) - 65) + ";"
                        line = line[b2 + 1:]
                    else:
                        break
                if qAnswer.endswith(";"):
                    qAnswer = qAnswer[:-1]
            elif option_rule.search(line):
                if st.session_state.debug:
                    print(f"{line}")
                temp2 = temp2 + line[2:] + ";"
            elif line.find("正确答案：") != -1:
                print(line)
                temp = line[line.find("正确答案：") + 5:]
                for each in temp:
                    qAnswer = qAnswer + str(ord(each) - 65) + ";"
                if qAnswer.endswith(";"):
                    qAnswer = qAnswer[:-1]
        else:
            continue
    ClearTables()
    st.success(f"共生成{generQuesCount}道试题")


def resetTableID():
    for tablename in ["questions", "commquestions", "morepractise", "questionaff", "studyinfo", "setup_默认", f"setup_{st.session_state.StationCN}"]:
        SQL = f"SELECT ID from {tablename} order by ID"
        rows = mdb_sel(cur, SQL)
        for i, row in enumerate(rows):
            SQL = f"UPDATE {tablename} set ID = {i + 1} where ID = {row[0]}"
            mdb_modi(conn, cur, SQL)
    st.success("题库ID重置成功")


def AIGenerQues():
    quesPack, chars, chapterPack, dynaQuesType, generQuesCount = [], ["A", "B", "C", "D", "E", "F", "G", "H"], [], ["单选题", "多选题", "判断题", "填空题"], 0
    StationCNPack, chosenStationCN = [], st.session_state.StationCN
    temp = "站室题库现有: "
    for each in dynaQuesType:
        SQL = f"SELECT Count(ID) from questions where qType = '{each}'"
        qCount = mdb_sel(cur, SQL)[0][0]
        temp = temp + "[:red[" + each + "]] " + str(qCount) + "道 "
    temp = temp + "\n\n公共题库现有: "
    for each in dynaQuesType:
        SQL = f"SELECT Count(ID) from commquestions where qType = '{each}'"
        qCount = mdb_sel(cur, SQL)[0][0]
        temp = temp + "[:red[" + each + "]] " + str(qCount) + "道 "
    temp = temp.strip()
    st.caption(temp)
    table = st.radio(label="请选择要生成的题库", options=("站室题库", "公共题库"), horizontal=True, index=None)
    if table and table != "公共题库":
        SQL = "SELECT Station from stations order by ID"
        rows = mdb_sel(cur, SQL)
        for row in rows:
            StationCNPack.append(row[0])
        chosenStationCN = st.select_slider("请选择要导入的站室", options=StationCNPack, value=st.session_state.StationCN)
        col1, col2 = st.columns(2)
        SQL = f"SELECT chapterName from questionaff where StationCN = '{chosenStationCN}' and chapterName <> '公共题库' and chapterName <> '错题集'"
        rows = mdb_sel(cur, SQL)
        for row in rows:
            chapterPack.append(row[0])
        with col1:
            chapter = st.selectbox(label="请选择章节", options=chapterPack, index=None)
        with col2:
            textChapter = st.text_input("请输入新章节名称", value="", placeholder="添加新的章节")
            textChapter = textChapter.strip()
    elif table == "公共题库":
        chapter, textChapter = "", ""
    quesRefer = st.text_area("请输入参考资料")
    quesType = st.radio(label="请选择要生成的题型", options=("单选题", "多选题", "判断题", "填空题"), index=None, horizontal=True)
    quesCount = st.number_input("请输入要生成的题目数量", min_value=1, max_value=10, value=5, step=1)
    if table is not None and quesRefer != "" and quesType is not None:
        buttonGener = st.button("生成试题")
        if buttonGener:
            if chapter is None and textChapter != "":
                SQL = f"SELECT ID from questionaff where chapterName = '{textChapter}' and StationCN = '{chosenStationCN}'"
                if not mdb_sel(cur, SQL):
                    SQL = f"INSERT INTO questionaff(chapterName, StationCN, chapterRatio) VALUES ('{textChapter}', '{chosenStationCN}', 5)"
                    mdb_ins(conn, cur, SQL)
                    st.toast(f"新的章节: :red[{textChapter}]添加完毕")
                chapter = textChapter
            if chapter is not None and table == "站室题库" or table == "公共题库":
                outputFile = f"./outputQues/{chosenStationCN}-{table}-{chapter}-{quesType}_{time.strftime('%Y%m%d%H%M%S', time.localtime(int(time.time())))}.txt"
                if os.path.exists(outputFile):
                    os.remove(os.path)
                if st.session_state.debug:
                    os.system("cls")
                generQuesCount, displayQues = 0, ""
                infoArea = st.empty()
                with infoArea.container():
                    st.info("正在使用 :red[文心千帆大模型] 进行试题生成, 请稍等...")
                ques = qianfan_AI_GenerQues(quesRefer, quesType, quesCount, "ERNIE-Speed-8K")
                quesPack = ques.split("题型")
                for each in quesPack:
                    if each != "":
                        quesHeader, qOption, Option, qAnswer, qAnalysis, flagSuccess = "", "", [], "", "", True
                        temp = each[:10]
                        for dqt in dynaQuesType:
                            if temp.find(dqt) != -1:
                                quesType = dqt
                                break
                        b1 = each.find("试题")
                        if b1 != -1:
                            each = each[b1 + 3:]
                            c1 = each.find("标准答案")
                            c2 = each.find("试题解析")
                            b2 = each.find("选项")
                            if c1 != -1 and c2 != -1:
                                if quesType == "填空题":
                                    quesHeader = each[:c1].replace("\n\n", "").replace("\n", "").replace("**", "").replace("无选项，填写空白处即可。", "").replace("无选项，本题为填空题", "").replace("选项：", "").strip()
                                else:
                                    quesHeader = each[:b2].replace("\n\n", "").replace("\n", "").replace("**", "").strip()
                                if quesHeader.startswith("*: "):
                                    quesHeader = quesHeader[3:]
                                if quesType == "单选题" or quesType == "多选题":
                                    b3 = each.find("标准答案")
                                    if b3 != -1:
                                        Option = each[b2 + 3:b3].replace("\n\n", "").replace("正确的？ 选项：", "").replace("正确的？", "").strip().split("\n")
                                        displayOption = each[b2 + 3:b3].replace("**", "").replace("正确的？ 选项：", "").replace("正确的？", "").strip()
                                        displayOption = displayOption.replace("A. ", "\n\nA. ").replace("B. ", "\nB. ").replace("C. ", "\nC. ").replace("D. ", "\nD. ").replace("E. ", "\nE. ").replace("F. ", "\nF. ").replace("G. ", "\nG. ").replace("H. ", "\nH. ")
                                        for each2 in Option:
                                            for each3 in chars:
                                                each2 = each2.replace(f"{each3}.", "").strip()
                                            qOption = qOption + each2 + ";"
                                        if qOption.endswith(";"):
                                            qOption = qOption[:-1]
                                        b4 = each.find("试题解析")
                                        if b4 != -1:
                                            qAnswer = each[b3 + 5:b4].replace("\n", "").replace("*", "").strip()
                                            displayAnswer = qAnswer
                                            qAnalysis = each[b4 + 5:].replace("\n", "").replace("*", "").strip()
                                            if quesType == "单选题":
                                                qAnswer = ord(qAnswer[0].upper()) - 65
                                                if qAnswer > 7 or qAnswer < 0:
                                                    flagSuccess = False
                                            elif quesType == "多选题":
                                                qAnswer = qAnswer.replace("，", "").replace(",", "").replace("、", "").replace("。", "").replace(" ", "").replace("（", "(")
                                                if qAnswer.find("(") != -1:
                                                    qAnswer = qAnswer[:qAnswer.find("(")].strip()
                                                temp = ""
                                                print(f"未处理前的多选题标准答案:{qAnswer}")
                                                for each4 in qAnswer:
                                                    if ord(each4.upper()) - 65 > 7 or ord(each4.upper()) - 65 < 0:
                                                        flagSuccess = False
                                                        break
                                                    else:
                                                        temp = temp + str(ord(each4) - 65) + ";"
                                                qAnswer = temp
                                                if qAnswer.endswith(";"):
                                                    qAnswer = qAnswer[:-1]
                                elif quesType == "判断题":
                                    if each[c1 + 5:c2].find("正确") != -1 or each[c1 + 5:c2].find("A") != -1:
                                        qAnswer = "1"
                                        displayAnswer = "正确"
                                    else:
                                        qAnswer = "0"
                                        displayAnswer = "错误"
                                    displayOption = "A. 正确\nB. 错误\n"
                                    qAnalysis = each[c2 + 5:].replace("\n", "").replace("*", "").strip()
                                elif quesType == "填空题":
                                    displayOption = ""
                                    qAnswer = each[c1 + 5:c2].replace("\n", "").replace("*", "").replace("无选项", "").replace("；", ";").replace("，", ";").replace("。", "").replace("、", ";").strip()
                                    if qAnswer.startswith(":"):
                                        qAnswer = qAnswer[1:]
                                    displayAnswer = qAnswer
                                    qAnalysis = each[c2 + 5:].replace("\n", "").replace("*", "").strip()
                                    i = 12
                                    while i > 0:
                                        if quesHeader.find("_" * i) != -1:
                                            quesHeader = quesHeader.replace("_" * i, "()")
                                        i -= 1
                            if qAnalysis.startswith(":"):
                                qAnalysis = qAnalysis[1:].strip()
                            if qAnalysis.endswith("---"):
                                qAnalysis = qAnalysis[:-3].strip()
                            if quesType == "单选题" and len(str(qAnswer)) > 1:
                                flagSuccess = False
                            if st.session_state.debug:
                                print(f"debug: 题目:[{quesHeader}] 选项:[{qOption}], 标准答案:[{qAnswer}] 答题解析:[{qAnalysis}]")
                        if qAnswer != "" and quesHeader != "" and len(str(qAnswer)) < 200 and len(quesHeader) < 200 and flagSuccess:
                            if table == "公共题库":
                                SQL = f"SELECT ID from commquestions where Question = '{quesHeader}' and qType = '{quesType}'"
                                if not mdb_sel(cur, SQL):
                                    SQL = f"INSERT INTO commquestions(Question, qOption, qAnswer, qType, qAnalysis, SourceType) VALUES('{quesHeader}', '{qOption}', '{qAnswer}', '{quesType}', '{qAnalysis}', 'AI-LLM')"
                                    mdb_ins(conn, cur, SQL)
                                    generQuesCount += 1
                            elif table == "站室题库":
                                SQL = f"SELECT ID from questions where Question = '{quesHeader}' and qType = '{quesType}' and StationCN = '{chosenStationCN}' and chapterName = '{chapter}'"
                                if not mdb_sel(cur, SQL):
                                    SQL = f"INSERT INTO questions(Question, qOption, qAnswer, qType, qAnalysis, StationCN, chapterName, SourceType) VALUES('{quesHeader}', '{qOption}', '{qAnswer}', '{quesType}', '{qAnalysis}', '{chosenStationCN}', '{chapter}', 'AI-LLM')"
                                    mdb_ins(conn, cur, SQL)
                                    generQuesCount += 1
                            displayQues = displayQues + f":blue[**第{generQuesCount}题:**]\n\n:red[题型: ]{quesType}\n\n:red[题目: ]{quesHeader}\n\n:red[选项: ]\n{displayOption}\n\n:red[答案: ]{displayAnswer}\n\n:red[解析: ]{qAnalysis}\n\n{'-' * 40}\n\n"
                infoArea.empty()
                if generQuesCount > 0:
                    st.success("试题生成成功")
                    st.subheader(f"A.I.生成{generQuesCount}道试题:", divider="green")
                    st.markdown(displayQues)
                    #with open(outputFile, mode="w", encoding='utf-8') as f:
                    #f.write(displayQues.replace(" ]", "").replace("]", "").replace("**", "").replace("-" * 40, "").replace(":blue[", "").replace(":red[", "").replace("\n\n", "\n"))
                    #f.close()
                else:
                    st.info("A.I.未生成到任何试题, 请检查参考资料是否正确或是生成的试题已经在题库中")
            else:
                st.warning("站室题库请选择章节")
    else:
        st.info("请设置各选项和添加参考资料")


def ClearMP():
    buttonSubmit = st.button("清空所有内容", type="primary")
    if buttonSubmit:
        bcArea = st.empty()
        with bcArea.container():
            st.button("确认清空", type="secondary", on_click=ClearMPAction, args=(bcArea,))


def ClearMPAction(bcArea):
    mdb_del(conn, cur, SQL="DELETE FROM morepractise")
    bcArea.empty()
    st.success("错题集已清空")


def studyinfo():
    study = sac.segmented(
        items=[
            sac.SegmentedItem(label="学习进度", icon="grid-3x2-gap"),
            sac.SegmentedItem(label="错题集", icon="list-stars"),
            sac.SegmentedItem(label="学习记录重置", icon="bootstrap-reboot"),
        ], align="center", color="red"
    )
    if study == "学习进度":
        studyinfoDetail()
    if study == "错题集":
        displayErrorQues()
    elif study == "学习记录重置":
        studyReset()


def displayErrorQues():
    SQL = f"SELECT Question, qOption, qAnswer, qType, qAnalysis, userAnswer, ID, WrongTime from morepractise where userAnswer <> '' and qAnswer <> userAnswer and userName = {st.session_state.userName} order by WrongTime DESC"
    rows = mdb_sel(cur, SQL)
    if rows:
        for row in rows:
            #st.subheader("", divider="red")
            with st.expander(label=f"题目: {row[0]} 次数: {row[7]}", expanded=False):
                if row[3] == "单选题":
                    st.write(":red[标准答案:]")
                    option, userAnswer = [], ["A", "B", "C", "D"]
                    tmp = row[1].replace("；", ";").split(";")
                    for index, each in enumerate(tmp):
                        each = each.replace("\n", "").replace("\t", "").strip()
                        option.append(f"{userAnswer[index]}. {each}")
                    st.radio(" ", option, key=f"compare_{row[6]}", index=int(row[2]), horizontal=True, label_visibility="collapsed", disabled=True)
                    st.write(f"你的答案: :red[{userAnswer[int(row[5])]}] 你的选择为: :blue[错误]")
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
                    st.write(f"你的答案: :red[{tmp[:-2]}] 你的选择为: :blue[错误]")
                elif row[3] == "判断题":
                    st.write(":red[标准答案:]")
                    option = ["A. 正确", "B. 错误"]
                    tmp = int(row[2]) ^ 1
                    st.radio(" ", option, key=f"compare_{row[6]}", index=tmp, horizontal=True, label_visibility="collapsed", disabled=True)
                    tmp = int(row[5]) ^ 1
                    st.write(f"你的答案: :red[{option[tmp]}] 你的选择为: :blue[错误]")
                elif row[3] == "填空题":
                    option = row[2].replace("；", ";").split(";")
                    userAnswer = row[5].replace("；", ";").split(";")
                    st.write(":red[标准答案:]")
                    for index, value in enumerate(option):
                        st.write(f"第{index + 1}个填空: :green[{value}]")
                    st.write("你的答案:")
                    for index, value in enumerate(userAnswer):
                        st.write(f"第{index + 1}个填空: :red[{value}]")
                    st.write("你的填写为: :blue[错误]")
                if row[4] != "":
                    if row[4].endswith("]"):
                        #st.write(row[4])
                        st.markdown(f"答案解析: {row[4][:-1]}]")
                    else:
                        st.markdown(f"答案解析: :green[{row[4]}]")
    else:
        st.info("暂无数据")


def studyReset():
    buttonSubmit = st.button("重置学习记录", type="primary")
    if buttonSubmit:
        st.button("确认重置", type="secondary", on_click=studyResetAction)


def studyResetAction():
    SQL = f"DELETE from studyinfo where userName = {st.session_state.userName}"
    mdb_del(conn, cur, SQL)
    st.success("学习记录已重置")


def studyinfoDetail():
    scol1, scol2, scol3, scol4, scol5 = st.columns(5)
    scol1.metric(label="姓名", value=st.session_state.userCName, help=st.session_state.userCName)
    scol2.metric(label="站室", value=st.session_state.StationCN, help=st.session_state.StationCN)
    SQL = f"SELECT Count(ID) from questionaff where StationCN = '{st.session_state.StationCN}' and chapterName <> '错题集'"
    rows = mdb_sel(cur, SQL)
    scol3.metric(label="章节总计", value=rows[0][0], help="包含公共题库, 不含错题集")
    SQL = f"SELECT Count(ID) from questions where StationCN = '{st.session_state.StationCN}' UNION SELECT Count(ID) from commquestions"
    rows = mdb_sel(cur, SQL)
    ct = rows[0][0] + rows[1][0]
    scol4.metric(label="试题总计", value=ct, help="包含公共题库, 不含错题集")
    SQL = f"SELECT Count(ID) from studyinfo where userName = {st.session_state.userName}"
    rows = mdb_sel(cur, SQL)
    scol5.metric(label="已学习试题", value=rows[0][0], help=f"总完成率: {int(rows[0][0] / ct * 100)}%")
    style_metric_cards(border_left_color="#8581d9")
    st.write("###### :violet[如果上面6个标签无显示内容, 请改用浅色主题]")
    with st.expander("各章节进度详情", icon=":material/format_list_bulleted:", expanded=True):
        SQL = "SELECT Count(ID) from commquestions"
        ct = mdb_sel(cur, SQL)[0][0]
        if ct > 0:
            SQL = f"SELECT Count(ID) from studyinfo where userName = {st.session_state.userName} and chapterName = '公共题库'"
            cs = mdb_sel(cur, SQL)[0][0]
            st.progress(value=cs / ct, text=f":blue[公共题库] 已完成 :orange[{int((cs / ct) * 100)}%]")
        SQL = f"SELECT chapterName from questionaff where StationCN = '{st.session_state.StationCN}' and chapterName <> '公共题库' and chapterName <> '错题集' order by ID"
        rows = mdb_sel(cur, SQL)
        for row in rows:
            SQL = f"SELECT Count(ID) from questions where StationCN = '{st.session_state.StationCN}' and chapterName = '{row[0]}'"
            ct = mdb_sel(cur, SQL)[0][0]
            if ct > 0:
                SQL = f"SELECT Count(ID) from studyinfo where userName = {st.session_state.userName} and chapterName = '{row[0]}'"
                cs = mdb_sel(cur, SQL)[0][0]
                st.progress(value=cs / ct, text=f":blue[{row[0]}] 已完成 :orange[{int((cs / ct) * 100)}%]")


conn = apsw.Connection("./DB/ETest_enc.db")
cur = conn.cursor()
cur.execute("PRAGMA cipher = 'aes256cbc'")
cur.execute("PRAGMA key = '7745'")
cur.execute("PRAGMA journal_mode = WAL")

st.logo("./Images/etest-logo.png", icon_image="./Images/exam2.png")

login_page = st.Page(login, title="登录", icon=":material/login:")
logout_page = st.Page(logout, title="登出", icon=":material/logout:")
changePassword_menu = st.Page(changePassword, title="修改密码", icon=":material/lock_reset:")

dashboard_page = st.Page("training.py", title="生成题库", icon=":material/construction:", default=True)
choseExam_page = st.Page("training.py", title="选择考试", icon=":material/data_check:", default=True)
trainingQues_page = st.Page("exam.py", title="题库练习", icon=":material/format_list_bulleted:")
execExam_page = st.Page("exam.py", title="开始考试", icon=":material/history_edu:")
search_page = st.Page("search.py", title="信息查询", icon=":material/search:")
dbsetup_page = st.Page("dbsetup.py", title="参数设置", icon=":material/settings:")
dbbasedata_page = st.Page("dbbasedata.py", title="数据录入", icon=":material/app_registration:")
todo_menu = st.Page(todo, title="待办事项", icon=":material/event_note:")
aboutInfo_menu = st.Page(aboutInfo, title="关于...", icon=":material/info:")
aboutLicense_menu = st.Page(aboutLicense, title="License", icon=":material/license:")
dboutput_menu = st.Page(dboutput, title="文件导出", icon=":material/output:")
dbfunc_menu = st.Page(dbfunc, title="题库功能", icon=":material/input:")
studyinfo_menu = st.Page(studyinfo, title="学习信息", icon=":material/import_contacts:")


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.rerun()

if st.session_state.logged_in:
    if st.session_state.examType == "exam":
        pg = st.navigation(
            {
                "功能": [choseExam_page, execExam_page],
                "账户": [changePassword_menu, logout_page],
                "关于": [aboutLicense_menu, aboutInfo_menu],

            }
        )
    elif st.session_state.examType == "training":
        if st.session_state.userType == "admin":
            pg = st.navigation(
                {
                    "功能": [dashboard_page, trainingQues_page, dbbasedata_page, dboutput_menu, dbfunc_menu, dbsetup_page],
                    "查询": [search_page],
                    "信息": [studyinfo_menu],
                    "账户": [changePassword_menu, logout_page],
                    "关于": [aboutLicense_menu, aboutInfo_menu],
                }
            )
        elif st.session_state.userType == "user":
            pg = st.navigation(
                {
                    "功能": [dashboard_page, trainingQues_page],
                    "信息": [studyinfo_menu],
                    "账户": [changePassword_menu, logout_page],
                    "关于": [aboutLicense_menu, aboutInfo_menu],
                }
            )
else:
    pg = st.navigation([login_page])

updatePyFileinfo()

pg.run()
