import os
import re
import subprocess
from time import sleep
from http.server import BaseHTTPRequestHandler, HTTPServer

host_name = '192.168.0.68'
host_port = 8080

connected_to = ""
connected_to_reg = re.compile("[A-F].*")
def get_connected_to():
    global connected_to
    result = subprocess.run(['expressvpn', 'status'], stdout=subprocess.PIPE)
    res = result.stdout.decode('utf-8')
    match = connected_to_reg.search(res)
    if match:
        connected_to = match.group(0)
    else:
        connected_to = res

info = {}
def get_info():
    global info
    info = {}
    result = subprocess.run(['curl', 'ipinfo.io'], stdout=subprocess.PIPE)
    res = result.stdout.decode('utf-8')
    split = res.splitlines()
    if len(split) > 2:
        for line in split[1:-1]:
            line = line.lstrip().replace('"', '').replace(',', '')
            args = line.split(':')
            if len(args) == 2:
                info[args[0]] = args[1]
  
servers = {}
def get_servers():
    global servers
    servers = {}
    result = subprocess.run(['expressvpn', 'list', 'all'], stdout=subprocess.PIPE)
    res = result.stdout.decode('utf-8')
    split = res.splitlines()
    for line in split[3:]:
        key = line[0: 5].rstrip()
        name = line[5:]
        if name[-1] == 'Y':
            name = name[:-1]
        tmp = name
        idx = name.find(')')
        if idx != -1:
            name = name[idx+1:]
        name = name.lstrip().rstrip()
        if len(name) == 0:
            name = tmp.lstrip().rstrip()
        servers[key] = name

class VPNChange(BaseHTTPRequestHandler):

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        get_connected_to()
        get_servers()
        get_info()
        
        def add_info(key, label):
            s = ""
            if key in info:
                s += '<h2>'
                s += label + ': ' + info[key]
                s += '</h2>'
            return s
            
        def add_button(key):
            s = ""
            s += '<h2>'
            s += '<a href="/' + key + '">'
            s += '<button style="height:50px; width:500px;">'
            s += servers[key]
            s += '</button>'
            s += '</a>'
            s += '</h2>'
            return s
        
        html = '<html>'
        html += '<body style="width:500px; margin:auto;">'
        html += '<div class="content">'
        html += '<h1>'
        html += connected_to
        html += '</h1>'
        
        html += add_info('ip', 'IP')
        html += add_info('country', 'Country')
        html += add_info('region', 'Region')
        html += add_info('city', 'City')
        
        html += '<br>' 
        html += '<h1>'
        html += '<a href="/disconnect">'
        html += '<button style="height:50px; width:500px;">'
        html += "Disconnect"
        html += '</button>'
        html += '</a>'
        html += '</h1>'
        html += '<br>'
        
        for key in sorted(servers):
            html += add_button(key)
        html += '</div>'
        html += '</body>'
        html += '</html>'
        
        self.do_HEAD()
        if self.path != '/':
            key = self.path[1:]
            if key in servers:
                result = subprocess.run(['expressvpn', 'disconnect'], stdout=subprocess.PIPE)
                print(result.stdout.decode('utf-8'))
                result = subprocess.run(['expressvpn', 'connect', key], stdout=subprocess.PIPE)
                print(result.stdout.decode('utf-8'))
                get_connected_to()
            elif key == 'disconnect':
                result = subprocess.run(['expressvpn', 'disconnect'], stdout=subprocess.PIPE)
                print(result.stdout.decode('utf-8')) 
                
        self.wfile.write(html.format().encode("utf-8"))

if __name__ == '__main__':
    get_connected_to()
    get_servers()
    get_info()

    http_server = HTTPServer((host_name, host_port), VPNChange)
    print("Server Starts - %s:%s" % (host_name, host_port))

    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()