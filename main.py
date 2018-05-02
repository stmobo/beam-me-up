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

def get_ips():
    stdout = sp.run(['ip', 'addr', 'show'], stdout=sp.PIPE).stdout

    ips = []

    for match in re.finditer(ip_pattern, stdout.decode('utf-8')):
        addr = match.group(1)

        if addr != '127.0.0.1':
            ips.append(addr)

    return ips

file_dir = './files'

if not os.path.exists(file_dir):
    os.mkdir(file_dir)

@route('/qr.png')
def qr():
    ip = get_ips()[0]

    qr_img = qrcode.make('http://{}:{}'.format(ip, port))

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
        r += "<div><a href=\"/recv/{}\">{}</a></div>".format(f.name, f.name)

    return r

@get('/')
def index():
    network_code = r"""
        <div class="container">
            <h2>Scan to connect to this laptop's hotspot:</h2>
            <img src="/network.png" />
        </div>
    """

    if not show_hotspot_code:
        network_code = ""

    return r"""
<html>
    <head>
            <meta charset="utf-8">
            <title>Beam Me Up!</title>
            <style>
                div.container {
                    display: inline-block;
                }
                h2 {
                    text-align: center;
                }
            </style>
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
                        .appendTo(document.body)
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
        <form action="/xmit" method="post" enctype="multipart/form-data">
            <div>
                Select a file: <input type="file" name="upload" id="upload" />
            </div>
            <div id="progress"></div>
        </form>
        <div>
        Receivable files:
        """+get_receive_links()+r"""
        </div>
        """+network_code+"""
        <div class="container">
            <h2>Scan to go to this webpage:</h2>
            <img src="/qr.png" />
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
