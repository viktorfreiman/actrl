import asyncio
import socket
import sys
import os
import time

PORT = 8000
CHUNK_LIMIT = 50
RESPONSE = (
    "HTTP/1.1 {status} {status_msg}\r\nConnection: closed\r\n\r\n{html}"
)


class AudacityException(Exception):
    pass


def parse_request(request_str):
    part_one, part_two = request_str.split("\r\n\r\n")
    http_lines = part_one.split("\r\n")
    method, url, _ = http_lines[0].split(" ")
    # TODO: catch this with exception
    if method != "GET":
        status, status_msg = 405, "Not allowed"
    else:
        status, status_msg = 200, "OK"

    return status, status_msg, url


def audacity_cmd(cmd):
    if sys.platform == "win32":
        write_pipe_name = "\\\\.\\pipe\\ToSrvPipe"
        read_pipe_name = "\\\\.\\pipe\\FromSrvPipe"
        eol = "\r\n\0"
    else:
        write_pipe_name = "/tmp/audacity_script_pipe.to." + str(os.getuid())
        read_pipe_name = "/tmp/audacity_script_pipe.from." + str(os.getuid())
        eol = "\n"

    # Allow a little time for connection to be made.
    time.sleep(0.001)

    if not os.path.exists(read_pipe_name):
        raise AudacityException(
            read_pipe_name + " does not exist. "
            "Ensure Audacity is running and mod-script-pipe is set to "
            "Enabled in the Preferences window."
        )

    write_pipe = open(write_pipe_name, "w")
    read_pipe = open(read_pipe_name)

    write_pipe.write(cmd + eol)
    write_pipe.flush()

    response = ""
    line = ""
    while True:
        response += line
        line = read_pipe.readline()
        if line == "\n" and len(response) > 0:
            break

    # Allow a little time for connection to be made.
    time.sleep(0.001)

    # sys.stdout.write(response + '\n')  # DEBUG
    if "BatchCommand finished: Failed!" in response:
        raise AudacityException(response)

    return response


async def load_response(path):
    # response = f"Hello world! {path=}"
    # right now we only support one word commands
    # curl localhost:8000/cmd
    cmd = path[1:]
    response = audacity_cmd(cmd)

    return response


async def build_response(request):
    status, status_msg, url = parse_request(request)
    html = await load_response(url)
    response = RESPONSE.format(status=status, status_msg=status_msg, html=html)
    return response.encode("utf-8")


async def read_request(client):
    request = ""
    while True:
        chunk = (await loop.sock_recv(client, CHUNK_LIMIT)).decode("utf8")
        request += chunk
        if len(chunk) < CHUNK_LIMIT:
            break

    return request


async def handle_client(client):
    request = await read_request(client)
    response = await build_response(request)
    await loop.sock_sendall(client, response)
    client.close()


async def run_server(selected_server):
    while True:
        client, _ = await loop.sock_accept(selected_server)
        loop.create_task(handle_client(client))


if __name__ == "__main__":
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("localhost", PORT))
    server.listen(1)
    server.setblocking(False)

    loop = asyncio.get_event_loop()
    try:
        print(f"Server started on port {PORT}")
        loop.run_until_complete(run_server(server))
    except KeyboardInterrupt:
        server.close()
        print("Server stopped")
