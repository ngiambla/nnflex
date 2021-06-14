''' Interconnect.py: An abstraction to connect any compute elements together.

This class enables communication and data xfer between compute elements.


'''
from core.compackets import MemWritePacket, MemReadPacket
from core.memory import Memory

class TransactionQueue:
    def __init__(self, max_availability = 1):
        if max_availability <= 0:
            raise ValueError("A transaction queue MUST have at least 1 element")
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

    def is_data_remaining(self):
        return False if not self._queue else True


class Interconnect:
    '''Interconnect: An abstraction on how to connect compute elements

    Notes:
        This can be used to interface between _any_ compute elements
        e.g., Memory, PEs, Tiles, etc.

    '''
    def __init__(self, system_clock_ref):
        self._transaction_queue_map = dict()
        self._system_clock_ref = system_clock_ref


    def add_connection(self, compute_element, queue_size = 1):
        '''add_connecton: Adds a compute element to this interconnect

        Notes:
            An Exception (ValueError) is raised if:
            (1) the compute_element already exists in the transaction_queue_map

        Args:
            compute_element: A compute element to interface with
            queue_size: The number of can be waiting for the compute_element.

        ''' 
        if compute_element in self._transaction_queue_map:
            raise ValueError("Compute Element: "+str(compute_element)+" already added.")

        self._transaction_queue_map[compute_element] = TransactionQueue(queue_size)


    def get_neighbours(self, requestor):
        '''get_neighbours: Fetches all compute elements connected to this interconnect

        Args:
            requestor: The compute element asking for it's neighbours

        Returns:
            The addressable compute elements as a set()
        '''         
        neighbours = set(self._transaction_queue_map.keys()) - set(requestor)
        return neighbours

    def is_neighbour_free(self, neighbour):
        if neighbour not in self._transaction_queue_map:
            raise ValueError("Requested Neighbour is not on this interconnect."+str(neighbour))

        return self._transaction_queue_map[neighbour].is_data_remaining()

    def send(self, packet):
        '''send_to: Sends a packet from source to destination via the interconnect

        Notes:
            A ValueError can be raised if either:
            (1) A memory packet is sent to a non memory device
            (2) The requested destination is NOT on this interconnect.

        Args:
            packet: The data packet (MemWrite,MemRead, Data) to XFER.

        Returns:
            True if the transmisson was successful, False if the queue for the device is full.
            If False is returned, the source device should stall.
        '''
        if packet.destination_device() not in self._transaction_queue_map:
            raise ValueError("Requested Destination is not on this interconnect."+str(packet.destination_device()))

        packet.stamp_sent(self._system_clock_ref.current_clock())

        return self._transaction_queue_map[packet.destination_device()].queue(packet)


    def get_packet(self, requestor):
        '''get_packet: Fetches any packet from the interconnect queue for the requesting dev

        Args:
            requestor: The device wondering if any packets are avail to process
            packets_to_process: The maximum number of packets the requestor CAN process.

        Returns:
            A list with any packets available for the requestor. An empty list will be returned
            if there are no requests.
        '''
        if requestor not in self._transaction_queue_map:
            raise ValueError("Requestor is not registered on this interconnect. Please add it to the interconnect.")

        # Fetch the packet from the queue
        packet = self._transaction_queue_map[requestor].dequeue()
        if packet is not None:
            # Stamp the packet, now that it's been received.
            packet.stamp_received(self._system_clock_ref.current_clock())
        return packet

    def whats_on_the_interconnect(self):
        for device in self._transaction_queue_map:
            print("+= Interconnect["+str(self)+"]: "+str(device)+" => "+str(self._transaction_queue_map[device]._queue))