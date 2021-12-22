import struct
def read_config(config):
    namemap = {}
    with open(config, 'r') as f:
        for line in f:
            ip_url = line.split(' ')
            ip = ip_url[0]
            name = ip_url[1]
            namemap[name.strip()] = ip
        return namemap
def read_config2(config):
    namemap = {}
    with open(config, 'r') as f:
        for line in f:
            if line.strip() != '':
                ip, name = line.split(' ')[0],line.split(' ')[1]
                namemap[name.strip()] = ip.strip()
    return namemap
d = {}
d = read_config('example.txt')
print(d)
d = read_config2('example.txt')
print(d)
