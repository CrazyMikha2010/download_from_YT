# This script implements a simple proxy server that fragments data to bypass Deep Packet Inspection (DPI).

import random
import asyncio

# getting blocked domains
BLOCKED = [line.rstrip().encode() for line in open('blacklist.txt', 'r', encoding='utf-8')]
TASKS = []

# launch socket server
async def main(host, port):

    server = await asyncio.start_server(new_conn, host, port)
    await server.serve_forever()

# reads from reader and writes to writer until EOF (end of file) or connection close
async def pipe(reader, writer):

    while not reader.at_eof() and not writer.is_closing():
        try:
            writer.write(await reader.read(1500))
            await writer.drain()
        except:
            break

    writer.close()

# processes new connection
async def new_conn(local_reader, local_writer):

    # read http request
    http_data = await local_reader.read(1500)

    try:
        type, target = http_data.split(b"\r\n")[0].split(b" ")[0:2]
        host, port = target.split(b":")
    except:
        local_writer.close()
        return

    # if type of request is not CONNECT close the connection
    if type != b"CONNECT":
        local_writer.close()
        return

    # send answer to the client
    local_writer.write(b'HTTP/1.1 200 OK\n\n')
    await local_writer.drain()

    try:
        remote_reader, remote_writer = await asyncio.open_connection(host, port)
    except:
        local_writer.close()
        return

    if port == b'443':
        await fragemtn_data(local_reader, remote_writer)

    # add tasks to pipe data between local and remote connections
    TASKS.append(asyncio.create_task(pipe(local_reader, remote_writer)))
    TASKS.append(asyncio.create_task(pipe(remote_reader, local_writer)))

# fragments data to bypass DPI (Deep Packet Inspection)
async def fragemtn_data(local_reader, remote_writer):

    # read title and data
    head = await local_reader.read(5)
    data = await local_reader.read(1500)
    parts = []

    # if data does not contain blocked domains, send it as is
    if all([data.find(site) == -1 for site in BLOCKED]):
        remote_writer.write(head + data)
        await remote_writer.drain()

        return

    # if data contains blocked domains, fragment it
    while data:
        part_len = random.randint(1, len(data))
        parts.append(bytes.fromhex("1603") + bytes([random.randint(0, 255)]) + int(
            part_len).to_bytes(2, byteorder='big') + data[0:part_len])

        data = data[part_len:]

    remote_writer.write(b''.join(parts))
    await remote_writer.drain()

if __name__ == "__main__":
    asyncio.run(main(host='127.0.0.1', port=8881))
