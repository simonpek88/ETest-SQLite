# coding UTF-8
import os
import re
import time

import apsw
import openpyxl
import pandas as pd
import pydeck as pdk
import streamlit as st
import streamlit_antd_components as sac
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor
from PIL import Image, ImageDraw, ImageFont
from st_keyup import st_keyup
from streamlit_extras.badges import badge
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_timeline import st_timeline
from xlsxwriter.workbook import Workbook

from commFunc import (deepseek_AI_GenerQues, getParam, mdb_del, mdb_ins,
                      mdb_modi, mdb_sel, qianfan_AI_GenerQues,
                      updateActionUser, updatePyFileinfo)

# cSpell:ignoreRegExp /[^\s]{16,}/
# cSpell:ignoreRegExp /\b[A-Z]{3,15}\b/g


def getUserCName(sUserName, sType="Digit"):
    SQL = ""
    if sType.capitalize() == "Digit":
        SQL = f"SELECT userCName, StationCN from users where userName = {sUserName}"
    elif sType.capitalize() == "Str":
        SQL = f"SELECT userCName, StationCN from users where userCName = '{sUserName}'"
    if SQL != "":
        rows = mdb_sel(cur, SQL)
        if rows:
            st.session_state.userCName = rows[0][0]
            st.session_state.StationCN = rows[0][1]
        else:
            st.session_state.userCName = "未找到"
            st.session_state.StationCN = "未找到"
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
        confirmPassword = st.text_input("请再次输入新密码", max_chars=8, placeholder="请与上一步输入的密码一致", type="password", autocomplete="new-password")
        buttonSubmit = st.button("确认修改")
    if oldPassword:
        SQL = "SELECT ID from users where userName = " + str(st.session_state.userName) + " and userPassword = '" + oldPassword + "'"
        if mdb_sel(cur, SQL):
            if newPassword and confirmPassword and newPassword != "":
                if newPassword == confirmPassword:
                    if buttonSubmit:
                        SQL = f"UPDATE users set userPassword = '{newPassword}' where userName = {st.session_state.userName}"
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
    updateActionUser(st.session_state.userName, "修改密码", st.session_state.loginTime)


@st.cache_data
def get_userName(searchUserName=""):
    searchUserNameInfo = ""
    if len(searchUserName) > 1:
        SQL = f"SELECT userName, userCName, StationCN from users where userName like '{searchUserName}%'"
        rows = mdb_sel(cur, SQL)
        for row in rows:
            searchUserNameInfo += f"用户编码: :red[{row[0]}] 姓名: :blue[{row[1]}] 站室: :orange[{row[2]}]\n\n"
    if searchUserNameInfo != "":
        searchUserNameInfo += "\n请在用户编码栏中填写查询出的完整编码"
    return searchUserNameInfo


@st.cache_data
def get_userCName(searchUserCName=""):
    searchUserCNameInfo = ""
    if len(searchUserCName) > 1:
        SQL = f"SELECT userName, userCName, StationCN from users where userCName like '{searchUserCName}%'"
        rows = mdb_sel(cur, SQL)
        for row in rows:
            searchUserCNameInfo += f"用户编码: :red[{row[0]}] 姓名: :blue[{row[1]}] 站室: :orange[{row[2]}]\n\n"
    else:
        searchUserCNameInfo = ":red[**请输入至少2个字**]"
    if searchUserCNameInfo != "" and "请输入至少2个字" not in searchUserCNameInfo:
        searchUserCNameInfo += "\n请在用户编码栏中填写查询出的完整编码"

    return searchUserCNameInfo


def login():
    #st.write("## :blue[专业技能考试系统 - 离线版]")
    st.markdown("<font face='微软雅黑' color=blue size=20><center>**专业技能考试系统 — 离线版**</center></font>", unsafe_allow_html=True)
    login = st.empty()
    with login.container(border=True):
        userName = st_keyup("请输入用户编码", placeholder="请输入用户编码, 必填项", max_chars=8)
        st.session_state.userCName = ""
        if userName:
            filtered = get_userName(userName)
            if filtered == "":
                getUserCName(userName, "Digit")
                st.caption(f"用户名: :blue[{st.session_state.userCName}] 站室: :orange[{st.session_state.StationCN}]")
        else:
            filtered = ""
        if st.session_state.userCName == "未找到" or filtered:
            st.caption(filtered)
        if userName == "" or st.session_state.userCName == "未找到":
            userCName = st_keyup("请输入用户姓名", placeholder="请输入用户姓名, 至少2个字, 用于查询, 非必填项", max_chars=8)
            st.session_state.userCName = ""
            if userCName:
                filtered = get_userCName(userCName)
                if filtered == "":
                    getUserCName(userCName, "Str")
                    st.caption(f"用户名: :blue[{st.session_state.userCName}] 站室: :orange[{st.session_state.StationCN}]")
            else:
                filtered = ""
            if st.session_state.userCName == "未找到" or filtered:
                promptArea = st.empty()
                with promptArea.container():
                    st.caption(filtered)
                if userName and filtered == "":
                    promptArea.empty()
        userPassword = st.text_input("请输入密码", max_chars=8, placeholder="用户初始密码为1234", type="password", autocomplete="off")
        examType = st.selectbox("请选择功能类型", ("练习", "考试"), index=0, help="各站管理员如需更改设置及查询请选择练习模式, 考试模式只能考试及修改密码")
        buttonLogin = st.button("登录")
    if buttonLogin:
        if userName != "" and userPassword != "":
            SQL = "SELECT userName, userCName, userType, StationCN from users where userName = " + str(userName) + " and userPassword = '" + userPassword + "'"
            result = mdb_sel(cur, SQL)
            if result:
                st.toast(f"用户: {result[0][0]} 姓名: {result[0][1]} 登录成功, 欢迎回来")
                login.empty()
                st.session_state.logged_in = True
                st.session_state.userName = result[0][0]
                st.session_state.userCName = result[0][1].replace(" ", "")
                st.session_state.userType = result[0][2]
                st.session_state.StationCN = result[0][3]
                st.session_state.examLimit = getParam("同场考试次数限制", st.session_state.StationCN)
                st.session_state.debug = bool(getParam("测试模式", st.session_state.StationCN))
                st.session_state.curQues = 0
                st.session_state.examChosen = False
                st.session_state.loginTime = int(time.time())
                SQL = f"UPDATE users set activeUser = 1, loginTime = {st.session_state.loginTime}, activeTime_session = 0, actionUser = '空闲' where userName = {st.session_state.userName}"
                mdb_modi(conn, cur, SQL)
                ClearTables()
                #cur.execute("VACUUM")
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
        else:
            st.warning("请输入用户编码和密码")


def logout():
    delOutdatedTable()
    SQL = f"UPDATE users set activeUser = 0, activeTime = activeTime + activeTime_session, activeTime_session = 0 where userName = {st.session_state.userName}"
    mdb_modi(conn, cur, SQL)
    cur.execute("VACUUM")

    for key in st.session_state.keys():
        del st.session_state[key]
    st.session_state.logged_in = False

    cur.close()
    conn.close()

    st.rerun()


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
    updateActionUser(st.session_state.userName, "浏览[关于]信息", st.session_state.loginTime)


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
    st.markdown(open("./LICENSE", "r", encoding="utf-8").read())
    updateActionUser(st.session_state.userName, "浏览License信息", st.session_state.loginTime)


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
            SQL = "SELECT userCName from users where userName = " + str(tmp)
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
        searchButton = st.button("导出为Excel文件", type="primary")
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
                    with open(outputFile, "rb") as file:
                        content = file.read()
                    file.close()
                    buttonDL = st.download_button("点击下载", content, file_name=f"考试成绩_{outputFile[outputFile.rfind('/') + 1:]}", icon=":material/download:", type="secondary")
                    st.success(f":green[[{searchExamName}]] :gray[考试成绩成功导出至程序目录下] :orange[{outputFile[2:]}]")
                    if buttonDL:
                        st.toast("文件已下载至你的默认目录")
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
    SQL = "DELETE from questionaff where chapterName <> '公共题库' and chapterName <> '错题集' and chapterName <> '关注题集' and chapterName not in (SELECT DISTINCT(chapterName) from questions)"
    mdb_del(conn, cur, SQL)
    SQL = "UPDATE users set userCName = replace(userCName, ' ', '') where userCName like '% %'"
    mdb_modi(conn, cur, SQL)
    for each in ["questions", "commquestions", "morepractise"]:
        mdb_modi(conn, cur, SQL=f"update {each} set Question = REPLACE(Question,'\n', '')")
    st.toast("站室题库/公共题库/错题集/章节信息库 记录清理完成")


def create_element(name):
    return OxmlElement(name)


def create_attribute(element, name, value):
    element.set(qn(name), value)


def add_page_number(run):
    fldChar1 = create_element('w:fldChar')
    create_attribute(fldChar1, 'w:fldCharType', 'begin')

    instrText = create_element('w:instrText')
    create_attribute(instrText, 'xml:space', 'preserve')
    instrText.text = "PAGE"

    fldChar2 = create_element('w:fldChar')
    create_attribute(fldChar2, 'w:fldCharType', 'end')

    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)


def questoWord():
    allType, stationCName, chapterNamePack, outChapterName = [], [], [], []
    st.subheader("题库导出", divider="blue")
    SQL = f"SELECT paramName, param from setup_{st.session_state.StationCN} where paramType = 'questype'"
    rows = mdb_sel(cur, SQL)
    for row in rows:
        allType.append(row[0])
    quesTable = st.selectbox("请选择功能类型", ("站室题库", "公共题库", "试卷", "错题集", "关注题集"), index=None)
    quesType = st.multiselect("题型", allType, default=allType)
    stationCN, headerExamName = "全站", ""
    if quesTable == "站室题库" or quesTable == "错题集" or quesTable == "关注题集":
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
            st.write("📢:red[试卷题库如果导出文件中不包含设置的题型, 请按如下提示操作, 其他类型题库没有此限制.]")
            step = sac.steps(
                items=[
                    sac.StepsItem(title='参数设置'),
                    sac.StepsItem(title='题型设置'),
                    sac.StepsItem(title='重新生成题库'),
                    sac.StepsItem(title='试卷导出'),
                ], index=None, return_index=True
            )
            if step is not None:
                st.image(f"./Images/help/OutputFile{step}.png", caption=f"操作步骤{step + 1}")
        else:
            st.warning("请先生成题库")
            quesTable = ""
    if stationCN != "全站" and quesTable == "站室题库":
        SQL = f"SELECT chapterName from questionaff where StationCN = '{stationCN}' and chapterName <> '公共题库' and chapterName <> '错题集' and chapterName <> '关注题集' order by ID"
        rows = mdb_sel(cur, SQL)
        for row in rows:
            chapterNamePack.append(row[0])
        outChapterName = st.multiselect("章节", chapterNamePack, default=chapterNamePack)
    sac.switch(label="复核模式", on_label="On", align='start', size='md', value=False, key="sac_recheck")
    if st.session_state.sac_recheck:
        sac.switch(label="附加答题解析", on_label="On", align='start', size='md', value=False, key="sac_Analysis")
    if quesTable and quesType:
        buttonSubmit = st.button("导出为Word文件", type="primary")
        if buttonSubmit:
            if quesTable == "站室题库":
                tablename = "questions"
            elif quesTable == "公共题库":
                tablename = "commquestions"
            elif quesTable == "试卷":
                tablename = st.session_state.examFinalTable
            elif quesTable == "错题集":
                tablename = "morepractise"
            elif quesTable == "关注题集":
                tablename = "favques"
            else:
                tablename = ""
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
                if stationCN == "全站" or quesTable == "试卷":
                    SQL = f"SELECT Question, qOption, qAnswer, qType, ID, SourceType, qAnalysis from {tablename} where qType = '{each}' order by ID"
                else:
                    if quesTable != "站室题库" and quesTable != "公共题库":
                        SQL = f"SELECT Question, qOption, qAnswer, qType, ID, SourceType, qAnalysis from {tablename} where qType = '{each}' and StationCN = '{stationCN}' order by ID"
                    elif quesTable == "站室题库":
                        if outChapterName:
                            SQL = f"SELECT Question, qOption, qAnswer, qType, ID, SourceType, qAnalysis from {tablename} where qType = '{each}' and StationCN = '{stationCN}' and (chapterName = "
                            for each5 in outChapterName:
                                SQL += f"'{each5}' or chapterName = "
                            SQL = SQL[:-18] + ") order by ID"
                        else:
                            SQL = f"SELECT Question, qOption, qAnswer, qType, ID, SourceType, qAnalysis from {tablename} where qType = '{each}' and StationCN = '{stationCN}' order by ID"
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
                        elif each == "单选题" or each == "多选题":
                            qa = row[1].replace("；", ";").split(";")
                            for each2 in qa:
                                tmp = tmp + f"{option[qa.index(each2)]}. {each2}{' ' * 8}"
                            textOption = pOption.add_run(tmp)
                            textOption.font.size = Pt(optionFS)
                        elif each == "判断题":
                            textOption = pOption.add_run(f"A. 正确{' ' * 15}B. 错误{' ' * 15}")
                            textOption.font.size = Pt(optionFS)
                        #textOption.font.name = "Microsoft YaHei"
                        #textOption.element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
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
                                else:
                                    fhQT = "未知"
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
                            if st.session_state.sac_Analysis and row[6] != "":
                                pAnalysis = quesDOC.add_paragraph()
                                if row[5] != "AI-LLM":
                                    textAnalysis = pAnalysis.add_run(f"人工解析: [{row[6].replace(':red', '').replace('[', '').replace(']', '').replace('**', '')}]")
                                else:
                                    textAnalysis = pAnalysis.add_run(f"请特别注意 A.I.解析: [{row[6].replace('**', '')}]")
                                textAnalysis.font.bold = True
                                textAnalysis.font.size = Pt(answerFS)
                                textAnalysis.font.color.rgb = RGBColor(79, 66, 181)
                                #textAnalysis.font.underline = True
                                #textAnalysis.font.italic = True
                        i += 1
            add_page_number(quesDOC.sections[0].footer.paragraphs[0].add_run())
            quesDOC.sections[0].footer.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            header = quesDOC.sections[0].header.paragraphs[0]
            header.text = f"{stationCN}\t\t{quesTable}"
            header.style = quesDOC.styles["Header"]
            if headerExamName != "":
                outputFile = f"./QuesDoc/{stationCN}-{headerExamName}-{quesTable}_{time.strftime('%Y%m%d%H%M%S', time.localtime(int(time.time())))}.docx"
            else:
                outputFile = f"./QuesDoc/{stationCN}-{quesTable}_{time.strftime('%Y%m%d%H%M%S', time.localtime(int(time.time())))}.docx"
            if os.path.exists(outputFile):
                os.remove(outputFile)
            quesDOC.save(outputFile)
            if os.path.exists(outputFile):
                if os.path.exists(outputFile):
                    with open(outputFile, "rb") as file:
                        content = file.read()
                    file.close()
                    buttonDL = st.download_button("点击下载", content, file_name=outputFile[outputFile.rfind("/") + 1:], icon=":material/download:", type="secondary")
                    st.success(f":green[[{quesTable}]] :gray[题库成功导出至程序目录下] :orange[{outputFile[2:]}]")
                    if buttonDL:
                        st.toast("文件已下载至你的默认目录")
            else:
                st.warning(f":red[[{quesTable}]] 题库导出失败")


def dboutput():
    bc = sac.segmented(
        items=[
            sac.SegmentedItem(label="题库导出(Word格式)", icon="database-down"),
            #sac.SegmentedItem(label="试卷导出(DF格式)", icon="journal-arrow-down"),
            sac.SegmentedItem(label="考试成绩导出(Excel格式)", icon="layout-text-sidebar-reverse"),
        ], color="green", align="center"
    )
    if bc == "题库导出(Word格式)":
        questoWord()
    elif bc == "试卷导出(DF格式)":
        resultExcel()
    elif bc == "考试成绩导出(Excel格式)":
        examResulttoExcel()
    if bc is not None:
        updateActionUser(st.session_state.userName, bc, st.session_state.loginTime)


def actDelExamTable():
    for each in st.session_state.keys():
        if each.startswith("delExamTable_"):
            if st.session_state[each]:
                each = each.replace("delExamTable_", "")
                mdb_del(conn, cur, SQL=f"DROP TABLE IF EXISTS {each}")
                st.info(f"{each} 试卷删除成功")


def delExamTable():
    flagExistTable = False
    SQL = "SELECT name from sqlite_master where type = 'table' and name like 'exam_%'"
    tempTable = mdb_sel(cur, SQL)
    if tempTable:
        st.subheader("删除试卷", divider="red")
        for row in tempTable:
            if row[0].count("_") == 3 or row[0].count("_") == 4:
                st.checkbox(f"{row[0]}", key=f"delExamTable_{row[0]}")
                flagExistTable = True
    if flagExistTable:
        st.button("确认删除", on_click=actDelExamTable)
    else:
        st.info("暂无试卷")


def dbinputSubmit(tarTable, orgTable):
    tmpTable, SQL, maxcol = "", "", 0
    if tarTable == "站室题库":
        tablename = "questions"
        SQL = f"INSERT INTO {tablename}(Question, qOption, qAnswer, qType, qAnalysis, StationCN, chapterName) VALUES (?, ?, ?, ?, ?, ?, ?)"
        maxcol = 7
    elif tarTable == "公共题库":
        tablename = "commquestions"
        SQL = f"INSERT INTO {tablename}(Question, qOption, qAnswer, qType, qAnalysis) VALUES (?, ?, ?, ?, ?)"
        maxcol = 5
    if SQL != "":
        st.spinner(f"正在向 [{tarTable}] 导入题库...")
        SQL2 = f"SELECT Max(ID) from {tablename}"
        maxid = mdb_sel(cur, SQL2)[0][0]
        if maxid is None:
            maxid = 0
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
        SQL = f"UPDATE {tablename} set qOption = replace(qOption, '；', ';'), qAnswer = replace(qAnswer, '；', ';') where (qOption like '%；%' or qAnswer like '%；%') and (qType = '单选题' or qType = '多选题' or qType = '填空题')"
        mdb_modi(conn, cur, SQL)
        SQL = f"UPDATE {tablename} set qType = '单选题' where qType = '选择题' and ID > {maxid}"
        mdb_modi(conn, cur, SQL)
        SQL = f"SELECT ID, qOption, qAnswer, qType, Question from {tablename} where ID > {maxid} and (qType = '单选题' or qType = '多选题' or qType = '判断题')"
        rows = mdb_sel(cur, SQL)
        for row in rows:
            SQL = ""
            if row[3] == "单选题" or row[3] == "多选题":
                for each in row[2].split(";"):
                    if int(each) < 0 or int(each) >= len(row[1].split(";")):
                        SQL = f"DELETE from {tablename} where ID = {row[0]}"
            elif row[3] == "判断题":
                if int(row[2]) < 0 or int(row[2]) > 1:
                    SQL = f"DELETE from {tablename} where ID = {row[0]}"
            if SQL != "":
                mdb_del(conn, cur, SQL)
                st.warning(f"试题: [{row[4]}] 题型: [{row[3]}] 选项: [{row[1]}] 答案: [{row[2]}] 因为选项及答案序号不相符, 没有导入")
        SQL = "INSERT INTO questionaff(chapterName, StationCN, chapterRatio, examChapterRatio) SELECT DISTINCT chapterName, StationCN, 5, 5 FROM questions"
        mdb_ins(conn, cur, SQL)
        ClearTables()
        st.success(f":green[[{tmpTable[:-2]}] 向 [{tarTable}]] :gray[导入成功]")


def dbinput():
    inputOption = []
    targetTable = st.radio("导入至:", ("站室题库", "公共题库"), index=None, horizontal=True)
    inputType = st.radio("文件来源:", ("服务器中文件", "上传文件"), index=0, horizontal=True)
    if targetTable:
        if inputType == "服务器中文件":
            for root, dirs, files in os.walk("./InputQues"):
                for file in files:
                    if os.path.splitext(file)[1].lower() == '.xlsx' and f"{st.session_state.StationCN}_{targetTable}" in os.path.splitext(file)[0]:
                        inputOption.append(os.path.splitext(file)[0])
            if inputOption:
                orgTable = st.multiselect("请选择导入文件", inputOption, default=None)
                if orgTable:
                    st.button("导入", on_click=dbinputSubmit, args=(targetTable, orgTable))
                else:
                    st.warning("请选择要导入的文件")
            else:
                st.warning("没有可导入的本站文件")
        elif inputType == "上传文件":
            uploaded_file = st.file_uploader("**请选择Excel文件, 系统会自动改名为: :red[站室名称_站室题库/公共题库_用户上传_上传日期]**", type=["xlsx"])
            if uploaded_file is not None:
                bytes_data = uploaded_file.getvalue()
                outFile = f"./InputQues/{st.session_state.StationCN}_{targetTable}_用户上传_{time.strftime('%Y%m%d%H%M%S', time.localtime(int(time.time())))}.xlsx"
                if os.path.exists(outFile):
                    os.remove(outFile)
                with open(outFile, 'wb') as output_file:
                    output_file.write(bytes_data)
                if os.path.exists(outFile):
                    st.success("文件上传成功, 请选择文件来源为: :red[**服务器中文件**]并重新导入")
    else:
        st.write("请选择要导入的题库")


def dbfunc():
    bc = sac.segmented(
        items=[
            sac.SegmentedItem(label="A.I.出题", icon="robot"),
            sac.SegmentedItem(label="题库导入", icon="database-up"),
            #sac.SegmentedItem(label="Word文件导入", icon="text-wrap", disabled=st.session_state.debug ^ True),
            sac.SegmentedItem(label="删除试卷", icon="trash3"),
            sac.SegmentedItem(label="删除静态题库", icon="trash3"),
            sac.SegmentedItem(label="删除用户上传文件", icon="trash3"),
            sac.SegmentedItem(label="错题集重置", icon="journal-x"),
            sac.SegmentedItem(label="重置题库ID", icon="bootstrap-reboot", disabled=st.session_state.debug ^ True),
        ], align="start", color="red"
    )
    if bc == "A.I.出题":
        AIGenerQues()
    elif bc == "题库导入":
        dbinput()
    elif bc == "Word文件导入":
        inputWord()
    elif bc == "错题集重置":
        ClearMP()
    elif bc == "删除试卷":
        delExamTable()
    elif bc == "删除静态题库":
        delStaticExamTable()
    elif bc == "删除用户上传文件":
        delUserUploadFiles()
    elif bc == "重置题库ID":
        buttonReset = st.button("重置题库ID", type="primary")
        if buttonReset:
            st.button("确认重置", type="secondary", on_click=resetTableID)
    if bc is not None:
        updateActionUser(st.session_state.userName, bc, st.session_state.loginTime)


def delUserUploadFiles():
    flagDelUserFiles = False
    for root, dirs, files in os.walk("./InputQues"):
        for file in files:
            if os.path.splitext(file)[1].lower() == '.xlsx' and "_用户上传_" in os.path.splitext(file)[0]:
                st.checkbox(os.path.splitext(file)[0], value=False, key=f"delUserFiles_{os.path.splitext(file)[0]}")
                flagDelUserFiles = True
    if flagDelUserFiles:
        buttonDel = st.button("删除", type="primary")
        if buttonDel:
            st.button("确认删除", type="secondary", on_click=actionDelUserUploadFiles)
    else:
        st.warning("没有用户上传文件")


def actionDelUserUploadFiles():
    for key in st.session_state.keys():
        if key.startswith("delUserFiles_"):
            if st.session_state[key]:
                os.remove(f"./InputQues/{key.replace('delUserFiles_', '')}.xlsx")
            del st.session_state[key]
    st.success("所选文件已经删除")


def resetActiveUser():
    SQL = f"UPDATE users set activeUser = 0 where userName <> {st.session_state.userName}"
    mdb_modi(conn, cur, SQL)
    st.success("已重置所有用户状态")


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
    for tablename in ["questions", "commquestions", "morepractise", "favques", "examidd", "examresult", "questionaff", "studyinfo", "users", "setup_默认", f"setup_{st.session_state.StationCN}"]:
        SQL = f"SELECT ID from {tablename} order by ID"
        rows = mdb_sel(cur, SQL)
        for i, row in enumerate(rows):
            SQL = f"UPDATE {tablename} set ID = {i + 1} where ID = {row[0]}"
            mdb_modi(conn, cur, SQL)
            if tablename == "questions" or tablename == "commquestions":
                SQL = f"UPDATE studyinfo set cid = {i + 1} where cid = {row[0]} and questable = '{tablename}'"
                mdb_modi(conn, cur, SQL)
        #st.toast(f"重置 {tablename} 表ID完毕")
    st.success("题库ID重置成功")


def AIGenerQues():
    quesPack, chars, chapterPack, dynaQuesType, generQuesCount = [], ["A", "B", "C", "D", "E", "F", "G", "H"], [], ["单选题", "多选题", "判断题", "填空题"], 0
    AIModelNamePack, quesTypePack, generQuesCountPack, gqc = [], [], [], 0
    StationCNPack, chosenStationCN = [], st.session_state.StationCN
    temp = f"{st.session_state.StationCN}-站室题库现有: "
    for each in dynaQuesType:
        SQL = f"SELECT Count(ID) from questions where qType = '{each}' and StationCN = '{st.session_state.StationCN}'"
        qCount = mdb_sel(cur, SQL)[0][0]
        temp = temp + ":red[" + each + "]: " + str(qCount) + "道 "
    temp = temp + "\n\n公共题库现有: "
    for each in dynaQuesType:
        SQL = f"SELECT Count(ID) from commquestions where qType = '{each}'"
        qCount = mdb_sel(cur, SQL)[0][0]
        temp = temp + ":red[" + each + "]: " + str(qCount) + "道 "
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
    AIModelNamePack = st.multiselect(
        "可选LLM大模型",
        ["DeepSeek", "文心千帆"],
        ["DeepSeek", "文心千帆"],
    )
    quesTypePack = st.multiselect(
        "请选择要生成的题型",
        dynaQuesType,
        dynaQuesType,
    )
    quesCount = st.number_input("请输入要生成的题目数量", min_value=1, max_value=10, value=5, step=1)
    if table is not None and quesRefer != "" and AIModelNamePack != [] and quesTypePack != []:
        buttonGener = st.button("生成试题")
        if buttonGener:
            if chapter is None and textChapter != "":
                SQL = f"SELECT ID from questionaff where chapterName = '{textChapter}' and StationCN = '{chosenStationCN}'"
                if not mdb_sel(cur, SQL):
                    SQL = f"INSERT INTO questionaff(chapterName, StationCN, chapterRatio, examChapterRatio) VALUES ('{textChapter}', '{chosenStationCN}', 5, 5)"
                    mdb_ins(conn, cur, SQL)
                    st.toast(f"新的章节: :red[{textChapter}]添加完毕")
                chapter = textChapter
            if chapter is not None and table == "站室题库" or table == "公共题库":
                if st.session_state.debug:
                    os.system("cls")
                generQuesCount, displayQues, generQuesCountPack = 0, "", []
                infoArea = st.empty()
                for quesType in quesTypePack:
                    gqc = 0
                    for AIModelName in AIModelNamePack:
                        with infoArea.container(border=True):
                            st.info(f"正在使用 :red[{AIModelName}大模型] 进行:blue[{quesType}] 试题生成, 请稍等...")
                        if AIModelName == "文心千帆":
                            ques = qianfan_AI_GenerQues(quesRefer, quesType, quesCount, "ERNIE-Speed-8K")
                        elif AIModelName == "DeepSeek":
                            ques = deepseek_AI_GenerQues(quesRefer, quesType, quesCount)
                        else:
                            ques = ""
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
                                    if qOption.count(";") == 0 and (quesType == "单选题" or quesType == "多选题"):
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
                                            gqc += 1
                                            displayQues = displayQues + f":blue[**第{generQuesCount}题:**]\n\n:red[题型: ]{quesType}\n\n:red[题目: ]{quesHeader}\n\n:red[选项: ]\n{displayOption}\n\n:red[答案: ]{displayAnswer}\n\n:red[解析: ]{qAnalysis}\n\n{'-' * 40}\n\n"
                                    elif table == "站室题库":
                                        SQL = f"SELECT ID from questions where Question = '{quesHeader}' and qType = '{quesType}' and StationCN = '{chosenStationCN}' and chapterName = '{chapter}'"
                                        if not mdb_sel(cur, SQL):
                                            SQL = f"INSERT INTO questions(Question, qOption, qAnswer, qType, qAnalysis, StationCN, chapterName, SourceType) VALUES('{quesHeader}', '{qOption}', '{qAnswer}', '{quesType}', '{qAnalysis}', '{chosenStationCN}', '{chapter}', 'AI-LLM')"
                                            mdb_ins(conn, cur, SQL)
                                            generQuesCount += 1
                                            gqc += 1
                                            displayQues = displayQues + f":blue[**第{generQuesCount}题:**]\n\n:red[题型: ]{quesType}\n\n:red[题目: ]{quesHeader}\n\n:red[选项: ]\n{displayOption}\n\n:red[答案: ]{displayAnswer}\n\n:red[解析: ]{qAnalysis}\n\n{'-' * 40}\n\n"
                    generQuesCountPack.append(gqc)
                infoArea.empty()
                if generQuesCount > 0:
                    tempInfo = f"试题生成完毕, 总计生成试题{generQuesCount}道, 其中"
                    for index, value in enumerate(quesTypePack):
                        tempInfo = tempInfo + f"{value}: {generQuesCountPack[index]}道, "
                    st.success(tempInfo[:-2])
                    st.subheader("具体如下:", divider="green")
                    st.markdown(displayQues)
                else:
                    st.info("A.I.未生成到任何试题, 请检查参考资料是否正确或是生成的试题已经在题库中")
            else:
                st.warning("站室题库请选择章节")
    else:
        st.info("请设置各选项和添加参考资料")


def ClearMP():
    buttonSubmit = st.button("清空错题集所有记录", type="primary")
    if buttonSubmit:
        bcArea = st.empty()
        with bcArea.container():
            st.button("确认清空", type="secondary", on_click=ClearMPAction, args=(bcArea,))


def ClearMPAction(bcArea):
    mdb_del(conn, cur, SQL="DELETE from morepractise")
    bcArea.empty()
    st.success("错题集已重置")


def studyinfo():
    study = sac.segmented(
        items=[
            sac.SegmentedItem(label="学习进度", icon="grid-3x2-gap"),
            sac.SegmentedItem(label="错题集", icon="list-stars"),
            sac.SegmentedItem(label="章节时间线", icon="clock-history"),
            sac.SegmentedItem(label="学习记录重置", icon="bootstrap-reboot"),
        ], align="center", color="red"
    )
    if study == "学习进度":
        studyinfoDetail()
    elif study == "错题集":
        displayErrorQues()
    elif study == "章节时间线":
        generTimeline()
    elif study == "学习记录重置":
        studyReset()
    if study is not None:
        updateActionUser(st.session_state.userName, f"查看信息-{study}", st.session_state.loginTime)


def userRanking():
    study = sac.segmented(
        items=[
            sac.SegmentedItem(label="榜单", icon="bookmark-star"),
            sac.SegmentedItem(label="证书", icon="patch-check"),
            sac.SegmentedItem(label="荣誉榜", icon="mortarboard"),
        ], align="center", color="red"
    )
    if study == "榜单":
        displayUserRanking()
    elif study == "证书":
        displayCertificate()
    elif study == "荣誉榜":
        displayMedals()
    if study is not None:
        updateActionUser(st.session_state.userName, f"证书及榜单-{study}", st.session_state.loginTime)


def displayUserRanking():
    xData, yData, boardInfo = [], [], ""
    boardType = st.radio(" ", options=["个人榜", "站室榜"], index=0, horizontal=True, label_visibility="collapsed")
    if boardType == "个人榜":
        SQL = "SELECT userCName, StationCN, userRanking from users order by userRanking DESC limit 0, 5"
    elif boardType == "站室榜":
        SQL = "SELECT StationCN, ID, sum(userRanking) as Count from users GROUP BY StationCN order by Count DESC"
    else:
        SQL = ""
    rows = mdb_sel(cur, SQL)
    for index, row in enumerate(rows):
        xData.append(row[0])
        yData.append(row[2])
        if boardType == "个人榜":
            boardInfo = boardInfo + f"第 {index + 1} 名: {row[0]} 站室: {row[1]} 刷题数: {row[2]}\n\n"
        elif boardType == "站室榜":
            boardInfo = boardInfo + f"第 {index + 1} 名: {row[0]} 刷题数: {row[2]}\n\n"
        else:
            boardInfo = ""
    itemArea = st.empty()
    with itemArea.container(border=True):
        st.bar_chart(data=pd.DataFrame({"用户": xData, "试题数": yData}), x="用户", y="试题数", color=(155, 17, 30))
    if boardType == "站室榜":
        data = []
        for row in rows:
            SQL = f"SELECT lat, lng, Station from stations where Station = '{row[0]}'"
            tmpTable = mdb_sel(cur, SQL)
            for i in range(row[2]):
                data.append([round(tmpTable[0][0] / 100, 2), round(tmpTable[0][1] / 100, 2)])
        chart_data = pd.DataFrame(data, columns=["lat", "lng"],)
        st.pydeck_chart(
            pdk.Deck(
                map_style="road",
                initial_view_state=pdk.ViewState(
                    #latitude=39.12,
                    #longitude=117.34,
                    latitude=data[0][0],
                    longitude=data[0][1],
                    zoom=10,
                    pitch=50,
                ),
                layers=[
                    pdk.Layer(
                        "HexagonLayer",
                        data=chart_data,
                        get_position="[lng, lat]",
                        radius=200,
                        elevation_scale=4,
                        elevation_range=[0, 3000],
                        pickable=True,
                        extruded=True,
                        coverage=1,
                    ),
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=chart_data,
                        get_position="[lng, lat]",
                        get_color="[37, 150, 209, 160]",
                        get_radius=200,
                        coverage=1,
                    ),
                ],
            )
        )
    st.subheader(boardInfo)


def generTimeline():
    timelineData, i = [], 1
    SQL = f"SELECT chapterName from questionaff where StationCN = '{st.session_state.StationCN}' and chapterName <> '错题集' order by ID"
    rows = mdb_sel(cur, SQL)
    for row in rows:
        if row[0] != "公共题库":
            SQL = f"SELECT Count(ID) from questions where chapterName = '{row[0]}'"
            quesCount = mdb_sel(cur, SQL)[0][0]
        else:
            SQL = "SELECT Count(ID) from commquestions"
            quesCount = mdb_sel(cur, SQL)[0][0]
        SQL = f"SELECT startTime from studyinfo where userName = '{st.session_state.userName}' and chapterName = '{row[0]}' order by startTime"
        rows2 = mdb_sel(cur, SQL)
        if rows2:
            trainingDate = time.strftime("%Y-%m-%d", time.localtime(rows2[0][0]))
            trainingDate2 = time.strftime("%Y-%m-%d", time.localtime(rows2[-1][0]))
            if len(rows2) == quesCount:
                temp = {"id": i, "content": row[0], "start": trainingDate, "end": trainingDate2}
            else:
                temp = {"id": i, "content": row[0], "start": trainingDate, "type": "point"}
            timelineData.append(temp)
            i += 1
    #st.write(timelineData)
    if timelineData:
        timeline = st_timeline(timelineData, groups=[], options={}, height="300px")
        if timeline is not None:
            if "end" in timeline:
                st.write(f"章节: :green[{timeline['content']}] 练习开始时间: :blue[{timeline['start']}] 完成时间: :orange[{timeline['end']}]")
            else:
                st.write(f"章节: :green[{timeline['content']}] 练习开始时间: :blue[{timeline['start']}]")
    else:
        st.write(":red[暂无学习记录]")


def displayCertificate():
    flagGener, flagInfo = False, True
    SQL = f"SELECT examName from examidd where StationCN = '{st.session_state.StationCN}' and examName <> '练习题库' order by ID"
    rows = mdb_sel(cur, SQL)
    for row in rows:
        SQL = f"SELECT userCName, examScore, examDate, CertificateNum, ID from examresult where userName = '{st.session_state.userName}' and examName = '{row[0]}' and examPass = 1 order by examScore DESC limit 0, 1"
        rows2 = mdb_sel(cur, SQL)
        if rows2:
            flagGener = True
            if flagGener and flagInfo:
                st.write(":orange[如需打印, 请打开 :green[程序目录下Image/Certificate] 或者点击下载证书]")
                flagInfo = False
            examDetail = rows2[0]
            with st.expander(label=f"{row[0]}", expanded=False):
                examDateDetail = time.strftime("%Y%m%d%H%M%S", time.localtime(examDetail[2]))
                if examDetail[3] == 0:
                    SQL = "SELECT Max(CertificateNum) from examresult"
                    maxCertNum = mdb_sel(cur, SQL)[0][0] + 1
                else:
                    maxCertNum = examDetail[3]
                certFile = f"./Images/Certificate/Cert-Num.{str(maxCertNum).rjust(5, '0')}-{st.session_state.userName}-{examDetail[0]}-{row[0]}_{examDateDetail}.png"
                if not os.path.exists(certFile):
                    if examDetail[1] >= 100:
                        medal = "./Images/gold-award.png"
                    elif examDetail[1] >= 90:
                        medal = "./Images/silver-award.png"
                    else:
                        medal = "./Images/bronze-award.png"
                    examDate = time.strftime("%Y-%m-%d", time.localtime(examDetail[2]))
                    generCertificate(certFile, medal, st.session_state.userCName, row[0], examDate, maxCertNum)
                if os.path.exists(certFile):
                    SQL = f"UPDATE examresult set CertificateNum = {maxCertNum} where ID = {examDetail[4]}"
                    mdb_modi(conn, cur, SQL)
                    st.image(certFile)
                with open(certFile, "rb") as file:
                    st.download_button(
                        label="下载证书",
                        data=file,
                        file_name=certFile[certFile.rfind("/") + 1:].replace("Cert", "证书"),
                        mime="image/png",
                        icon=":material/download:"
                    )
                file.close()
    if not flagGener:
        st.info("您没有通过任何考试, 无法生成证书")


def generCertificate(certFile, medal, userCName, examName, examDate, maxCertNum):
    namePosX = [866, 821, 796, 760, 726, 696]
    if len(userCName) == 2:
        userCName = userCName[0] + " " + userCName[-1]
    font = ImageFont.truetype("./Fonts/msyhbd.ttf", 70)
    font2 = ImageFont.truetype("./Fonts/msyhbd.ttf", 30)
    font3 = ImageFont.truetype("./Fonts/msyhbd.ttf", 36)
    font4 = ImageFont.truetype("./Fonts/renaissance.ttf", 46)
    backpng = './Images/Certificate-bg.png'
    im = Image.open(backpng)
    imMedal = Image.open(medal)
    im.paste(imMedal, (784, 860), imMedal)
    imMedal.close()
    dr = ImageDraw.Draw(im)
    dr.text((160, 132), f"No.{str(maxCertNum).rjust(5, '0')}", font=font4, fill='grey')
    if len(userCName.replace(" ", "")) - 1 >= 0 and len(userCName.replace(" ", "")) - 1 <= 5:
        dr.text((namePosX[len(userCName.replace(" ", "")) - 1], 460), userCName, font=font, fill='grey')
    else:
        dr.text((460, 460), userCName, font=font, fill='grey')
    dr.text((900 - int(len(examName) * 15), 710), examName, font=font2, fill='grey')
    dr.text((410, 940), examDate, font=font3, fill='grey')
    im.save(certFile)
    im.close()


def displayMedals():
    SQL = "SELECT examName from examidd where examName <> '练习题库' order by ID"
    rows = mdb_sel(cur, SQL)
    for row in rows:
        with st.expander(label=f"{row[0]}", expanded=False):
            mcol1, mcol2, mcol3, mcol4, mcol5, mcol6 = st.columns(6)
            SQL = f"SELECT userCName, examScore, examDate from examresult where examName = '{row[0]}' and examPass = 1 order by examScore DESC limit 0, 3"
            rows2 = mdb_sel(cur, SQL)
            if rows2:
                if len(rows2) > 0:
                    examDate = time.strftime("%Y-%m-%d", time.localtime(rows2[0][2]))
                    mcol3.image("./Images/gold-medal.png")
                    mcol4.write(f"##### :red[{rows2[0][0]}]")
                    mcol4.write(f"成绩: {rows2[0][1]}分")
                    mcol4.write(f"{examDate}")
                if len(rows2) > 1:
                    examDate = time.strftime("%Y-%m-%d", time.localtime(rows2[1][2]))
                    mcol1.image("./Images/silver-medal.png")
                    mcol2.write(f"##### :grey[{rows2[1][0]}]")
                    mcol2.write(f"成绩: {rows2[1][1]}分")
                    mcol2.write(f"{examDate}")
                if len(rows2) > 2:
                    examDate = time.strftime("%Y-%m-%d", time.localtime(rows2[2][2]))
                    mcol5.image("./Images/bronze-medal.png")
                    mcol6.write(f"##### :orange[{rows2[2][0]}]")
                    mcol6.write(f"成绩: {rows2[2][1]}分")
                    mcol6.write(f"{examDate}")


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
    scol1, scol2, scol3 = st.columns(3)
    SQL = f"SELECT Count(ID) from questionaff where StationCN = '{st.session_state.StationCN}' and chapterName <> '错题集' and chapterName <> '关注题集'"
    rows = mdb_sel(cur, SQL)
    scol1.metric(label="章节总计", value=rows[0][0], help="包含公共题库, 不含错题集")
    SQL = f"SELECT Count(ID) from questions where StationCN = '{st.session_state.StationCN}'"
    ct1 = mdb_sel(cur, SQL)[0][0]
    SQL = "SELECT Count(ID) from commquestions"
    ct2 = mdb_sel(cur, SQL)[0][0]
    ct = ct1 + ct2
    scol2.metric(label="试题总计", value=ct, help="包含公共题库, 不含错题集")
    SQL = f"SELECT Count(ID) from studyinfo where userName = {st.session_state.userName}"
    rows = mdb_sel(cur, SQL)
    scol3.metric(label="已学习试题", value=f"{rows[0][0]} - {int(rows[0][0] / ct * 100)}%", help=f"总完成率: {int(rows[0][0] / ct * 100)}%")
    style_metric_cards(border_left_color="#8581d9")
    helpInfo = ["点击页面⤴️右上角红圈处图标, 并选择Settings", "点击Choose app theme, colors and fonts", "选择Light或是Custom Theme"]
    st.write("###### :violet[如果上面3个标签无显示内容, 请按照以下步骤改用浅色主题]")
    step = sac.steps(
        items=[
            sac.StepsItem(title='页面设置'),
            sac.StepsItem(title='主题设置'),
            sac.StepsItem(title='选择主题'),
        ], index=None, return_index=True
    )
    if step is not None:
        st.image(f"./Images/help/themesetup{step}.png", caption=f"{helpInfo[step]}")
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


def userStatus():
    st.subheader(":violet[在线用户状态]", divider="rainbow")
    bc = sac.segmented(
        items=[
            sac.SegmentedItem(label="在线用户状态", icon="people"),
            sac.SegmentedItem(label="重置所有用户状态", icon="person-slash"),
        ], align="start", color="red"
    )
    if bc == "在线用户状态":
        actionUserStatus()
    elif bc == "重置所有用户状态":
        buttonReset = st.button("重置所有用户状态", type="primary")
        if buttonReset:
            st.button("确认重置", type="secondary", on_click=resetActiveUser)
    if bc is not None:
        updateActionUser(st.session_state.userName, bc, st.session_state.loginTime)


def actionUserStatus():
    SQL = "SELECT userCName, userType, StationCN, actionUser, loginTime, activeTime_session, activeTime from users where activeUser = 1 order by ID"
    rows = mdb_sel(cur, SQL)
    df = pd.DataFrame(rows, dtype=str)
    df.columns = ["姓名", "类型", "站室", "用户操作", "登录时间", "活动时间", "累计活动时间"]
    for index, value in enumerate(rows):
        df.loc[index, "登录时间"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(df["登录时间"][index])))
        activeTime = int(df.loc[index, "活动时间"])
        hTime = int(activeTime / 3600)
        mTime = int((activeTime % 3600) / 60)
        if mTime < 10:
            mTime = "0" + str(mTime)
        sTime = int(activeTime % 60)
        if sTime < 10:
            sTime = "0" + str(sTime)
        df.loc[index, "活动时间"] = f"{hTime}:{mTime}:{sTime}"
        activeTime = int(df.loc[index, "累计活动时间"])
        hTime = int(activeTime / 3600)
        mTime = int((activeTime % 3600) / 60)
        if mTime < 10:
            mTime = "0" + str(mTime)
        sTime = int(activeTime % 60)
        if sTime < 10:
            sTime = "0" + str(sTime)
        df.loc[index, "累计活动时间"] = f"{hTime}:{mTime}:{sTime}"
    st.dataframe(df, use_container_width=True)


@st.fragment
def actionQuesModify(row):
    option = []
    qQuestion, qOption, qAnswer, qType, qAnalysis = row
    st.session_state.qModifyQues_qType = qType
    st.write(f"**此题为{qType}**")
    st.text_area(":blue[**题目**]", value=qQuestion, key="qModifyQues_Question")
    if qType == "单选题":
        qOption2 = qOption.split(";")
        st.session_state.qModifyQues_optionCount = len(qOption2)
        for index, value in enumerate(qOption2):
            st.text_input(f":orange[**选项{chr(65 + index)}**]", value=value, key=f"qModifyQues_{index}")
            option.append(chr(65 + index))
        st.radio(":red[**答案**]", options=option, index=int(qAnswer), key="qModifyQues_Answer", horizontal=True)
    elif qType == "多选题":
        qOption2 = qOption.split(";")
        qAnswer2 = qAnswer.split(";")
        st.session_state.qModifyQues_optionCount = len(qOption2)
        for index, value in enumerate(qOption2):
            st.text_input(f":orange[**选项{chr(65 + index)}**]", value=value, key=f"qModifyQues_{index}")
            if str(index) in qAnswer2:
                st.checkbox(":blue[**选择**]", value=True, key=f"qModifyQues_Answer_{index}")
            else:
                st.checkbox(":blue[**选择**]", value=False, key=f"qModifyQues_Answer_{index}")
    elif qType == "判断题":
        st.radio(":red[**答案**]", ["A. 正确", "B. 错误"], key="qModifyQues_Answer", index=int(qAnswer) ^ 1, horizontal=True)
    elif qType == "填空题":
        qAnswer2 = qAnswer.split(";")
        st.session_state.qModifyQues_optionCount = len(qAnswer2)
        for index, value in enumerate(qAnswer2):
            st.text_input(":orange[**答案**]", value=value, key=f"qModifyQues_Answer_{index}")
    st.text_area(":green[**答案解析**]", value=qAnalysis, key="qModifyQues_Answer_Analysis")


def quesModify():
    col1, col2 = st.columns(2)
    chosenTable = col1.selectbox(":red[选择题库]", ["站室题库", "公共题库"], index=None)
    quesID = col2.number_input(":blue[题目ID]", min_value=0, step=1)
    if chosenTable is not None and quesID > 0:
        if chosenTable == "站室题库":
            tablename = "questions"
        elif chosenTable == "公共题库":
            tablename = "commquestions"
        else:
            tablename = ""
        col3, col4, col5 = st.columns(3)
        buttonDisplayQues = col3.button("显示试题", icon=":material/dvr:")
        if buttonDisplayQues:
            SQL = f"SELECT Question, qOption, qAnswer, qType, qAnalysis from {tablename} where ID = {quesID}"
            rows = mdb_sel(cur, SQL)
            if rows:
                col4.button("更新试题", on_click=actionQM, args=(quesID, tablename, rows[0]), icon=":material/published_with_changes:")
                col5.button("删除试题", on_click=actionDelQM, args=(quesID, tablename, rows[0]), icon=":material/delete:")
                actionQuesModify(rows[0])
            else:
                st.error("未找到该题目, 请检查题库名称及题目ID是否正确")
    else:
        st.error("请选择题库")


def actionQM(quesID, tablename, mRow):
    mOption, mAnswer, Option = "", "", ["A", "B", "C", "D", "E", "F", "G", "H"]
    mQues = st.session_state.qModifyQues_Question
    mAnalysis = st.session_state.qModifyQues_Answer_Analysis
    if st.session_state.qModifyQues_qType == "单选题" or st.session_state.qModifyQues_qType == "多选题":
        for i in range(st.session_state.qModifyQues_optionCount):
            mOption = mOption + st.session_state[f"qModifyQues_{i}"] + ";"
        if mOption.endswith(";"):
            mOption = mOption[:-1]
        if st.session_state.qModifyQues_qType == "单选题":
            for index, value in enumerate(Option):
                if value == st.session_state.qModifyQues_Answer:
                    mAnswer = index
                    break
        else:
            for i in range(st.session_state.qModifyQues_optionCount):
                if st.session_state[f"qModifyQues_Answer_{i}"]:
                    mAnswer = mAnswer + str(i) + ";"
            if mAnswer.endswith(";"):
                mAnswer = mAnswer[:-1]
    elif st.session_state.qModifyQues_qType == "判断题":
        if "正确" in st.session_state.qModifyQues_Answer:
            mAnswer = 1
        else:
            mAnswer = 0
    elif st.session_state.qModifyQues_qType == "填空题":
        for i in range(st.session_state.qModifyQues_optionCount):
            mAnswer = mAnswer + st.session_state[f"qModifyQues_Answer_{i}"] + ";"
        if mAnswer.endswith(";"):
            mAnswer = mAnswer[:-1]
    SQL = f"UPDATE {tablename} set Question = '{mQues}', qOption = '{mOption}', qAnswer = '{mAnswer}', qAnalysis = '{mAnalysis}' where ID = {quesID}"
    mdb_modi(conn, cur, SQL)
    clearModifyQues(quesID, tablename, mRow)
    for key in st.session_state.keys():
        if key.startswith("qModifyQues_"):
            del st.session_state[key]
    st.toast("试题修改成功")


def actionDelQM(quesID, tablename, mRow):
    SQL = f"DELETE from {tablename} where ID = {quesID}"
    mdb_del(conn, cur, SQL)
    clearModifyQues(quesID, tablename, mRow)
    for key in st.session_state.keys():
        if key.startswith("qModifyQues_"):
            del st.session_state[key]
    st.toast("试题删除成功")


def clearModifyQues(quesID, tablename, mRow):
    delTablePack = ["morepractise", "favques"]
    for each in delTablePack:
        SQL = f"DELETE from {each} where Question = '{mRow[0]}' and qOption = '{mRow[1]}' and qAnswer = '{mRow[2]}' and qType = '{mRow[3]}'"
        mdb_del(conn, cur, SQL)
    SQL = f"DELETE from studyinfo where cid = {quesID} and quesTable = '{tablename}'"
    mdb_del(conn, cur, SQL)


def aboutReadme():
    st.markdown(open("./README.md", "r", encoding="utf-8").read())


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
actionUserStatus_menu = st.Page(userStatus, title="用户状态", icon=":material/group:")
dbsetup_page = st.Page("dbsetup.py", title="参数设置", icon=":material/settings:")
dbbasedata_page = st.Page("dbbasedata.py", title="数据录入", icon=":material/app_registration:")
aboutInfo_menu = st.Page(aboutInfo, title="关于...", icon=":material/info:")
#aboutLicense_menu = st.Page(aboutLicense, title="License", icon=":material/copyright:")
aboutReadme_menu = st.Page(aboutReadme, title="Readme", icon=":material/library_books:")
dboutput_menu = st.Page(dboutput, title="文件导出", icon=":material/output:")
dbfunc_menu = st.Page(dbfunc, title="题库功能", icon=":material/input:")
studyinfo_menu = st.Page(studyinfo, title="学习信息", icon=":material/import_contacts:")
Ranking_menu = st.Page(userRanking, title="证书及榜单", icon=":material/stars:")
studyinfo_menu = st.Page(studyinfo, title="学习信息", icon=":material/import_contacts:")
quesModify_menu = st.Page(quesModify, title="试题修改", icon=":material/border_color:")


pg = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.rerun()

if st.session_state.logged_in:
    updatePyFileinfo(st.session_state.debug)
    if st.session_state.examType == "exam":
        pg = st.navigation(
            {
                "功能": [choseExam_page, execExam_page],
                "账户": [changePassword_menu, logout_page],
                "关于": [aboutReadme_menu, aboutInfo_menu],

            }
        )
    elif st.session_state.examType == "training":
        if st.session_state.userType == "admin":
            pg = st.navigation(
                {
                    "功能": [dashboard_page, trainingQues_page, dbbasedata_page, quesModify_menu, dboutput_menu, dbfunc_menu, dbsetup_page],
                    "查询": [search_page, actionUserStatus_menu],
                    "信息": [studyinfo_menu, Ranking_menu],
                    "账户": [changePassword_menu, logout_page],
                    "关于": [aboutReadme_menu, aboutInfo_menu],
                }
            )
        elif st.session_state.userType == "user":
            pg = st.navigation(
                {
                    "功能": [dashboard_page, trainingQues_page],
                    "信息": [studyinfo_menu, Ranking_menu],
                    "账户": [changePassword_menu, logout_page],
                    "关于": [aboutReadme_menu, aboutInfo_menu],
                }
            )
    st.sidebar.write(f"### 姓名: :orange[{st.session_state.userCName}] 站室: :orange[{st.session_state.StationCN}]")
    st.sidebar.caption("📢:red[不要刷新页面, 否则会登出]")
else:
    pg = st.navigation([login_page])

pg.run()
