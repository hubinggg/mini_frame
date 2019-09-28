import multiprocessing
import socket
import re
from datetime import date, datetime

import sys

# from dynamic import mini_frame

'''
服务器只负责转发合并数据
'''

class WSGIServer(object):

    def __init__(self, port, app, static_path):
        # 1. 搭建tpc服务器端 创建套接字
        self.tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.app = app
        self.static_path = static_path

        # 设置当服务器先close 即服务器端4次挥手之后资源能够立即释放，这样就保证了，下次运行程序时 可以立即绑定7788端口
        self.tcp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # 2. 绑定address
        self.tcp_server_socket.bind(('127.0.0.1', port))

        # 3. 将手机设置为正常的 响铃模式(让默认的套接字由主动变为被动 listen)
        self.tcp_server_socket.listen(128)

    def service_client(self, new_client_socket, i):
        '''为这个客户端返回数据'''
        # 接受浏览器发送的请求信息
        # GET / HTTP/1.1
        print()
        print("第{}次请求".format(i))
        print('-' * 20)
        # 变量初始化问题 知道类型就设置成相应类型，不知道就设置成None
        url = ''
        request_data = new_client_socket.recv(1024 * 1024)
        if request_data:
            request_str = request_data.decode()
            print('请求头：\n', request_str)
            # [^/]+：匹配任意字符串一直到/停， 只要不是/，前面至少有一个， ^在[]中为取反，不在[]为匹配字符串开头
            # [^/]+/(.*?)\sHTTP/1.1
            # [ ^] *: 一直匹配到空格停
            ret = re.match(r'[^/]+(/[^ ]*)', request_str)
            url = ret.group(1)
            if url == '/':
                url = '/index.html'

        print('请求的资源：', url)

        if not url.endswith('.html'):
            try:
                # 发送响应http格式的信息给浏览器
                header = 'HTTP/1.1 200 OK\n '
                header += 'Content-Type: text/html;charset=utf-8 \r\n'
                header += '\n'
                # 用h1 html标签浏览器可以立即加载出信息，用纯文本发送数据，浏览器会认为你还有数据没发送完，一直加载，不显示信息
                # 读取html文件夹中的index.html文件，作为响应的body
                filepath = self.static_path + url
                # print(filepath)
                file = open(filepath, 'rb')
                body = file.read()
                file.close()

                # Can't convert 'bytes' object to str implicitly
                # response_data += body
                # 可以将response分部发送给浏览器，这个整个程序执行完一次才叫一次服务器的响应过程
                # 将response header部分发送给浏览器
                new_client_socket.send(header.encode())  # encode()为编码，编码成字节码，io中可传输的数据格式
                # 将response body部分发送给浏览器
                new_client_socket.send(body)
            except:
                header = 'HTTP/1.1 404 NOT FOUND\r\n '
                header += 'Content-Type: text/html;charset=utf-8 \r\n'
                header += '\r\n'
                body = '<h1>NOT FOUND</h1>'
                # 将response header部分发送给浏览器
                new_client_socket.send(header.encode())  # encode()为编码，编码成字节码，io中可传输的数据格式
                # 将response body部分发送给浏览器
                new_client_socket.send(body.encode())
        else:
            environ = dict()
            environ['path_info'] = url
            body = self.app(environ, self.set_response_header)

            header = 'HTTP/1.1 {}\n '.format(self.status)
            for key, value in self.headers:
                header += '{}:{}\r\n'.format(key, value)
            header += '\n'

            response = header + body

            new_client_socket.send(response.encode('utf-8'))

        print('第{}次请求完毕'.format(i))
        new_client_socket.close()

    def set_response_header(self, status, headers):
        self.status = status
        self.headers = [('server', 'mini_web v1.1')]
        self.headers += headers

    def run_forever(self):
        i = 0
        while True:
            i += 1
            # 4. 等待别人的电话到来(等待客户端的链接 accept)
            new_client_socket, client_addr = self.tcp_server_socket.accept()
            # 5. 为这个客户服务

            '''
        用process创建子进程时，子进程会复制一份主进程的资源
         p.start()这句话之前的全局变量和局部变量都会被复制一份，所以tcp_server_socket.accept()
         也会被赋值一份，复制的资源：地址空间，全局变量，文件描述符，各种硬件等等资源
         socket接口对应的操作系统的网络驱动程序，网络驱动程序对应一个文件描述符，所以这里的文件描述符对应两份，有两份网络驱动，所以要关闭两次，一份主进程对应第86行，一份是子进程对应57行，不然的话只关闭一次网络驱动还在运行
        '''
            p = multiprocessing.Process(target=self.service_client, args=(new_client_socket, i))
            p.start()
            new_client_socket.close()

        # 7. 关闭socket网络io流
        tcp_server_socket.close()


def main():
    global frame_name, app_name
    if len(sys.argv) == 3:
        try:
            port = int(sys.argv[1])
            frame_app_name = sys.argv[2]
        except:
            print('端口输入错误。。。。')
            return

    else:
        print('请按照一下方式来运行')
        print('python3 xxx.py port mini_frame:application')
        return  # return的功能--结束函数

    try:
        frame_name, app_name = re.split(':', frame_app_name)
    except:
        print('输入有误')

    with open('web_server.conf') as file:
        conf_info = eval(file.read())

    # 动态导入模块
    sys.path.insert(0, conf_info['dynamic_path'])
    # import frame_name --->它直接找frame_name这个变量名，不会找它的值
    frame = __import__(frame_name)  # 返回值标记着 导入的这个模块，表示创建了一个模块实例对象
    app = getattr(frame, app_name)  # 此时app就指向了 dynamic/mini_frame模块中的application这个函数

    wsgiServer = WSGIServer(port, app, conf_info['static_path'])
    wsgiServer.run_forever()


if __name__ == '__main__':
    main()
