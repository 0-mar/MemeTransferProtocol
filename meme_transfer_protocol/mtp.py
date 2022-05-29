import base64
import socket
import time

import pynetstring

BUFFER_SIZE = 4096


class MTPConnection:
    """
    This class represents a MTP connection.

    It is divided into 3 phases (methods) - initiation phase, data channel phase and end phase.
    """

    def __init__(self, host: str = "159.89.4.84", port: int = 42070, nick: str = "Nautilus",
                 meme_path: str = "memik.png",
                 password: str = "12345", description: str = "( ͡° ͜ʖ ͡°)", is_nsfw: str = "false"):
        self.host = host
        self.port = port
        self.nick = nick
        self.meme_path = meme_path
        self.password = password
        self.description = description
        self.is_nsfw = is_nsfw

        self.decoder = pynetstring.Decoder()

        self.total_data_len = 0
        self.data_channel_port = -1

        self.security_token = ""
        self.security_token2 = ""

        self.successful = False

        self.phase_one()

    def phase_one(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as soc:
            soc.connect((self.host, self.port))

            self.initiate_connection(soc)
            self.choose_nick(soc)

            self.phase_two()
            self.phase_three(soc)

    def phase_two(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, int(self.data_channel_port)))

            request = self.initiate_data_channel(s)

            while request.startswith("S REQ"):
                command = self.get_request_data(request, s)
                data_to_send = None

                if command == "meme":
                    data_to_send = base64.b64encode(open(self.meme_path, "rb").read()).decode("ascii")
                elif command == "description":
                    data_to_send = self.description
                elif command == "isNSFW":
                    data_to_send = self.is_nsfw
                elif command == "password":
                    data_to_send = self.password
                else:
                    raise MTPError("E Invalid command", s)

                request = self.send_data(s, data_to_send)
            else:
                self.security_token2 = self.get_request_data(request, s)

                if self.security_token2 == self.security_token:
                    raise MTPError("E Security tokens cannot be the same!", s)

                # print("Konec prenosu na DataChannelu | " + request)

    def phase_three(self, soc: socket.socket):
        self.check_data_len(soc)
        self.end_connection(soc)

    # -------------------------------------------------------------------------------- #
    #                    BASIC METHODS USED IN ALL PHASES                              #
    # -------------------------------------------------------------------------------- #
    def recv_timeout(self, the_socket, timeout=3):
        # make socket non blocking
        the_socket.setblocking(0)

        # total data partwise in an array
        total_data = []

        # beginning time
        begin = time.time()
        while True:
            # if you got some data, then break after timeout
            if total_data and time.time() - begin > timeout:
                break

            # if you got no data at all, wait a little longer
            elif time.time() - begin > timeout * 10:
                # print("Server neodpovida")
                raise MTPError("E Server does not respond", the_socket)

            # recv something
            try:
                data = the_socket.recv(BUFFER_SIZE)
                if data:
                    total_data.append(data)
                    # change the beginning time for measurement
                    begin = time.time()
                else:
                    # sleep for sometime to indicate a gap
                    time.sleep(0.1)
            except:
                pass

        return total_data

    def get_all_data(self, soc: socket.socket):
        data = self.recv_timeout(soc)
        decoded_list = []

        for item in data:
            decoded_list.extend(self.decoder.feed(item))

        return decoded_list

    def communicate(self, soc: socket.socket, message_to_send: str):
        if message_to_send:
            msg = pynetstring.encode(message_to_send)
            soc.sendall(msg)
            # print("\nOdeslana zprava: " + message_to_send)

        decoded_list = self.get_all_data(soc)
        # print("Prichozi data jsou: " + str(decoded_list))

        return decoded_list

    # -------------------------------------------------------------------------------- #
    #                           FIRST PHASE METHODS                                    #
    # -------------------------------------------------------------------------------- #

    def initiate_connection(self, soc: socket.socket):
        received_data = self.communicate(soc, "C MTP V:1.0")

        if received_data[0].decode() != "S MTP V:1.0":
            # print(decoded_list[0].decode())
            raise MTPError("E Server did not establish connection", soc)

    def choose_nick(self, soc: socket.socket):
        received_data = self.communicate(soc, "C " + self.nick)

        token_msg = received_data[0].decode()
        port_msg = received_data[1].decode()

        if not token_msg.startswith("S "):
            raise MTPError("E Invalid token message", soc)

        else:
            lst = token_msg.split(sep=" ")
            self.security_token = lst[1]

        if not port_msg.startswith("S "):
            raise MTPError("E Invalid port message", soc)

        else:
            lst = port_msg.split(sep=" ")
            self.data_channel_port = lst[1]

    # -------------------------------------------------------------------------------- #
    #                           SECOND PHASE METHODS                                   #
    # -------------------------------------------------------------------------------- #

    def initiate_data_channel(self, soc: socket.socket):
        received_data = self.communicate(soc, "C " + self.nick)

        lst = received_data[0].decode().split(sep=" ")
        new_token = lst[1]

        if new_token != self.security_token:
            # print(new_token + " != " + self.security_token)
            raise MTPError("E Security tokens are not the same!", soc)

        request = received_data[1].decode()
        # print("pozadavek serveru je: " + request)

        return request

    #       *--*--*--*--* HELPER METHODS *--*--*--*--*

    def send_data(self, soc: socket.socket, data_to_encode: str):
        received_data = self.communicate(soc, "C " + data_to_encode)
        self.total_data_len += int(self.get_request_data(received_data[0].decode(), soc))

        next_request = received_data[1].decode()

        return next_request

    def get_request_data(self, req: str, soc: socket.socket):
        data = ""
        try:
            data = req.split(sep=" ")[1].split(sep=":")[1]
        except IndexError:
            raise MTPError("E Invalid request message format", soc)

        return data

    # -------------------------------------------------------------------------------- #
    #                           THIRD PHASE METHODS                                    #
    # -------------------------------------------------------------------------------- #

    def check_data_len(self, soc: socket.socket):
        received_data = self.communicate(soc, "")
        data_len_msg = received_data[0].decode()

        if not data_len_msg.startswith("S "):
            raise MTPError("E Invalid data length message", soc)

        lst = data_len_msg.split(sep=" ")
        data_len = int(lst[1])

        if not self.total_data_len == data_len:
            raise MTPError("E Data length is not the same (" + str(self.total_data_len) + "(client) vs " +
                           str(data_len) + "(server))", soc)

    def end_connection(self, soc: socket.socket):
        received_data = self.communicate(soc, "C " + self.security_token2)

        if received_data[0].decode() != "S ACK":
            raise MTPError("E Server did not end connection properly", soc)

        self.successful = True
        # print("SPOJENI USPESNE UKONCENO")


class MTPError(Exception):
    """
    Represents errors that happen during the MTP.

    :param message: Error message that will be sent to the server
    :param sock: Socket which will be used for sending
    """
    def __init__(self, message, sock: socket.socket):
        self.message = message
        self.sock = sock

        msg = pynetstring.encode(message)
        sock.sendall(msg)

        # print("ODESLANA ZPRAVA NA SERVER " + message)
