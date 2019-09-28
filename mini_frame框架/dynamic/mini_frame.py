import logging
import re
from pymysql import connect
from urllib.parse import unquote
url_patterns = dict()


def route(url):
    def set_fun(func):
        url_patterns[url] = func

        def call_func(*args, **kwargs):
            return func(*args, **kwargs)

        return call_func

    return set_fun


'''在python解释器执行这行代码，不用调用， 他就执行了装饰器call_func之前的代码，'''


@route('/index.html')
def index(ret):
    with open('./templates/index.html', encoding='utf-8') as file:
        content = file.read()

    # 创建Connection连接
    conn = connect(host='localhost', port=3306, user='root', password='root', database='stock_db', charset='utf8')
    # 获得Cursor对象
    cs = conn.cursor()
    cs.execute('select * from info;')
    stock_infos = cs.fetchall()

    cs.close()
    conn.close()

    tr_template = """<tr>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>
                    <input type="button" value="添加" id="toAdd" name="toAdd" systemidvaule="{}">
                </td>
                </tr>
            """

    context = ''
    for row in stock_infos:
        context += tr_template.format(*row, row[1])

    content = re.sub('{%content%}', context, content)
    return content


@route('/center.html')
def center(ret):
    with open('./templates/center.html', encoding='utf-8') as file:
        content = file.read()

    # 创建Connection连接
    conn = connect(host='localhost', port=3306, user='root', password='root', database='stock_db', charset='utf8')
    # 获得Cursor对象
    cs = conn.cursor()
    cs.execute(
        "select i.code,i.short,i.chg,i.turnover,i.price,i.highs,f.note_info from info as i inner join focus as f on i.id=f.info_id;")
    stock_infos = cs.fetchall()
    cs.close()
    conn.close()

    tr_template = """
            <tr>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>
                    <a type="button" class="btn btn-default btn-xs" href="/update/{}.html"> <span class="glyphicon glyphicon-star" aria-hidden="true"></span> 修改 </a>
                </td>
                <td>
                    <input type="button" value="删除" id="toDel" name="toDel" systemidvaule="{}">
                </td>
            </tr>
        """

    context = ""
    for row in stock_infos:
        context += tr_template.format(*row, row[0], row[0])

    content = re.sub('{%content%}', context, content)

    return content


# 给路由添加正则表达式的原因：在实际开发时，url中往往会带有很多参数，例如/add/000007.html中000007就是参数，
# 如果没有正则的话，那么就需要编写N次@route来进行添加 url对应的函数 到字典中，此时字典中的键值对有N个，浪费空间
# 而采用了正则的话，那么只要编写1次@route就可以完成多个 url例如/add/00007.html /add/000036.html等对应同一个函数，此时字典中的键值对个数会少很多
@route("/add/(\d+).html")
def add_focus(ret):
    # 1.获取股票代码
    stock_code = ret.group(1)

    # 2. 判断是否有这个股票代码
    # 创建Connection连接
    conn = connect(host='localhost', port=3306, user='root', password='root', database='stock_db', charset='utf8')
    # 获得Cursor对象
    cs = conn.cursor()
    sql = '''select id from info where code=%s;'''
    cs.execute(sql, (stock_code,))
    info_id = cs.fetchone()
    if not info_id:
        cs.close()
        conn.close()
        return '大哥，我们是创业公司，请手下留情。。。。'

    # 3. 判断一下是否已经关注过
    sql = '''select * from focus where info_id={}'''.format(info_id[0])
    cs.execute(sql)
    if cs.fetchone():
        cs.close()
        conn.close()
        return '已经关注过'

    # 4. 添加关注

    note_info = '还行'
    print(note_info)
    sql = "insert into focus(note_info, info_id) values('{}', {})".format(note_info, info_id[0])
    print(sql)
    cs.execute(sql)
    conn.commit()
    cs.close()
    conn.close()
    return "add  ok ....{}".format(stock_code)


@route("/delete/(\d+).html")
def detele_focus(ret):
    # 1.获取股票代码
    stock_code = ret.group(1)

    # 2. 判断是否有这个股票代码
    # 创建Connection连接
    conn = connect(host='localhost', port=3306, user='root', password='root', database='stock_db', charset='utf8')
    # 获得Cursor对象
    cs = conn.cursor()
    sql = '''select f.id from info as i inner join focus as f on i.id=f.info_id where i.code=%s;'''
    cs.execute(sql, (stock_code,))
    focus_id = cs.fetchone()
    if not focus_id:
        cs.close()
        conn.close()
        return '此股票没关注，不能取消'

    # 4. 取消关注
    sql = "delete from focus where id='{}'".format(focus_id[0])
    print(sql)
    cs.execute(sql)
    conn.commit()
    cs.close()
    conn.close()
    return "delete  ok ....{}".format(stock_code)


@route(r"/update/(\d+)\.html")
def show_update_page(ret):
    """显示修改的那个页面"""
    # 1. 获取股票代码
    stock_code = ret.group(1)

    # 2. 打开模板
    with open("./templates/update.html", encoding='utf-8') as f:
        content = f.read()

    # 3. 根据股票代码查询相关的备注信息
    conn = connect(host='localhost', port=3306, user='root', password='root', database='stock_db', charset='utf8')
    cs = conn.cursor()
    sql = """select f.note_info from focus as f inner join info as i on i.id=f.info_id where i.code=%s;"""
    cs.execute(sql, (stock_code,))
    stock_infos = cs.fetchone()
    note_info = stock_infos[0]  # 获取这个股票对应的备注信息
    cs.close()
    conn.close()

    content = re.sub(r"\{%note_info%\}", note_info, content)
    content = re.sub(r"\{%code%\}", stock_code, content)

    return content


@route(r"/update/(\d+)/(.*)\.html")
def save_update_page(ret):
    """"保存修改的信息"""
    stock_code = ret.group(1)
    comment = ret.group(2)
    comment = unquote(comment)


    conn = connect(host='localhost', port=3306, user='root', password='root', database='stock_db', charset='utf8')
    cs = conn.cursor()
    sql = """update focus set note_info=%s where info_id = (select id from info where code=%s);"""
    cs.execute(sql, (comment, stock_code))
    conn.commit()
    cs.close()
    conn.close()

    return "修改成功..."


def application(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/html;charset=utf-8')])
    url = environ['path_info']
    # 判断key值可以直接对dict in
    '''因为异常可以进行传递'''
    # if url in url_patterns:
    #     func = url_patterns[url]
    #     return func()

    # 第一步，创建一个logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Log等级总开关

    # 第二步，创建一个handler，用于写入日志文件
    logfile = './log.txt'
    fh = logging.FileHandler(logfile, mode='a', encoding='utf-8')  # open的打开模式这里可以进行参考
    fh.setLevel(logging.INFO)  # 输出到file的log等级的开关


    # 第四步，定义handler的输出格式
    formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    fh.setFormatter(formatter)

    # 第五步，将logger添加到handler里面
    logger.addHandler(fh)

    logging.info("访问的是: %s" % url)

    url_patterns.keys()
    try:
        ret = None
        for url_re, func in url_patterns.items():
            ret = re.match(url_re, url)

            if ret:
                return func(ret)
                break
            # else:
            #     return "请求的url({})没有对应的函数....".format(url)

        else:
            logging.warning("没有对应的函数....")
            return "请求的url({})没有对应的函数....".format(url)


    except Exception as e:
        return '产生子异常：{}'.format(e)
