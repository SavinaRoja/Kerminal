# encoding: utf-8

from .telemachus_api import plotables

import asyncio
import collections
import json
import logging
import threading
import queue
import time

from autobahn.asyncio.websocket import WebSocketClientProtocol,\
                                       WebSocketClientFactory

log = logging.getLogger('kerminal.communication')
log.setLevel(logging.DEBUG)

#Initialize all plotable variables in the dict
global LIVE_DATA
LIVE_DATA = {k: 0 for k in plotables}

global MSG_QUEUE
MSG_QUEUE = queue.Queue()


class OrderedSet(collections.MutableSet):
    def __init__(self, iterable=None):
        self.end = end = []
        end += [None, end, end]         # sentinel node for doubly linked list
        self.map = {}                   # key --> [key, prev, next]
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.map)

    def __contains__(self, key):
        return key in self.map

    def add(self, key):
        if key not in self.map:
            end = self.end
            curr = end[1]
            curr[2] = end[1] = self.map[key] = [key, curr, end]

    def discard(self, key):
        if key in self.map:
            key, prev, next = self.map.pop(key)
            prev[2] = next
            next[1] = prev

    def __iter__(self):
        end = self.end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self.end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def pop(self, last=True):
        if not self:
            raise KeyError('set is empty')
        key = self.end[1][0] if last else self.end[2][0]
        self.discard(key)
        return key

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return set(self) == set(other)


class SubscriptionManager(object):
    """
    Basically a set of semaphores, I'm still refining this concept...
    """
    def __init__(self, queue):
        self.map = {}
        self.queue = queue

    def __len__(self):
        return len(self.map)

    def __contains__(self, key):
        return key in self.map

    def __iter__(self):
        for i in self.map:
            yield i

    def add(self, key):
        if key in self.map:  # Seen before
            if self.map[key] == 0:
                self.queue.put(('+', key))
            self.map[key] += 1
        else:  # Not seen before
            self.queue.put(('+', key))
            self.map[key] = 1

    #Naming this "drop" for now to help interfaces straight in my head
    def drop(self, key):
        if key in self.map:  # Seen before
            self.map[key] -= 1
            if self.map[key] == 0:
                self.queue.put(('-', key))
        else:
            pass  # Can't drop what you haven't seen


global DATA_LOG_ON, DATA_LOG_VARS, DATA_LOG_FILE
DATA_LOG_ON = False
DATA_LOG_VARS = OrderedSet(['t.universalTime',
                            'v.missionTime',
                            'sys.time'])
DATA_LOG_FILE = 'kerminaldata.csv'


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
        self.data_log = None  # This will be None, or an open file

    def onOpen(self):
        log.debug('WebSocket connect open.')

        #Below here are things that should be executed once at each connection
        self.send_json_message({'+': ['v.name',
                                      'p.paused',
                                      't.universalTime',
                                      'v.missionTime'],
                                #'rate': 1000,
                                })

        @asyncio.coroutine
        def consume_queue():
            global MSG_QUEUE
            composition = {}
            while True:
                try:
                    item = MSG_QUEUE.get_nowait()
                except queue.Empty:
                    if composition:
                        self.send_json_message(composition)
                        composition = {}
                    #The sleep time here could be changed, or I could set this
                    #up to be signaled by an event
                    yield from asyncio.sleep(0.1)
                else:
                    try:
                        action, key = item
                    except ValueError:  # If the item is a dict, send it on
                        self.send_json_message(item)
                    else:
                        if action in composition:
                            composition[action].append(key)
                        else:
                            composition[action] = [key]
                        log.debug(composition)

        asyncio.Task(consume_queue())

    def onMessage(self, payload, isBinary):
        #The Telemachus server should never send binary data, but just in case
        if isBinary:
            log.debug('Received binary data: {0}'.format(payload))
        else:
            #Telemachus server should always send text as json
            try:
                msg = json.loads(payload.decode('utf-8'))
            except Exception as e:  # In case of bad encoding or other problems
                log.exception(e)
                log.debug('Could not parse: {0}'.format(payload))
                return
            else:
                msg['sys.time'] = time.time()
                log.debug('Message Received: {0}'.format(msg))
            #The client subscribes to p.paused on connection, it should always
            #be present and is exempt from subscription management
            #When the game is paused, Kerminal will act as though it has not
            #received the message.
            if not msg['p.paused']:
                global LIVE_DATA
                LIVE_DATA.update(msg)
                #Logging stuff
                global DATA_LOG_ON, DATA_LOG_VARS, DATA_LOG_FILE
                if DATA_LOG_ON:  # Logging is enabled
                    #If self.data_log is None, but DATA_LOG_ON is True, then
                    #logging was just enabled and we need to open the file and
                    #write the headers
                    if self.data_log is None:
                        self.data_log = open(DATA_LOG_FILE, 'a', -1)
                        self.data_log.write(';'.join(DATA_LOG_VARS) + '\n')
                    #Write the log vars to the file
                    self.data_log.write(';'.join([str(LIVE_DATA[v]) for v in DATA_LOG_VARS]) + '\n')
                else:
                    if self.data_log is not None:
                        self.data_log.close()
                        self.data_log = None

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

        global DATA_LOG_VARS
        self.data_log_vars = DATA_LOG_VARS

        #global SUBSCRIPTION_SET
        self.subscription_manager = SubscriptionManager(MSG_QUEUE)

    @property
    def data_log_on(self):
        global DATA_LOG_ON
        return DATA_LOG_ON

    @data_log_on.setter
    def data_log_on(self, val):
        global DATA_LOG_ON
        DATA_LOG_ON = val

    @property
    def data_log_file(self):
        global DATA_LOG_FILE
        return DATA_LOG_FILE

    @data_log_file.setter
    def data_log_file(self, val):
        global DATA_LOG_FILE
        DATA_LOG_FILE = val

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
        except Exception as e:
            log.exception(e)
        finally:
            #Tear down the loop
            self.loop.close()
            self.loop = None
            self.make_connection.clear()  # Clear so we can wait for it again
            self.connected = False
            #Reset important connection state variables
            self.data_log_vars = OrderedSet(['t.universalTime',
                                             'v.missionTime',
                                             'sys.time'])

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
