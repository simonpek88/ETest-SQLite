# coding UTF-8
import time

import apsw
import streamlit as st

from commFunc import GenerExam, getParam, mdb_del, mdb_ins, mdb_modi, mdb_sel

# cSpell:ignoreRegExp /[^\s]{16,}/
# cSpell:ignoreRegExp /\b[A-Z]{3,15}\b/g


def training():
    StationCN = st.session_state.StationCN
    userName = st.session_state.userName
    for each in ["questions", "commquestions"]:
        for each2 in [['（', '('], ['）', ')']]:
            SQL = f"UPDATE {each} set Question = replace(Question, '{each2[0]}', '{each2[1]}') where qType = '填空题' and Question like '%{each2[0]}%'"
            mdb_modi(conn, cur, SQL)
        for each2 in ['( )', '(  )', '(   )', '(    )']:
            SQL = f"UPDATE {each} set Question = replace(Question, '{each2}', '()') where qType = '填空题' and Question like '%{each2}'"
            mdb_modi(conn, cur, SQL)
    quesType = []
    SQL = f"SELECT paramName from setup_{st.session_state.StationCN} where paramType = 'questype' and param = 1 order by ID"
    rows = mdb_sel(cur, SQL)
    for row in rows:
        quesType.append([row[0], getParam(f"{row[0]}数量", st.session_state.StationCN)])
    generPack, examIDPack, chapterPack, tempCP, genResult = [], [], [], [], []
    generQues = st.empty()
    with generQues.container():
        if st.session_state.examType == "exam":
            #date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            date = int(time.time())
            SQL = f"SELECT examName from examidd where StationCN = '{st.session_state.StationCN}' and validDate >= {date} order by validDate"
            rows = mdb_sel(cur, SQL)
            for row in rows:
                examIDPack.append(row[0])
            examName = st.selectbox("请选择考试场次", examIDPack, index=None)
            if examName:
                generButtonQues = st.button("开始考试")
                if generButtonQues:
                    st.session_state.examName = examName
                    st.spinner("正在生成题库...")
                    SQL = "SELECT chapterName from questionaff where chapterName <> '错题集' and StationCN = '" + StationCN + "'"
                    rows = mdb_sel(cur, SQL)
                    for row in rows:
                        generPack.append(row[0])
                    genResult = GenerExam(generPack, StationCN, userName, examName, st.session_state.examType, quesType, st.session_state.examRandom, st.session_state.GenerNewOnly)
        elif st.session_state.examType == "training":
            col1, col2 = st.columns(2)
            SQL = f"SELECT chapterRatio from questionaff where StationCN = '{st.session_state.StationCN}' and chapterName = '公共题库'"
            tempCR1 = mdb_sel(cur, SQL)[0][0]
            SQL = f"SELECT chapterRatio from questionaff where StationCN = '{st.session_state.StationCN}' and chapterName = '错题集'"
            tempCR2 = mdb_sel(cur, SQL)[0][0]
            with col1:
                generPack.append(st.checkbox("公共题库", value=True))
                for i in range(4):
                    st.caption("")
                generPack.append(st.checkbox("错题集", value=False))
                for i in range(4):
                    st.caption("")
            with col2:
                st.slider("章节权重", min_value=1, max_value=10, value=tempCR1, step=1, key="tempCR_1", on_change=updateCR)
                st.slider("章节权重", min_value=1, max_value=10, value=tempCR2, step=1, key="tempCR_2", on_change=updateCR)
            i, k = 0, 0
            SQL = "SELECT chapterName, chapterRatio, ID from questionaff where StationCN = '" + StationCN + "' and chapterName <> '公共题库' and chapterName <> '错题集' order by chapterName"
            rows = mdb_sel(cur, SQL)
            for row in rows:
                with col1:
                    generPack.append(st.checkbox(row[0], value=True))
                    i = 2 if i > 2 else i
                    for j in range(i + 1):
                        st.caption("")
                with col2:
                    if k == 7 or k == 10:
                        st.caption("")
                    st.slider("章节权重", min_value=1, max_value=10, value=row[1], step=1, key=f"tempCR_{row[2]}", on_change=updateCR)
                i += 1
                k += 1
            st.checkbox("仅未学习试题", value=False, key="GenerNewOnly", help="仅从未学习试题中生成")
            generButtonQues = st.button("生成题库")
            if generButtonQues:
                st.session_state.examName = "练习题库"
                st.spinner("正在生成题库...")
                for index, value in enumerate(generPack):
                    if value:
                        if index == 0:
                            chapterPack.append("公共题库")
                        elif index == 1:
                            chapterPack.append("错题集")
                        else:
                            chapterPack.append(rows[index - 2][0])
                if chapterPack:
                    genResult = GenerExam(chapterPack, StationCN, userName, st.session_state.examName, st.session_state.examType, quesType, st.session_state.examRandom, st.session_state.GenerNewOnly)
                else:
                    st.warning("题库生成试题失败, 请检查题库设置")
    if genResult:
        if genResult[0]:
            generQues.empty()
            st.success(f"题库生成完毕, 总共生成{genResult[1]}道试题, 请在👈左侧边栏选择功能")
            st.session_state.examTable = genResult[2]
            st.session_state.examFinalTable = genResult[3]
            st.session_state.confirmSubmit = False
            st.session_state.curQues = 0
            st.session_state.flagCompleted = False
            st.session_state.examStartTime = int(time.time())
            st.session_state.goto = False
            if st.session_state.examType != "training":
                st.session_state.examChosen = True
            else:
                st.session_state.examChosen = False
        else:
            st.session_state.examChosen = False
            st.warning("题库生成试题不满足要求, 请检查生成设置或联系管理员")


@st.fragment
def updateCR():
    for key in st.session_state.keys():
        if key.startswith("tempCR_"):
            upID = key[key.find("_") + 1:]
            SQL = f"UPDATE questionaff SET chapterRatio = {st.session_state[key]} WHERE ID = {upID}"
            mdb_modi(conn, cur, SQL)


conn = apsw.Connection("./DB/ETest_enc.db")
cur = conn.cursor()
cur.execute("PRAGMA cipher = 'aes256cbc'")
cur.execute("PRAGMA key = '7745'")
cur.execute("PRAGMA journal_mode = WAL")

if st.session_state.examType == "training":
    #st.write("### :red[生成练习题库]")
    st.markdown("<font face='微软雅黑' color=blue size=20><center>**生成练习题库**</center></font>", unsafe_allow_html=True)
elif st.session_state.examType == "exam":
    st.markdown("<font face='微软雅黑' color=red size=20><center>**选择考试**</center></font>", unsafe_allow_html=True)
if not st.session_state.examChosen:
    training()
else:
    st.warning("你不能重复选择考试场次")
