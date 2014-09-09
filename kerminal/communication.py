# encoding: utf-8

import asyncio
import json
import logging
import threading

from autobahn.asyncio.websocket import WebSocketClientProtocol,\
                                       WebSocketClientFactory

log = logging.getLogger('kerminal.communication')
log.addHandler(logging.FileHandler('connection.log'))
log.setLevel(logging.DEBUG)

global LIVE_DATA
LIVE_DATA = {}


class TelemachusProtocol(WebSocketClientProtocol):

    def send_json_message(self, message_dict):
        """
        This method renders the dictionary to a string appropriately for
        Telemachus and then sends it to the server. This will probably be used
        much more than `sendMessage` directly.
        """
        msg = json.dumps(message_dict, separators=(',', ':')).encode('utf-8')
        log.debug('Sending message {0}'.format(msg))
        self.sendMessage(msg)

    def onConnect(self, response):
        log.info('Connecting to server at: {0}'.format(response.peer))

    def onOpen(self):
        log.debug('WebSocket connect open.')

        #Below here are things that should be executed once at each connection
        self.send_json_message({'+': ['v.altitude']})

    def onMessage(self, payload, isBinary):
        #The Telemachus server should never send data as binary, but it can't
        #hurt at this stage to enable more debugging
        if isBinary:
            log.debug('Received binary data: {0}'.format(payload))
        else:
            #Should always get a json message
            msg = json.loads(payload.decode('utf-8'))
            global LIVE_DATA
            LIVE_DATA.update(msg)
            log.debug('Message: {0}'.format(msg))

    def onError(self, *args):
        log.debug('Error: {0}'.format(args))

    def onClose(self, wasClean, code, reason):
        log.info('WebSocket connection closed: {0}'.format(reason))
        asyncio.get_event_loop().stop()  # I think this stops the loop on close


class CommsThread(threading.Thread):

    def __init__(self, address='localhost', port=8085, task_queue=None):
        #if task_queue is None:
        super(CommsThread, self).__init__()
        self.daemon = True
        self.address = address
        self.port = port
        self.loop = None
        self.make_connection = threading.Event()  # Internal use
        self.connect_event = threading.Event()  # External tracking
        self.connected = False

        global LIVE_DATA
        self.data = LIVE_DATA

    def connect(self):
        url = 'ws://{0}:{1}/datalink'.format(self.address, str(self.port))
        log.info(url)
        self.factory = WebSocketClientFactory(url, debug=False)
        self.factory.protocol = TelemachusProtocol
        coro = self.loop.create_connection(self.factory,
                                           self.address,
                                           self.port)

        ### MAKING the connection
        #Whether success or fails, connect_event is set, later cleared by UI
        #Success -> self.connected=True ; Failure -> self.connected = False
        #If it fails, abort the connect method,
        try:
            self.loop.run_until_complete(coro)
        #TODO: Add in some informative messages to send back to the UI
        except:
            self.connect_event.set()
            self.connected = False
            self.loop.stop()
            self.loop.close()
            self.make_connection.clear()
            return
        else:
            self.connect_event.set()
            self.connected = True

        ### MAINTAINING the connection
        #connect_event is cleared by UI
        try:
            self.loop.run_forever()
        finally:
            self.loop.close()
            self.make_connection.clear()
            #self.connect_event.clear()

    def init_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def run(self):
        #This thread will stay alive, even if connections are lost or dropped
        while True:
            self.make_connection.wait()
            self.init_loop()
            self.connect()  # this blocks
