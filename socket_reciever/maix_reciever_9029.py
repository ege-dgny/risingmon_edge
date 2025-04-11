import socket
import ntcore
import time

# Initialize NetworkTables instance
inst = ntcore.NetworkTableInstance.getDefault()
inst.startClient4("vision_client")
inst.setServerTeam(9029)
#inst.startDSClient()  # Recommended if running on DS computer

# Get the table to publish to
table = inst.getTable("Vision")

# Socket server setup
server_ip = '0.0.0.0'
server_port = 9029

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((server_ip, server_port))
server_socket.listen(1)

print(f"Server listening on {server_ip}:{server_port}")

while True:
    client_socket, client_address = server_socket.accept()
    print(f"Connection from {client_address}")

    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break

            decoded = data.decode().strip()
            print(f"Received: {decoded}")

            try:
                x_str, y_str = decoded.split(',')
                x, y = int(x_str), int(y_str)

                # Publish to NetworkTables
                table.putNumber("target_x", x)
                table.putNumber("target_y", y)

            except ValueError:
                print("Malformed data received. Skipping.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()
        print(f"Connection with {client_address} closed")