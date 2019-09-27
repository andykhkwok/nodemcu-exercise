try:
    import usocket as socket
except:
    import socket



response_404 = """HTTP/1.0 404 NOT FOUND

<h1>404 Not Found</h1>
"""


response_500 = """HTTP/1.0 500 INTERNAL SERVER ERROR

<h1>500 Internal Server Error</h1>
"""


response_template = """HTTP/1.0 200 OK

%s
"""


import machine
import ntptime, utime
from machine import RTC
from machine import Pin
from time import sleep


seconds = ntptime.time()
rtc = RTC()
rtc.datetime(utime.localtime(seconds))


def time():
    body = """<html>
 <body>
 <h1>Time</h1>
 <p>%s</p>
 </body>
 </html>
    """ % str(rtc.datetime())

    return response_template % body


def dummy(pin, led, switch, adc):
    body = "This is a dummy endpoint"

    return response_template % body

def lighton(pin, led, switch, adc):
    pin.value(1)
    led.value(1)
    body = "The light is ON."
    return response_template % body

def lightoff(pin, led, switch, adc):
    pin.value(0)
    led.value(0)
    body = "The light is OFF."
    return response_template % body

def switch(pin, led, switch, adc):
    body = '{' + 'state: {} '.format(switch.value()) + '}'
    return response_template % body

def photo(pin, led, switch, adc):
    body = '{' + 'photo-senor value: {} '.format(adc.read()) + '}'
    return response_template % body

handlers = {
    'time': time,
    'dummy': dummy,
    'lighton': lighton,
    'lightoff': lightoff,
    'switch': switch,
    'photo': photo,
}

def main():

    pin = machine.Pin(9, machine.Pin.OUT)
    led = machine.Pin(2, machine.Pin.OUT)
    switch = machine.Pin(10, machine.Pin.IN) 
    adc = machine.ADC(0)
    
    s = socket.socket()
    ai = socket.getaddrinfo("0.0.0.0", 8080)
    addr = ai[0][-1]

    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    s.bind(addr)
    s.listen(5)
    print("Listening, connect your browser to http://<this_host>:8080/")

    while True:
        res = s.accept()
        client_s = res[0]
        client_addr = res[1]
        req = client_s.recv(4096)
        print("Request:")
        print(req)

        # The first line of a request looks like "GET /arbitrary/path/ HTTP/1.1".
        # This grabs that first line and whittles it down to just "/arbitrary/path/"

        try:
            # Given the path, identify the correct handler to use
            path = req.decode().split("\r\n")[0].split(" ")[1]
            handler = handlers[path.strip('/').split('/')[0]]
            response = handler(pin, led, switch, adc)
        except KeyError:
            response = response_404
        except Exception as e:
            response = response_500
            print(str(e))

        # A handler returns an entire response in the form of a multi-line string.
        # This breaks up the response into single strings, byte-encodes them, and
        # joins them back together with b"\r\n". Then it sends that to the client.
        client_s.send(b"\r\n".join([line.encode() for line in response.split("\n")]))

        client_s.close()
        print()

main()
