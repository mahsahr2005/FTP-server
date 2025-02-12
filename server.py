import socket
import os
import random
import random
# import stat
from datetime import datetime
import json
# import shutil


class FTPServer:
    def __init__(self, host, port):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        self.client_socket = None
        self.client_address = None
        # self.username = None
        self.current_directory = os.getcwd()
        self.CHUNK_SIZE = 1024 * 1024 # 1 MB chunks
        self.data_socket = None
        # self.permissions = {}  # To store the current user's permissions
        self.current_user = None   # To store the logged-in username
        self.json_file_path = "/Users/smm/Uni/T5/Network/Prj/phase-02-SMM-JUJU/users.json"
        # self.privilege_json = self.load_user_data()

    def load_user_data(self):
        try:
            with open(self.json_file_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print("User data file not found. Ensure 'users.json' is present.")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from the user data file: {e}")
            return {}
        except Exception as e:
            print(f"Unexpected error in load_user_data: {e}")
            return {}
        # with open(self.json_file_path, "r") as f:

        #     return json.load(f)

    def add_permission(self, user_name, command):
        
        # add the file name to the path
        admin = "admin"
        user_to_update = user_name
        new_file = command.split(' ')[2]
        # new_permission = self.current_directory + f'/{created_file_name}'
        new_permission = self.resolve_path(new_file)
        new_value = ["read","write","delete"]

        # Read the existing JSON data
        # try:
        #     with open(self.json_file_path, 'r') as file:
        #         data = json.load(file)  # Load the existing data
        # except FileNotFoundError:
        #     print("Error: JSON file not found.")
        #     data = None
        
        data = self.load_user_data()

        if data:
            # Check if the user exists in the permissions section
            if user_to_update in data["user_permissions"]:
                # Add the new permission to the user's permissions
                data["user_permissions"][user_to_update][new_permission] = new_value
                if user_to_update != admin:
                    # Add the new permission to admin permission
                    data["user_permissions"][admin][new_permission] = new_value

                # Write the updated data back to the file
                with open(self.json_file_path, 'w') as file:
                    json.dump(data, file, indent=4)
                    # print(f"Permission '{new_permission}' for user '{user_to_update}' added with value {new_value}!")
            # else:
            #     print(f"User '{user_to_update}' does not exist in the JSON file.")

    def has_privilege(self, username, file_path, privilege):
        try:
            if username == "admin":
                return True  # Admin has all privileges

            if username:
                try:
                    user = self.get_user_data(username)
                    file_privileges = user.get("permissions", {})
                    allowed_privileges = file_privileges.get(file_path, [])
                    return privilege in allowed_privileges
                except KeyError as e:
                    print(f"KeyError in has_privilege: {e}")
                    return False
                except Exception as e:
                    print(f"Error in has_privilege: {e}")
                    return False

            return False
        except Exception as e:
            print(f"Unexpected error in has_privilege: {e}")
            return False
        # if username == "admin":
        #     return True  # Admin has all privileges
        # # user = privilege_json.get(username)
        # if username:
        #     user = self.get_user_data(username)
        #     file_privileges = user.get("permissions", {})
        #     allowed_privileges = file_privileges.get(file_path, [])
        #     return privilege in allowed_privileges
        #     # return allowed_privileges
        # return False

    def get_user_data(self, username):
        try:
            privilege_json = self.load_user_data()
            # Access user information and permissions
            user_info = privilege_json["users"][username]
            user_permissions = privilege_json["user_permissions"][username]
            # Combine user info and permissions
            user_data = {
                # "username" : user_info["name"],
                "user_info": user_info,
                "permissions": user_permissions
            }
            return user_data
        except KeyError:
            return ""
 
    def delete_permission(self, file_path):
        # Permission to delete
        permission_to_delete = str(f"{file_path}")

        # Load the JSON file
        # try:
        #     with open(self.json_file_path, 'r') as file:
        #         data = json.load(file)  # Load JSON into a dictionary
        # except FileNotFoundError:
        #     print("Error: JSON file not found.")
        #     data = None

        data = self.load_user_data()
        
        if data:
        # Access user_permissions and remove the specific permission for all users
            user_permissions = data.get("user_permissions", {})
            for user, permissions in user_permissions.items():
                if permission_to_delete in permissions:
                    del permissions[permission_to_delete]
                    print("")
                else:
                    print("")

            # Save the updated data back to the JSON file
            with open(self.json_file_path, 'w') as file:
                json.dump(data, file, indent=4)

        else:
            print("No changes made due to missing or invalid data.")
      
    def resolve_path(self,directory_name):
        try:
            # Check if the path is absolute
            if os.path.isabs(directory_name):
                # It's already an absolute path, return it as-is
                resolved_path = os.path.abspath(directory_name)
            else:
                # It's a relative path, resolve it using the current directory
                resolved_path = os.path.abspath(os.path.join(self.current_directory, directory_name))

            return resolved_path
        except Exception as e:
            print(f"Error in resolving path for '{directory_name}': {e}")
            return None

        # # Check if the path is absolute
        # if os.path.isabs(directory_name):
        #     # It's already an absolute path, return it as-is
        #     resolved_path = os.path.abspath(directory_name)
        # else:
        #     # It's a relative path, resolve it using the current directory
        #     resolved_path = os.path.abspath(os.path.join(self.current_directory, directory_name))
    
        # return resolved_path

    def start(self):
        try:
            print("FTP Server started. Waiting for connections...")
            self.client_socket, self.client_address = self.server_socket.accept()
            print(f"Connection established with {self.client_address}")
            self.client_socket.send(b"220 FTP Server Ready\r\n")
            self.handle_commands()
        except Exception as e:
            print(f"Error in start server: {e}")
            if self.client_socket:
                self.client_socket.close()

    def handle_commands(self):

        while True:
            command = self.client_socket.recv(1024).decode('utf-8').strip()
                
            print(f"Received command: {command}")
                
            if command.startswith('USER'):
                self.ifUser = False
                user_name = command.split(' ')[1]
                self.handle_user(self.client_socket,user_name)
                
            elif command.startswith('PASS'):
                password = command.split(' ')[1]
                self.handle_pass(self.client_socket,self.ifUser,user_name,password)
                
            elif command.startswith('PASV'):
                self.data_socket = self.create_data_connection(self.client_socket)
                
            elif command.startswith('LIST'):

                if len(command.split()) > 1:
                    path = command.split(' ', 1)[1]
                    self.handle_list_with_path(self.client_socket, self.data_socket, path)
                else:
                    self.handle_list(self.client_socket, self.data_socket)
                        
            elif command.startswith('RETR'):
                file_name = command.split(' ')[1]
                self.handle_retr(self.client_socket, self.data_socket, file_name)
                
            elif command.startswith('STOR'):
                self.handle_stor(self.client_socket, self.data_socket, command)
                
            elif command.startswith('DELE'):
                file_name = command.split(' ')[1]
                self.handle_dele(file_name)
                
            elif command.startswith('MKD'):
                directory_name = command.split(' ')[1]
                self.handle_mkd(directory_name)
                
            elif command.startswith('RMD'):
                directory_name = command.split(' ')[1]
                self.handle_rmd(directory_name)
                
            elif command.startswith('PWD'):
                self.handle_pwd()
                
            elif command.startswith('CWD'):
                directory_name = command.split(' ')[1]
                self.handle_cwd(directory_name)
                
            elif command.startswith('CDUP'):
                self.handle_cdup()
                
            elif command == 'QUIT':
                self.client_socket.send(b"221 Goodbye\r\n")
                self.client_socket.close()
                break
                
            else:
                self.client_socket.send(b"500 Command not recognized\r\n")
        
    def create_data_connection(self, control_socket):
        try:
            data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Bind to an available port
            server_ip = control_socket.getsockname()[0]  # Get server's IP address
            data_port = random.randint(20000, 30000)  # Choose a random port in a safe range

            try:
                data_socket.bind((server_ip, data_port))
            except OSError as e:
                print(f"Error binding data socket to {server_ip}:{data_port} - {e}")
                control_socket.send(b"421 Service not available, closing control connection.\r\n")
                return None

            try:
                data_socket.listen(1)  # Ready to accept one connection
            except OSError as e:
                print(f"Error listening on data socket - {e}")
                control_socket.send(b"421 Service not available, closing control connection.\r\n")
                return None

            # Send PASV response to the client
            try:
                pasv_response = f"227 Entering Passive Mode ({server_ip}:{data_port})\r\n"
                control_socket.send(pasv_response.encode('utf-8'))
            except Exception as e:
                print(f"Error sending PASV response - {e}")
                control_socket.send(b"421 Service not available, closing control connection.\r\n")
                return None

            return data_socket

        except Exception as e:
            print(f"Error in create_data_connection: {e}")
            return None

        # data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
        # # Bind to an available port
        # server_ip = control_socket.getsockname()[0]  # Get server's IP address
        # data_port = random.randint(20000, 30000)    # Choose a random port in a safe range
        # data_socket.bind((server_ip, data_port))
        # data_socket.listen(1)  # Ready to accept one connection

        # # Send PASV response to the client
        # pasv_response = f"227 Entering Passive Mode ({server_ip}:{data_port})\r\n"
        # control_socket.send(pasv_response.encode('utf-8'))

        # return data_socket

    def handle_user(self, client_socket, user_name):
        try:
            if user_name:
                user_data = self.get_user_data(user_name)
                # name_of_users = user_data.get("users", {})
                # users_exists = name_of_users.get(user_name,[])
                if user_data:
                    self.current_user = user_name
                    self.ifUser = True
                    client_socket.send(b"331 Username okay, need password\r\n")
                else:
                    client_socket.send(b"530 User not found\r\n")
        except:   
            client_socket.send(b"530 Invalid input. Try again\r\n")

    def handle_pass(self, client_socket, ifUser, user_name, password):
        try:
            if ifUser:
                user_data = self.get_user_data(user_name)
                pass_of_user = user_data.get("user_info",{})
                # pass_match = pass_of_users.get(user_name,[])
                if password in pass_of_user:
                    client_socket.send(b"230 User logged in, proceed\r\n")
                else:
                    client_socket.send(b"530 Incorrect password\r\n")
            else:
                client_socket.send(b"503 Enter username first\r\n")
        except:
            client_socket.send(b"503 Bad sequence of commands\r\n")

    def handle_list_with_path(self, control_socket, data_socket, path):
        """Handles the LIST command with a specified path."""
        try:

            # Check if the path exists and is a directory
            if not os.path.exists(path):
                control_socket.send(f"550 {path}: No such file or directory.\r\n".encode('utf-8'))
                return
            if not os.path.isdir(path):
                control_socket.send(f"550 {path} is not a directory.\r\n".encode('utf-8'))
                return

            # Get the directory contents
            entries = os.listdir(path)
            response = []
            for entry in entries:
                entry_path = os.path.join(path, entry)
                stats = os.stat(entry_path)
                # perms = self.format_permissions(stats.st_mode)
                n_links = stats.st_nlink
                size = stats.st_size
                mtime = datetime.fromtimestamp(stats.st_mtime).strftime("%b %d %H:%M")
                # response.append(f"{perms} {n_links} user group {size} {mtime} {entry}")
                response.append(f"{n_links} user group {size} {mtime} {entry}")

            # Notify client that transfer is starting
            control_socket.send(b"150 Here comes the directory listing.\r\n")

            # Open a data connection
            client_socket, client_address = data_socket.accept()
            print(f"Data connection established with {client_address}")
        
            # Send the directory listing
            for line in response:
                client_socket.send(f"{line}\r\n".encode('utf-8'))

            # Close the data connection and notify the client
            client_socket.close()
            control_socket.send(b"226 Directory send okay.\r\n")

        except Exception as e:
            # Handle any errors
            control_socket.send(f"550 Error: {str(e)}\r\n".encode('utf-8'))

    def handle_list(self, control_socket, data_socket):

        control_socket.send(b"150 Opening data connection.\r\n")
        directory_contents = os.listdir(self.current_directory)  # Now listing the current directory
        listing = ""
        for item in directory_contents:
            item_stat = os.stat(item)
            # permissions = self.format_permissions(item_stat.st_mode)
            file_size = item_stat.st_size
            creation_time = datetime.fromtimestamp(item_stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
            # listing += f"{permissions} {file_size:10} {creation_time} {item}\r\n"
            listing += f"{file_size:10} {creation_time} {item}\r\n"

        client_socket, client_address = data_socket.accept()
        print(f"Data connection established with {client_address}")
        try:
            client_socket.send(listing.encode('utf-8'))
        except Exception as e:
            print(f"Error during listing transfer: {e}")
        finally:
            client_socket.close()

        control_socket.send(b"226 Transfer complete.\r\n")
 
    def handle_retr(self, control_socket, data_socket, file_name):
        
        """Handles the RETR command to send a file to the client."""
        
        if_allowed = self.has_privilege(self.current_user, file_name, 'read')
        
        if(if_allowed == False):
            control_socket.send(b"550 Permission denied: You cannot download this file.\r\n")
            return
        
        
        # Check if the file exists
        if not os.path.isfile(file_name):
            error_message = "550 File not found.\r\n"
            control_socket.send(error_message.encode('utf-8'))
            return

        # Notify client that file transfer is starting
        control_socket.send(b"150 Opening data connection.\r\n")

        #  Accept the client connection on the data socket
        client_socket, client_address = data_socket.accept()
        print(f"Data connection established with {client_address}")

        #  Send the file content
        try:
            with open(file_name, 'rb') as file:
                while chunk := file.read(1024):
                    client_socket.send(chunk)
            #  Notify client that transfer is complete
            control_socket.send(b"226 Transfer complete.\r\n")
        except Exception as e:
            print(f"Error during file transfer: {e}")
        finally:
            client_socket.close()

    def handle_stor(self, control_socket, data_socket, command):
        
        file_name = command.split()[2]
        file_path = self.resolve_path(file_name)
        
        file_to_access = command.split()[1]
        if_allowed = self.has_privilege(self.current_user, file_to_access, "write")

        if (if_allowed == False):
            control_socket.send(b"550 Permission denied: You cannot upload this file.\r\n")
            return


        # Notify client that the upload is starting
        control_socket.send(b"150 Opening data connection.\r\n")

        # Accept the client connection on the data socket
        client_socket, client_address = data_socket.accept()
        print(f"Data connection established with {client_address}")

        # Receive the file content and save it
        try:
            with open(file_path, 'wb') as file:
                while True:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    file.write(data)

            self.add_permission(self.current_user, command)
            
            control_socket.send(b"226 Transfer complete.\r\n")
        except PermissionError:
            control_socket.send(f"550 '{file_path}': Permission denied.\r\n".encode('utf-8'))
        except Exception as e:
            print(f"Error during file upload: {e}")
            control_socket.send(b"550 Error writing file.\r\n")
        finally:
            client_socket.close()

    def handle_dele(self, file_name):
        
        file_path = self.resolve_path(file_name)
        if_allowed = self.has_privilege(self.current_user, file_path, "delete")

        if (if_allowed == False):
            self.client_socket.send(b"550 Permission denied: You cannot delete this file.\r\n")
            return

        try:
            os.remove(file_name)
            self.delete_permission(file_path)
            self.client_socket.send(f"250 '{file_name}' deleted\r\n".encode('utf-8'))
        except FileNotFoundError:
            self.client_socket.send(f"550 '{file_name}': File not found.\r\n".encode('utf-8'))
        except PermissionError:
            self.client_socket.send(f"550 '{file_name}': Permission denied.\r\n".encode('utf-8'))
        except Exception as e:
            self.client_socket.send(f"550 '{file_name}': Error occurred ({str(e)})\r\n".encode('utf-8'))

    def handle_pwd(self):
        try:
            self.client_socket.send(f"257 \"{self.current_directory}\" is the current directory\r\n".encode())
        except Exception as e:
            print(f"Error in handle_pwd: {e}")
            self.client_socket.send(b"550 Error retrieving current directory\r\n")

        # self.client_socket.send(f"257 \"{self.current_directory}\" is the current directory\r\n".encode())

    def handle_mkd(self, directory_name):

        if_allowed = self.has_privilege(self.current_user, 'create', True)

        if (if_allowed == False):
            self.client_socket.send(b"550 Permission denied: You cannot create directories.\r\n")
            return

        try:
            directory_path = self.resolve_path(directory_name)
            os.mkdir(directory_path)
            self.client_socket.send(f"257 \"{directory_path}\" created as new directory\r\n".encode('utf-8'))
        except ValueError as ve:
            self.client_socket.send(b"550 Access to the path is restricted.\r\n")
            print(f"Error resolving path for MKD: {ve}")
        except FileExistsError:
            self.client_socket.send(f"550 '{directory_path}': Directory already exists.\r\n".encode('utf-8'))
        except PermissionError:
            self.client_socket.send(f"550 '{directory_path}': Permission denied.\r\n".encode('utf-8'))
        except OSError as os_err:
            self.client_socket.send(f"550 '{directory_path}': OS error ({str(os_err)}).\r\n".encode('utf-8'))
        except Exception as e:
            self.client_socket.send(f"550 '{directory_path}': Error occurred ({str(e)})\r\n".encode('utf-8'))
            print(f"Unexpected error in handle_mkd: {e}")

    def handle_rmd(self, directory_name):
        
        if_allowed = self.has_privilege(self.current_user, "delete", True)

        if (if_allowed == False):
            self.client_socket.send(b"550 Permission denied: You cannot remove directories.\r\n")
            return

        try:
            directory_path = self.resolve_path(directory_name)
            os.rmdir(directory_path)
            # shutil.rmtree(directory_path)
            self.client_socket.send(f"250 '{directory_path}' removed successfully\r\n".encode('utf-8'))
        except FileNotFoundError:
            self.client_socket.send(f"550 '{directory_path}': Directory not found.\r\n".encode('utf-8'))
        except OSError:
            self.client_socket.send(f"550 '{directory_path}': Directory not empty or cannot be removed.\r\n".encode('utf-8'))
        
    def handle_cwd(self, directory_name):
        
        directory_path = self.resolve_path(directory_name)
        try:
            os.chdir(directory_path)
            # self.current_directory = os.getcwd()
            self.current_directory = directory_path
            self.client_socket.send(f"250 Directory changed to {self.current_directory}\r\n".encode())
        except FileNotFoundError:
            self.client_socket.send(b"550 Directory not found\r\n")

    def handle_cdup(self):
        try:
            os.chdir('..')
            self.current_directory = os.getcwd()
            self.client_socket.send(f"250 Directory changed to {self.current_directory}\r\n".encode())
        except Exception as e:
            self.client_socket.send(f"550 {str(e)}\r\n".encode())

if __name__ == "__main__":
    ftp_server = FTPServer("127.0.0.1", 2121)
    ftp_server.start()
