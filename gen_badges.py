# coding utf-8
import importlib.metadata
import os
import sys

from pybadges import badge

# cSpell:ignoreRegExp /[^\s]{16,}/
# cSpell:ignoreRegExp /\b[A-Z]{3,15}\b/g
# cSpell:ignoreRegExp /\b[A-Z]\b/g

def check_is_changed(conn, cur, package_name, package_ver, svg_file):
    if os.path.exists(svg_file):
        if os.path.getsize(svg_file) > 0:
            sql = f"SELECT ID FROM package_info WHERE package_name = '{package_name}'"
            cur.execute(sql)
            result = cur.fetchone()
            if result:
                sql = f"SELECT ID FROM package_info WHERE package_name = '{package_name}' and package_ver = '{package_ver}'"
                cur.execute(sql)
                result2 = cur.fetchone()
                if result2:
                    return False
                else:
                    sql = f"UPDATE package_info SET package_ver = '{package_ver}' where package_name = '{package_name}'"
                    cur.execute(sql)
                    conn.commit()
                    return True
            else:
                sql = f"INSERT INTO package_info (package_name, package_ver) VALUES ('{package_name}', '{package_ver}')"
                cur.execute(sql)
                conn.commit()
                return True
        else:
            os.remove(svg_file)
            sql = f"UPDATE package_info SET package_ver = '{package_ver}' where package_name = '{package_name}'"
            cur.execute(sql)
            conn.commit()
            return True
    else:
        return True


def gen_badge(conn, cur, badge_text_pack, db_type='MySQL', app_name='app_name', app_ver='0.0.0', app_lm='2025-01-02 09:18:18'):
    badge_folder = './Images/badges'
    badge_ver_color = 'orange'

    # 生成app版本号badge
    if check_is_changed(conn, cur, app_name, app_ver, f'{badge_folder}/{app_name}-badge.svg'):
        with open(f'{badge_folder}/{app_name}-badge.svg', 'w') as f:
            f.write(badge(left_text=app_name, right_text=app_ver))
    if check_is_changed(conn, cur, f'{app_name}_last-updated', app_ver, f'{badge_folder}/{app_name}-lm-badge.svg'):
        with open(f'{badge_folder}/{app_name}-lm-badge.svg', 'w') as f:
            f.write(badge(left_text='Updated', right_text=app_lm[2:], right_color=badge_ver_color))

    # 获取python版本
    python_ver = sys.version[:sys.version.find('(')].strip()
    if check_is_changed(conn, cur, 'Python', python_ver, f'{badge_folder}/Python-badge.svg'):
        with open(f'{badge_folder}/Python-badge.svg', 'w') as f:
            #f.write(badge(left_text='Python', right_text=sys.version[:sys.version.find('(')].strip(), logo='https://dev.w3.org/SVG/tools/svgweb/samples/svg-files/python.svg', embed_logo=True))
            f.write(badge(left_text='Python', right_text=python_ver))

    if db_type == 'MySQL':
        # 执行查询以获取MySQL版本
        cur.execute("SELECT VERSION()")
        # 获取查询结果
        db_ver = cur.fetchone()[0]
    elif db_type == 'sqlite3':
        # 执行查询以获取 SQLite 版本号
        cur.execute("SELECT sqlite_version()")
        # 获取查询结果
        db_ver = cur.fetchone()[0]
    else:
        db_ver = 'unknown'
    if check_is_changed(conn, cur, db_type, db_ver, f'{badge_folder}/{db_type}-badge.svg'):
        with open(f'{badge_folder}/{db_type}-badge.svg', 'w') as f:
            f.write(badge(left_text=db_type, right_text=db_ver))

    # 获取指定package的版本号
    for package in badge_text_pack:
        package_version = importlib.metadata.version(package)
        if check_is_changed(conn, cur, package, package_version, f'{badge_folder}/{package}-badge.svg'):
            with open(f'{badge_folder}/{package}-badge.svg', 'w') as f:
                f.write(badge(left_text=package, right_text=package_version))
