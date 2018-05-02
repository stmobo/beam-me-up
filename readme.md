# Beam Me Up! -- a simple file transfer application

## What does this do?

Oftentimes, when I'm out and about, I have to move files around between my
laptop and my phone. I could use something like Bluetooth to move files around,
but the problem is that it's slow-- transferring anything larger
about half of a megabyte takes forever, draining my phone battery the entire time.

So I made this thing really quickly. It's a simple web application that
can receive and send files over a Wi-Fi connection-- without requiring actual _Internet_
access.

It also displays QR codes to automatically connect to
the website and possibly also a laptop hotspot for convenience.

## Prerequisites
 * `bottle` (pip)
 * `qrcode` (pip)
 * access to the `ip address show` command (for QR code generation)

## Configuration
The `host` and `port` variables in `main.py` control the IP address and port
the web server listens on.

If `show_hotspot_code` is True, then the webapp will also generate and display
QR codes to connect to a hotspot, using the SSID and password set using the
`hotspot_` variables.

## Running
`python3 main.py`

or alternatively

`./main.py`
