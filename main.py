#!/usr/bin/env python3

from bottle import get, post, request, response, route, run, static_file
import os.path
import os
import subprocess as sp
import re
from io import BytesIO
import qrcode

ip_pattern = r'inet6?\s+((?:[a-f0-9]+\:\:)?(?:[a-f0-9]+[\.\:]?)+)'

host = '0.0.0.0'
port = 8080

show_hotspot_code = True
hotspot_ssid = 'a laptop somewhere'
hotspot_crypto = 'WPA'
hotspot_password = 'thisisapassword?'

file_dir = './files'

if not os.path.exists(file_dir):
    os.mkdir(file_dir)


def get_ips():
    stdout = sp.run(['ip', 'addr', 'show'], stdout=sp.PIPE).stdout

    ips = []

    for match in re.finditer(ip_pattern, stdout.decode('utf-8')):
        addr = match.group(1)

        if addr != '127.0.0.1':
            ips.append(addr)

    return ips

def current_uri():
    ip = get_ips()[0]
    return 'http://{}:{}'.format(ip, port)

@route('/qr.png')
def qr():
    qr_img = qrcode.make(current_uri())

    img_io = BytesIO()
    qr_img.save(img_io, 'PNG')
    img_io.seek(0)

    response.set_header('Content-Type', 'image/png')

    return img_io

@route('/network.png')
def qr2():
    qr_img = qrcode.make('WIFI:T:'+hotspot_crypto+';S:'+hotspot_ssid+';P:'+hotspot_password+';;')

    img_io = BytesIO()
    qr_img.save(img_io, 'PNG')
    img_io.seek(0)

    response.set_header('Content-Type', 'image/png')

    return img_io

@route('/static/<filename:path>')
def statics(filename):
    return static_file(filename, root='./static')

@route('/js/<filename:path>')
def js(filename):
    return static_file(filename, root='./static/js')

@route('/recv/<filename:path>')
def xmit(filename):
    return static_file(filename, root=file_dir)

def receivable_files():
    it = os.scandir(file_dir)
    for entry in it:
        if not entry.name.startswith('.') and entry.is_file():
            yield entry

def get_receive_links():
    r = ''

    for f in receivable_files():
        r += "<a class=\"download-link button\" href=\"/recv/{}\">{}</a>".format(f.name, f.name)

    return r

@get('/')
def index():
    network_code = r"""
        <div class="container align-right">
            <h2>Scan to connect to this laptop's hotspot:</h2>
            <img src="/network.png" />
        </div>
    """

    if not show_hotspot_code:
        network_code = ""

    current_ip = get_ips()[0]

    return r"""
<html>
    <head>
            <meta charset="utf-8">
            <title>Beam Me Up!</title>
            <link rel="stylesheet" href="/static/style.css">
    </head>
    <script src="js/jquery-3.3.1.js"></script>
    <script src="js/vendor/jquery.ui.widget.js"></script>
    <script src="js/jquery.iframe-transport.js"></script>
    <script src="js/jquery.fileupload.js"></script>
    <script>
        function upload() {
            $('#upload').fileupload({
                url: '/xmit',
                maxChunkSize: 1000000,
                add: function(e, data) {
                    data.context = $('<button/>').text('Upload \''+data.files[0].name+'\'')
                        .appendTo('#upload-container')
                        .click(function() {
                            data.context = $('<p/>').text('Uploading...').replaceAll($(this));
                            data.submit();
                        });
                },
                progress: function(e, data) {
                    var progress = parseInt(data.loaded / data.total * 100, 10);
                    data.context.text('Uploading \''+data.files[0].name+'\': '+progress.toString()+'%');
                },
                done: function(e, data) {
                    data.context.text('Upload of \''+data.files[0].name+'\' complete!');
                }
            })
        }

        $(upload)
    </script>
    <body>
        <div class="overall-container">
            <div class="main-container">
                <h1>Beam Me Up! -- a simple file transfer application</h1>
                <form class="container align-left" action="/xmit" method="post" enctype="multipart/form-data">
                    <h2>Upload Files:</h2>
                    <div class="upload-container" id="upload-container">
                        <input type="file" name="upload" id="upload" />
                    </div>
                </form>
                <div class="container align-right">
                    <h2>Receivable files:</h2>
                    <div class="download-container">
                        """+get_receive_links()+r"""
                    </div>
                </div>
            </div>
            <div class="code-container">
                <div class="container align-left">
                    <h2>Scan to go to this webpage (<a href="""""+current_uri()+r"""">"""+current_uri()+r"""</a>):</h2>
                    <img src="/qr.png" />
                </div>
                """+network_code+"""
            </div>
        </div>
    </body>
</html>
"""

@route('/xmit', method='POST')
def receive_file():
    filename = request.forms.get('filename')
    upload = request.files.get('upload')

    if filename == "" or filename is None:
        filename = upload.filename

    dest_path = os.path.join(file_dir, filename)

    if 'Content-Range' in request.headers:
        range_str = request.headers['Content-Range']
        offset = int(range_str.split(' ')[1].split('-')[0])

        with open(dest_path, 'ab') as dest_file:
            data = upload.file.read()

            print("[{}] Writing {} bytes at offset {}".format(filename, len(data), offset))

            dest_file.seek(offset)
            dest_file.write(data)

        upload.file.close()
    else:
        print("Receiving {} bytes --> {}".format(upload.content_length, filename))
        upload.save(dest_path)

run(host=host, port=port)
