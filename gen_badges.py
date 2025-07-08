# coding utf-8
import importlib.metadata
import sys

from pybadges import badge

# cSpell:ignoreRegExp /[^\s]{16,}/
# cSpell:ignoreRegExp /\b[A-Z]{3,15}\b/g
# cSpell:ignoreRegExp /\b[A-Z]\b/g


def gen_badge(cur, badge_text_pack, db_type='MySQL', app_name='app_name', app_ver='0.0.0', app_lm='2025-01-02 09:18:18'):
    badge_folder = './Images/badges'
    badge_ver_color = 'orange'

    # 生成app版本号badge
    with open(f'{badge_folder}/{app_name}-badge.svg', 'w') as f:
        f.write(badge(left_text=app_name, right_text=app_ver))
    with open(f'{badge_folder}/{app_name}-lm-badge.svg', 'w') as f:
        f.write(badge(left_text='Updated', right_text=app_lm[2:], right_color=badge_ver_color))

    # 获取python版本
    with open(f'{badge_folder}/Python-badge.svg', 'w') as f:
        #f.write(badge(left_text='Python', right_text=sys.version[:sys.version.find('(')].strip(), logo='https://dev.w3.org/SVG/tools/svgweb/samples/svg-files/python.svg', embed_logo=True))
        f.write(badge(left_text='Python', right_text=sys.version[:sys.version.find('(')].strip()))

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
    with open(f'{badge_folder}/{db_type}-badge.svg', 'w') as f:
        f.write(badge(left_text=db_type, right_text=db_ver))

    # 获取指定package的版本号
    for package in badge_text_pack:
        package_version = importlib.metadata.version(package)

        with open(f'{badge_folder}/{package}-badge.svg', 'w') as f:
            if package == 'streamlit_antd_components':
                package = 'Ant Comp'
            f.write(badge(left_text=package, right_text=package_version))
