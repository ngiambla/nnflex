''' message_router.py: An abstraction to connect any devices together.

This class enables communication and data transfer between devices.

'''

from core.messaging import Message
from core.clock import ClockReference


class MessageQueue:
    ''' An object which implements a queue (specifically for messages) with a maximum capacity.
    '''
    def __init__(self, max_availability = 1):
        if max_availability <= 0:
            raise ValueError("A MessageQueue object MUST have at least 1 element")

        self._max_availability = max_availability
        self._queue = list()

    def queue(self, data):
        if len(self._queue) < self._max_availability:
            self._queue.append(data)
            return True
        return False

    def dequeue(self):
        if not self._queue:
            return None
        return self._queue.pop(0)


class MessageRouter:
    '''MessageRouter: An abstraction on how to connect and communicate between compute elements

    Notes:
        This can be used to interface between _any_ compute elements
        e.g., Memory, PEs, Tiles, etc.

    Args:
        system_clock_ref: The reference to the system clock.

    '''
    def __init__(self, system_clock_ref):
        self._message_queue_map = dict()
        if not isinstance(system_clock_ref, ClockReference):
            raise ValueError("system_clock_ref must be a ClockReference.")
        self._system_clock_ref = system_clock_ref


    def add_connection(self, device, queue_size = 1):
        '''add_connecton: Adds a device to this MessageRouter

        Notes:
            An Exception (ValueError) is raised if the compute_element already exists in the message_queue_map

        Args:
            device: A device to interface with
            queue_size: The number of can be waiting for the device.

        ''' 
        if device in self._message_queue_map:
            raise ValueError("Compute Element: "+str(device)+" already added.")

        self._message_queue_map[device] = MessageQueue(queue_size)


    def get_neighbours(self, requestor):
        '''get_neighbours: Fetches all compute elements connected to this MessageRouter

        Args:
            requestor: The compute element asking for it's neighbours

        Returns:
            The addressable compute elements as a set()
        '''         
        neighbours = set(self._message_queue_map.keys()) - set(requestor)
        return neighbours


    def send(self, message):
        '''send: Sends a Message from source to destination via the MessageRouter

        Notes:
            A ValueError can be raised if the requested destination is NOT on this MessageRouter.

        Args:
            message: The Message to transfer.

        Returns:
            True if the transmisson was successful, False if the router-queue for the device is full.
            If False is returned, the source device should stall on sending!
        '''
        if message.destination not in self._message_queue_map:
            raise ValueError("Requested Destination is not on this MessageRouter."+str(message.destination))

        if not isinstance(message, Message):
            raise ValueError("Cannot send a non-Message on a MessageRouter.")

        message.sent_clock = self._system_clock_ref.current_clock()

        return self._message_queue_map[message.destination].queue(message)


    def fetch(self, requestor):
        '''fetch: Fetches any message from the MessageRouter queue for the requesting dev

        Args:
            requestor: The device wondering if any messages are avail to process
            messages_to_process: The maximum number of messages the requestor CAN process.

        Returns:
            A Message if there are any in the requestor's queue, otherwise None will be returned.
        '''
        if requestor not in self._message_queue_map:
            raise ValueError("Requestor is not registered on this MessageRouter: "+str(requestor)+". Please add it to the MessageRouter.")

        # Fetch the message from the queue
        message = self._message_queue_map[requestor].dequeue()
        if message is not None:
            # Stamp the message, now that it's been received.
            message.recv_clock = self._system_clock_ref.current_clock()
        return message

