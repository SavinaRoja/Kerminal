# encoding: utf-8

import asyncio
import json
import logging
import threading
import queue

from autobahn.asyncio.websocket import WebSocketClientProtocol,\
                                       WebSocketClientFactory

log = logging.getLogger('kerminal.communication')
log.setLevel(logging.DEBUG)

global LIVE_DATA
LIVE_DATA = {}

global MSG_QUEUE
MSG_QUEUE = queue.Queue()


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
        self.send_json_message({'+': ['v.altitude', 't.universalTime',
                                      'v.missionTime', 'p.paused']})

        @asyncio.coroutine
        def consume_queue():
            global MSG_QUEUE
            while True:
                try:
                    msg_dict = MSG_QUEUE.get_nowait()
                except queue.Empty:
                    #The sleep time here could be changed, or I could set this
                    #up to be signaled by an event
                    yield from asyncio.sleep(0.1)
                else:
                    self.send_json_message(msg_dict)

        asyncio.Task(consume_queue())

    def onMessage(self, payload, isBinary):
        #The Telemachus server should never send data as binary, but it can't
        #hurt at this stage to enable more debugging
        if isBinary:
            log.debug('Received binary data: {0}'.format(payload))
        else:
            #Should always get a json message
            msg = json.loads(payload.decode('utf-8'))
            log.debug('Message: {0}'.format(msg))
            global LIVE_DATA
            LIVE_DATA.update(msg)

    def onError(self, *args):
        log.debug('Error: {0}'.format(args))

    def onClose(self, wasClean, code, reason):
        log.info('WebSocket connection closed: {0}'.format(reason))
        asyncio.get_event_loop().stop()


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

        global MSG_QUEUE
        self.msg_queue = MSG_QUEUE

    def connect(self):
        url = 'ws://{0}:{1}/datalink'.format(self.address, str(self.port))
        log.info(url)
        self.factory = WebSocketClientFactory(url, debug=False)
        self.factory.protocol = TelemachusProtocol
        coro = self.loop.create_connection(self.factory,
                                           self.address,
                                           self.port)

        #Notes about events:
        #The UI waits on the connect_event to know if the connection has either
        #failed or succeeded; the UI will clear this event.
        #self.connected differentiates between success and failure
        #Success -> self.connected=True ; Failure -> self.connected = False

        ### MAKING the connection
        try:
            self.loop.run_until_complete(coro)
        #TODO: Add in some informative messages to send back to the UI
        except:  # Failure, shut down and abort
            self.connect_event.set()  # Connection resolved
            self.connected = False  # Connection resolved badly
            #Tear down the loop
            self.loop.stop()
            self.loop.close()
            self.loop = None
            self.make_connection.clear()  # Clear so we can wait for it again
            return
        else:
            self.connect_event.set()  # Connection resolved
            self.connected = True  # Connection resolved well

        ### MAINTAINING the connection
        try:
            self.loop.run_forever()
        finally:
            #Tear down the loop
            self.loop.close()
            self.loop = None
            self.make_connection.clear()  # Clear so we can wait for it again

    def init_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.queue = asyncio.Queue()

    def run(self):
        #This thread will stay alive, even if connections are lost or dropped
        while True:
            self.make_connection.wait()
            self.init_loop()
            self.connect()  # this blocks
