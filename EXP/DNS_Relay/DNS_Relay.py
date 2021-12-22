import socket
import threading
from time import time


class DNS_Relay_Server:  # 一个relay server实例，通过缓存文件和外部地址来初始化
    def __init__(self, cache_file, name_server):
        # url_IP字典:通过域名查询ID
        self.url_ip = {}
        self.cache_file = cache_file
        self.load_file()
        self.name_server = name_server
        # trans字典：通过DNS响应的ID来获得原始的DNS数据包发送方
        self.trans = {}
        self.load_file()

    def load_file(self):
        f = open(self.cache_file, 'r', encoding='utf-8')
        for line in f:
            ip_url = line.split(' ')
            ip = ip_url[0]
            name = ip_url[1]
            self.url_ip[name.strip()] = ip
        f.close()

    def run(self):
        buffer_size = 512
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind(('', 53))
        server_socket.setblocking(False)
        while True:
            try:
                data, addr = server_socket.recvfrom(buffer_size)
                threading.Thread(target=self.handle, args=(server_socket, data, addr)).start()
            except:
                continue

    def handle(self, server_socket, data, addr):
        start_time = time()
        RecvDp = DNS_Packege(data)
        # print('RecvDp: ', data)
        id = RecvDp.ID
        # print('ID: ', id)
        # print('QR', RecvDp.QR)
        if RecvDp.QR == 0:  # query
            # statement
            name = RecvDp.name
            # print('name: ', name)
            # print('urt_ip: ', self.url_ip)
            # print('qtype: ', RecvDp.QTYPE)
            # print('name in urlip:', name in self.url_ip)
            if name in self.url_ip and RecvDp.QTYPE == 1:
                ip = self.url_ip[name]
                Intercepted = ip == '0.0.0.0'
                # print('intercepted or not:', Intercepted)
                response = RecvDp.generate_response(ip, Intercepted)
                # print('res is ', response)
                server_socket.sendto(response, addr)
                print('%s' % name, end='\t')
                if ip == '0.0.0.0':
                    print('INTERCEPT', '%fs' % (time() - start_time), sep='\t')
                    print()
                else:
                    print('RESOLVE', '%fs' % (time() - start_time), sep='\t')
                    print()
            elif RecvDp.QTYPE == 1:
                server_socket.sendto(data, self.name_server)
                self.trans[id] = (addr, name, start_time)
                print('%s' % name, 'RELAY', '%fs' % (time() - start_time), sep='\t')
                print()
        else:  # response
            if id in self.trans:
                target_addr, name, start_time = self.trans[id]
                server_socket.sendto(data, target_addr)
                del self.trans[id]


class DNS_Packege:  # 一个DNS Frame实例，用于解析和生成DNS帧
    def __init__(self, data):
        Msg_arr = bytearray(data)
        self.msg = Msg_arr
        # ID
        self.ID = (Msg_arr[0] << 8) + Msg_arr[1]
        # FLAGS
        self.Flags = (Msg_arr[2] << 8) + Msg_arr[3]
        self.QR = Msg_arr[2] >> 7
        # 资源记录数量
        self.QDCOUNT = (Msg_arr[4] << 8) + Msg_arr[5]
        # 回答资源记录数
        self.ACOUNT = (Msg_arr[6] << 8) + Msg_arr[7]
        self.auRR = (Msg_arr[8] << 8) + Msg_arr[9]
        self.addRR = (Msg_arr[10] << 8) + Msg_arr[11]
        # query内容解析
        self.querybytes = None
        self.name = ""
        self.name_length = 0
        self.QTYPE = None
        self.QCLASS = None
        if self.QR == 0:
            self.get_query(Msg_arr[12:])

    def get_query(self, data):
        # print('get_query data:', data)
        i = 0
        while (data[i] != 0):
            l = data[i]
            for j in range(i + 1, i + l + 1):
                c = data[j]
                self.name += chr(c)
            i += l + 1
            if data[i] != 0:
                self.name += '.'
            # print('debug:', self.name)
        # print('name has built: ', self.name)
        self.QTYPE = (data[i + 1] << 8) + data[i + 2]
        self.QCLASS = (data[i + 3] << 8) + data[i + 4]
        self.name_length = i + 5
        self.querybytes = data[0:i + 5]

    def generate_response(self, ip, Intercepted):
        if not Intercepted:
            flag = 0x8180
        else:
            flag = 0x8583
        # flag
        mss = self.msg
        mss[2] = (flag & 0xff00) >> 8
        mss[3] = (flag & 0x00ff)
        # answer count
        mss[6] = mss[4]
        mss[7] = mss[5]
        response_byte = self.get_response(ip)
        # print('answer: ', bytes(mss) + response_byte)
        return bytes(mss) + response_byte
        # return bytes(res)

    def get_response(self, ip):
        name = b'\xC0\x0C'  # 压缩算法,point to 0c
        type = b'\x00\x01'
        c = b'\x00\x01'
        ttl = b'\x00\x00\x00\xc8' # ttl = 200
        rdlength = b'\x00\x04'
        res = name + type + c + ttl + rdlength
        # print('res1: ', res)
        s = ip.split('.')
        res += bytes([int(s[0]),int(s[1]),int(s[2]),int(s[3]),])
        # print('res2:', res)
        return res


if __name__ == '__main__':
    cache_file = 'example.txt'
    name_server = ('223.5.5.5', 53)
    relay_server = DNS_Relay_Server(cache_file, name_server)  # 构造一个DNS_Relay_Server实例
    relay_server.run()
