import socket
import os


class FTPClient:
    def __init__(self, server_host, server_port):
        self.control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_host = server_host
        self.server_port = server_port
        self.CHUNK_SIZE = 1024 * 1024
        self.data_socket = None

    def connect_to_server(self):
        """Connect to the server."""
        try:
            self.control_socket.connect((self.server_host, self.server_port))
            print(self.control_socket.recv(1024).decode('utf-8'))
        except ConnectionRefusedError as e:
            print(f"Connection refused: {e}")
        except TimeoutError as e:
            print(f"Connection timed out: {e}")
        except Exception as e:
            print(f"Unexpected error in connect: {e}")

    def send_command(self, command):
        """Send a command to the server and receive its response."""
        try:
            self.control_socket.send(f"{command}\r\n".encode('utf-8'))
            response = self.control_socket.recv(1024).decode('utf-8')
            return response
        except BrokenPipeError as e:
            print(f"Broken pipe error: {e}")
        except ConnectionResetError as e:
            print(f"Connection reset error: {e}")
        except Exception as e:
            print(f"Unexpected error in send_command: {e}")
            return None

    def create_data_connection(self):
        """Establish a data connection for file transfer."""
        try:
            self.control_socket.send("PASV\r\n".encode('utf-8'))
            response = self.control_socket.recv(1024).decode('utf-8')
            print(response)

            if response.startswith("227"):
                try:
                    start = response.index('(') + 1
                    end = response.index(')')
                    parts = response[start:end].split(':')
                    data_port, data_ip = parts[1], parts[0]
                    return data_port, data_ip
                except (ValueError, IndexError) as e:
                    print(f"Error parsing PASV response: {e}")
                    return None

            return None
        except BrokenPipeError as e:
            print(f"Broken pipe error: {e}")
        except ConnectionResetError as e:
            print(f"Connection reset error: {e}")
        except Exception as e:
            print(f"Unexpected error in create_data_connection: {e}")
            return None
        
    def handle_retr(self, filepath):
        """Retrieve (download) a file from the server."""
        try:
            dataPort, dataIp = self.create_data_connection()
            if dataPort is None or dataIp is None:
                print("Failed to create data connection.")
                return

            try:
                data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                data_socket.connect((dataIp, int(dataPort)))
            except (socket.error, TypeError) as e:
                print(f"Error connecting data socket: {e}")
                return

            response = self.send_command(f"RETR {filepath}")
            print(response)
            if response.startswith("150"):  # File status okay; about to open data connection
                filename = os.path.basename(filepath)
                try:
                    with open(f"downloaded_{filename}", 'wb') as f:
                        while chunk := data_socket.recv(self.CHUNK_SIZE):
                            f.write(chunk)
                    data_socket.close()
                    print("File retrieved successfully.")
                    print(self.control_socket.recv(1024).decode('utf-8'))  # Read final server response
                except (IOError, socket.error) as e:
                    print(f"Error during file retrieval: {e}")
                    if 'data_socket' in locals():
                        data_socket.close()
            else:
                print(f"Server response error: {response}")
        except Exception as e:
            print(f"Unexpected error in retr: {e}")

    def handle_stor(self, filename, serverSideFilename):
        """Store (upload) a file to the server."""
        try:
            dataPort, dataIp = self.create_data_connection()
            if dataPort is None or dataIp is None:
                print("Failed to create data connection.")
                return

            try:
                data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                data_socket.connect((dataIp, int(dataPort)))
            except (socket.error, TypeError) as e:
                print(f"Error connecting data socket: {e}")
                return

            response = self.send_command(f"STOR {filename} {serverSideFilename}")
            print(response)
            if response.startswith("150"):  # File status okay; about to open data connection
                try:
                    with open(filename, 'rb') as f:
                        while chunk := f.read(self.CHUNK_SIZE):
                            data_socket.send(chunk)
                    data_socket.close()
                    print("File stored successfully.")
                    print(self.control_socket.recv(1024).decode('utf-8'))  # Read final server response
                except (IOError, socket.error) as e:
                    print(f"Error during file upload: {e}")
                    if 'data_socket' in locals():
                        data_socket.close()
            else:
                print(f"Server response error: {response}")
        except Exception as e:
            print(f"Unexpected error in stor: {e}")


    def handle_list(self,command):
        """List files in the server directory."""
        try:
            dataPort, dataIp = self.create_data_connection()
            if dataPort is None or dataIp is None:
                print("Failed to create data connection.")
                return

            try:
                data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                data_socket.connect((dataIp, int(dataPort)))
            except (socket.error, TypeError) as e:
                print(f"Error connecting data socket: {e}")
                return

            response = self.send_command(command)
            print(response)
            if response.startswith("150"):  # File status okay; about to open data connection
                try:
                    directory_listing = data_socket.recv(1024).decode('utf-8')
                    print("Directory contents:\n", directory_listing)
                except (socket.error, UnicodeDecodeError) as e:
                    print(f"Error during directory listing retrieval: {e}")
                finally:
                    data_socket.close()

                try:
                    print(self.control_socket.recv(1024).decode('utf-8'))  # Read final server response
                except (socket.error, UnicodeDecodeError) as e:
                    print(f"Error receiving final server response: {e}")
            else:
                print(f"Server response error: {response}")
        except Exception as e:
            print(f"Unexpected error in list_files: {e}")


    def command(self):
        
        
        while True:
            command = input(">").strip()
            
            if command == "QUIT":
                print(self.send_command("QUIT"))
                self.control_socket.close()
                break
            
            elif command.startswith("USER") or command.startswith("PASS"):
                print(self.send_command(command))
            
            elif command.startswith("LIST"):
                self.handle_list(command)
            
            elif command.startswith("RETR"):
                filename = command.split()[1]
                self.handle_retr(filename)
            
            elif command.startswith("STOR"):
                try:
                    filename = command.split()[1]
                    serverSideFilename = command.split()[2]
                    self.handle_stor(filename, serverSideFilename)
                except:
                    print("550 command is not recognized")

            elif command.startswith("DELE"):
                filename = command.split()[1]
                print(self.send_command(f"DELE {filename}"))
            
            elif command.startswith("MKD"):
                dirname = command.split()[1]
                print(self.send_command(f"MKD {dirname}"))
            
            elif command.startswith("RMD"):
                dirname = command.split()[1]
                print(self.send_command(f"RMD {dirname}"))
            
            elif command == "PWD":
                print(self.send_command("PWD"))
            
            elif command.startswith("CWD"):
                dirname = command.split()[1]
                print(self.send_command(f"CWD {dirname}"))
            
            elif command == "CDUP":
                print(self.send_command("CDUP"))

            else:
                print(self.send_command(command))
            
if __name__ == "__main__":
    # Predefined server IP and port
    server_ip = "127.0.0.1" # Replace with the actual server IP
    server_port = 2121 # Replace with the actual server port

    ftp_client = FTPClient(server_ip, server_port)
    ftp_client.connect_to_server()
    ftp_client.command()
