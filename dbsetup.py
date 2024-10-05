# coding UTF-8
import apsw
import streamlit as st
import streamlit_antd_components as sac

from commFunc import mdb_del, mdb_ins, mdb_modi, mdb_sel

# cSpell:ignoreRegExp /[^\s]{16,}/
# cSpell:ignoreRegExp /\b[A-Z]{3,15}\b/g


def updateDAParam(updateParamType):
    for key in st.session_state.keys():
        if key.startswith("dasetup_"):
            upID = key[key.find("_") + 1:]
            SQL = f"UPDATE setup_{st.session_state.StationCN} SET param = {int(st.session_state[key])} WHERE ID = {upID}"
            mdb_modi(conn, cur, SQL)
    st.success(f"{updateParamType} 参数更新成功")


def updateCR():
    for key in st.session_state.keys():
        if key.startswith("crsetup_"):
            upID = key[key.find("_") + 1:]
            SQL = f"UPDATE questionaff SET chapterRatio = {st.session_state[key]} WHERE ID = {upID}"
            mdb_modi(conn, cur, SQL)
    st.success("章节权重更新成功")


def updateSwitchOption(quesType):
    if st.session_state[quesType]:
        SQL = f"UPDATE setup_{st.session_state.StationCN} set param = 1 where paramName = '{quesType}'"
    else:
        SQL = f"UPDATE setup_{st.session_state.StationCN} set param = 0 where paramName = '{quesType}'"
    mdb_modi(conn, cur, SQL)
    if quesType == "测试模式":
        st.session_state.debug = bool(st.session_state[quesType])
    #st.success(f"{quesType} 设置更新成功")


def setupReset():
    mdb_del(conn, cur, SQL=f"DELETE from setup_{st.session_state.StationCN}")
    SQL = f"INSERT INTO setup_{st.session_state.StationCN}(paramName, param, paramType) SELECT paramName, param, paramType from setup_默认"
    mdb_ins(conn, cur, SQL)
    SQL = f"UPDATE questionaff set chapterRatio = 10 where StationCN = '{st.session_state.StationCN}' and (chapterName = '公共题库' or chapterName = '错题集')"
    mdb_modi(conn, cur, SQL)
    SQL = f"UPDATE questionaff set chapterRatio = 5 where StationCN = '{st.session_state.StationCN}' and chapterName <> '公共题库' and chapterName <> '错题集'"
    mdb_modi(conn, cur, SQL)
    bcArea.empty()
    st.success("所有设置已重置")


def updateAIModel():
    SQL = f"UPDATE setup_{st.session_state.StationCN} set param = 0 where paramType = 'others' and paramName like '%大模型'"
    mdb_modi(conn, cur, SQL)
    SQL = f"UPDATE setup_{st.session_state.StationCN} set param = 1 where paramType = 'others' and paramName = '{st.session_state.AIModel}'"
    mdb_modi(conn, cur, SQL)
    st.success(f"LLM大模型已设置为{st.session_state.AIModel}")


conn = apsw.Connection("./DB/ETest_enc.db")
cur = conn.cursor()
cur.execute("PRAGMA cipher = 'aes256cbc'")
cur.execute("PRAGMA key = '7745'")
cur.execute("PRAGMA journal_mode = WAL")

st.write("### :green[系统参数设置]")
with st.expander("# :blue[考试参数设置]"):
    #st.subheader("考试参数设置")
    SQL = f"SELECT paramName, param, ID from setup_{st.session_state.StationCN} where paramType = 'exam' order by ID"
    rows = mdb_sel(cur, SQL)
    for row in rows:
        #st.number_input(row[0], min_value=1, max_value=200, value=row[1], key=f"dasetup_{row[2]}")
        if "数量" in row[0]:
            st.slider(row[0], min_value=1, max_value=100, value=row[1], key=f"dasetup_{row[2]}")
        elif "分值" in row[0]:
            st.number_input(row[0], min_value=1, max_value=5, value=row[1], key=f"dasetup_{row[2]}", help="最高5分")
        elif row[0] == "合格分数线":
            st.slider(row[0], min_value=1, max_value=120, value=row[1], key=f"dasetup_{row[2]}", help="建议为总分的80%")
        elif row[0] == "同场考试次数限制":
            st.number_input(row[0], min_value=1, max_value=5, value=row[1], key=f"dasetup_{row[2]}", help="最多5次")
        elif row[0] == "考试题库每次随机生成":
            #st.toggle(row[0], value=row[1], key=f"dasetup_{row[2]}", help="开启有效, 关闭无效")
            sac.switch(label=row[0], value=row[1], key=row[0], on_label="On", align='start', size='md')
            updateSwitchOption(row[0])
        elif row[0] == "考试时间":
            st.slider(row[0], min_value=30, max_value=90, value=row[1], step=10, key=f"dasetup_{row[2]}", help="单位:分钟, 建议为60分钟")
        elif row[0] == "使用大模型评判错误的填空题答案":
            sac.switch(label=row[0], value=row[1], key=row[0], on_label="On", align='start', size='md')
            updateSwitchOption(row[0])
        else:
            st.slider(row[0], min_value=1, max_value=150, value=row[1], key=f"dasetup_{row[2]}")
    updateDA = st.button("考试参数更新", on_click=updateDAParam, args=("考试",))
with st.expander("# :red[章节权重设置]"):
    SQL = "SELECT chapterName, chapterRatio, ID from questionaff where chapterName <> '公共题库' and chapterName <> '错题集' and StationCN = '" + st.session_state.StationCN + "'"
    rows = mdb_sel(cur, SQL)
    if rows:
        SQL = "SELECT chapterName, chapterRatio, ID from questionaff where chapterName = '公共题库' and StationCN = '" + st.session_state.StationCN + "'"
        row = mdb_sel(cur, SQL)[0]
        st.slider(row[0], min_value=1, max_value=10, value=row[1], key=f"crsetup_{row[2]}", help="权重越大的章节占比越高")
        SQL = "SELECT chapterName, chapterRatio, ID from questionaff where chapterName = '错题集' and StationCN = '" + st.session_state.StationCN + "'"
        row = mdb_sel(cur, SQL)[0]
        st.slider(row[0], min_value=1, max_value=10, value=row[1], key=f"crsetup_{row[2]}", help="仅在练习题库中有效")
        for row in rows:
            st.slider(row[0], min_value=1, max_value=10, value=row[1], key=f"crsetup_{row[2]}", help="权重越大的章节占比越高")
        updateCR = st.button("章节权重更新", on_click=updateCR)
    else:
        st.warning("该站室没有可设置章节")
with st.expander("# :green[题型设置]"):
    SQL = f"SELECT paramName, param from setup_{st.session_state.StationCN} where paramType = 'questype' order by ID"
    rows = mdb_sel(cur, SQL)
    for row in rows:
        sac.switch(label=row[0], value=row[1], key=row[0], on_label="On", align='start', size='md')
        updateSwitchOption(row[0])
with st.expander("# :violet[导出文件字体设置]"):
    SQL = f"SELECT paramName, param, ID from setup_{st.session_state.StationCN} where paramType = 'fontsize' order by ID"
    rows = mdb_sel(cur, SQL)
    for row in rows:
        st.number_input(row[0], min_value=8, max_value=32, value=row[1], key=f"dasetup_{row[2]}", help="题库导出至Word文件中的字体大小")
    updateDA = st.button("字体设置更新", on_click=updateDAParam, args=("字体设置",))
with st.expander("# :orange[其他设置]"):
    SQL = f"SELECT paramName, param, ID from setup_{st.session_state.StationCN} where paramType = 'others' order by ID"
    rows = mdb_sel(cur, SQL)
    for row in rows:
        if row[0] == "显示考试时间" or row[0] == "A.I.答案解析更新至题库" or row[0] == "测试模式":
            sac.switch(label=row[0], value=row[1], key=row[0], on_label="On", align='start', size='md')
            updateSwitchOption(row[0])
    AIModel, AIModelIndex = [], 0
    SQL = f"SELECT paramName, param, ID from setup_{st.session_state.StationCN} where paramName like '%大模型' and paramType = 'others' order by ID"
    rows = mdb_sel(cur, SQL)
    for index, value in enumerate(rows):
        AIModel.append(value[0])
        if value[1] == 1:
            AIModelIndex = index
    st.radio("选择LLM大模型", options=AIModel, index=AIModelIndex, key="AIModel", horizontal=True, on_change=updateAIModel, help="讯飞输出质量高, 规范引用准确, 建议选用;文心千帆输出速度快, 内容可用;DeepSeek内容准确性相对高一些")
st.divider()
buttonReset = st.button("重置所有设置", type="primary")
if buttonReset:
    bcArea = st.empty()
    with bcArea.container():
        buttonConfirm = st.button("确认重置", type="secondary", on_click=setupReset)
