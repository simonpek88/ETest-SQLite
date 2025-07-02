# coding utf-8
from commFunc import execute_sql, execute_sql_and_commit
from mysql_pool import get_connection


def getVerInfo():
    try:
        sql = "SELECT Sum(pyMC) from verinfo"
        verinfo = execute_sql(cur3, sql)[0][0]
        sql = "SELECT Max(pyLM) from verinfo"
        verLM = execute_sql(cur3, sql)[0][0]
        sql = "SELECT Sum(pyLM * pyMC), Sum(pyMC) from verinfo where pyFile = 'thumbs-up-stars'"
        tmpTable = execute_sql(cur3, sql)
        likeCM = round(tmpTable[0][0] / tmpTable[0][1], 1)

        return verinfo, verLM, likeCM
    except Exception as e:

        return 0, 0, 0


def ClearTables():
    try:
        # 删除 questions 表中的重复记录
        sql_delete_questions = """
            DELETE q1
            FROM questions q1
            JOIN questions q2
            ON q1.Question = q2.Question
            AND q1.qType = q2.qType
            AND q1.StationCN = q2.StationCN
            AND q1.chapterName = q2.chapterName
            WHERE q1.id > q2.id;
        """
        cur3.execute(sql_delete_questions)

        # 删除 commquestions 表中的重复记录
        sql_delete_commquestions = """
            DELETE c1
            FROM commquestions c1
            JOIN commquestions c2
            ON c1.Question = c2.Question AND c1.qType = c2.qType
            WHERE c1.id > c2.id;
        """
        cur3.execute(sql_delete_commquestions)

        # 删除 morepractise 表中的重复记录
        sql_delete_morepractise = """
            DELETE m1
            FROM morepractise m1
            JOIN morepractise m2
            ON m1.Question = m2.Question AND m1.qType = m2.qType AND m1.userName = m2.userName
            WHERE m1.id > m2.id;
        """
        cur3.execute(sql_delete_morepractise)

        # 删除 questionaff 表中的重复记录
        sql_delete_questionaff = """
            DELETE a1
            FROM questionaff a1
            JOIN questionaff a2
            ON a1.chapterName = a2.chapterName AND a1.StationCN = a2.StationCN
            WHERE a1.id > a2.id;
        """
        cur3.execute(sql_delete_questionaff)

        # 删除不在 questions 表中的 chapterName
        sql_delete_invalid_chapters = """
            DELETE FROM questionaff
            WHERE chapterName NOT IN ('公共题库', '错题集', '关注题集')
            AND chapterName NOT IN (SELECT DISTINCT(chapterName) FROM questions);
        """
        cur3.execute(sql_delete_invalid_chapters)

        # 更新 users 表中的用户中文名，去除空格
        sql_update_users = """
            UPDATE users
            SET userCName = REPLACE(userCName, ' ', '')
            WHERE userCName LIKE '% %';
        """
        cur3.execute(sql_update_users)

        # 去除问题字段中的换行符 - questions
        sql_update_questions = """
            UPDATE questions
            SET Question = REPLACE(Question, '\n', '')
            WHERE Question LIKE '%\n%';
        """
        cur3.execute(sql_update_questions)

        # 去除问题字段中的换行符 - commquestions
        sql_update_commquestions = """
            UPDATE commquestions
            SET Question = REPLACE(Question, '\n', '')
            WHERE Question LIKE '%\n%';
        """
        cur3.execute(sql_update_commquestions)

        # 去除问题字段中的换行符 - morepractise
        sql_update_morepractise = """
            UPDATE morepractise
            SET Question = REPLACE(Question, '\n', '')
            WHERE Question LIKE '%\n%';
        """
        cur3.execute(sql_update_morepractise)

        # 提交事务
        conn3.commit()

    except Exception as e:
        conn3.rollback()


def clearModifyQues(quesID, tablename, mRow):
    delTablePack = ["morepractise", "favques"]
    for each in delTablePack:
        sql = f"DELETE from {each} where Question = '{mRow[0]}' and qOption = '{mRow[1]}' and qAnswer = '{mRow[2]}' and qType = '{mRow[3]}'"
        execute_sql_and_commit(conn3, cur3, sql)
    sql = f"DELETE from studyinfo where cid = {quesID} and quesTable = '{tablename}'"
    execute_sql_and_commit(conn3, cur3, sql)


def reviseQues():
    for each in ["questions", "commquestions"]:
        for each2 in [['（', '('], ['）', ')']]:
            sql = f"UPDATE {each} set Question = replace(Question, '{each2[0]}', '{each2[1]}') where qType = '填空题' and Question like '%{each2[0]}%'"
            execute_sql_and_commit(conn3, cur3, sql)
        for each2 in ['( )', '(  )', '(   )', '(    )']:
            sql = f"UPDATE {each} set Question = replace(Question, '{each2}', '()') where qType = '填空题' and Question like '%{each2}'"
            execute_sql_and_commit(conn3, cur3, sql)


def getStationCNALL(flagALL=False):
    StationCNamePack = []
    if flagALL:
        StationCNamePack.append("全站")
    sql = "SELECT Station from stations order by ID"
    rows = execute_sql(cur3, sql)
    for row in rows:
        StationCNamePack.append(row[0])

    return StationCNamePack


def get_userName(searchUserName=""):
    searchUserNameInfo = ""
    if len(searchUserName) > 1:
        sql = f"SELECT userName, userCName, StationCN from users where userName like '{searchUserName}%'"
        rows = execute_sql(cur3, sql)
        for row in rows:
            searchUserNameInfo += f"用户编码: :red[{row[0]}] 姓名: :blue[{row[1]}] 站室: :orange[{row[2]}]\n\n"
    if searchUserNameInfo != "":
        searchUserNameInfo += "\n请在用户编码栏中填写查询出的完整编码"

    return searchUserNameInfo


def get_userCName(searchUserCName=""):
    searchUserCNameInfo = ""
    if len(searchUserCName) > 1:
        sql = f"SELECT userName, userCName, StationCN from users where userCName like '{searchUserCName}%'"
        rows = execute_sql(cur3, sql)
        for row in rows:
            searchUserCNameInfo += f"用户编码: :red[{row[0]}] 姓名: :blue[{row[1]}] 站室: :orange[{row[2]}]\n\n"
    else:
        searchUserCNameInfo = ":red[**请输入至少2个字**]"
    if searchUserCNameInfo != "" and "请输入至少2个字" not in searchUserCNameInfo:
        searchUserCNameInfo += "\n请在用户编码栏中填写查询出的完整编码"

    return searchUserCNameInfo


conn3 = get_connection()
cur3 = conn3.cursor()
