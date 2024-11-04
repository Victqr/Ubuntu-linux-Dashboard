# Ubuntu Server Dashboard

A comprehensive web-based dashboard for monitoring and managing Ubuntu server resources, built using Flask. This dashboard offers real-time system information, user management, service control, a live chat feature, and an integrated file-sharing interface.

## Features

### User Authentication and Management
- **Secure Login System**: Authenticate users with role-based access (Administrator and User).
- **User Profiles**: Users can update their profile information including name, email, and profile picture.
- **Admin Controls**: Administrators can add or remove users and manage user roles.

### Dashboard Overview
- **System Information**: Monitor CPU, memory, disk usage, uptime, public and private IPs, and server hostname.
- **Service Monitoring**: Check the status of critical services like OpenVPN and Squid.
- **Service Controls**: Start, stop, and enable services directly from the dashboard (Admin only).

### File Sharing (SMB Integration)
- **Browse SMB Shares**: Access shared directories and files.
- **File Download**: Download files directly from the web interface.

### Live Chat Feature
- **Real-Time Messaging**: Communicate with other users via an integrated chat interface.
- **Auto-Refresh**: The chat updates every few seconds to reflect new messages.

### Command Line Access (Admin Only)
- **Run Commands**: Execute shell commands from the web interface and display the output.
- **Output Display**: View the result or error messages from executed commands.

### Visual Service Status Indicators
- **OpenVPN and Squid**: Status badges (green for active, red for inactive) for quick monitoring.
- **Service Management**: Administrators can start, stop, or enable services with a single click.

## Technologies Used
- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript
- **Monitoring Tools**: `psutil` for system resource statistics and `subprocess` for command execution
- **Networking**: `socket` and `requests` for network information

## Installation and Setup

### Prerequisites
- Python 3.x
- Required Python packages: `Flask`, `psutil`, `requests`

### Installation Steps
1. **Clone the Repository**:
    ```bash
    git clone https://github.com/victqr/ubuntu-server-dashboard.git
    cd ubuntu-server-dashboard
    ```

2. **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Run the Flask Application**:
    ```bash
    python app.py
    ```

4. **Access the Dashboard**:
   Open `http://localhost:5000` in your web browser. For remote access, use `http://<server-ip>:5000`.

### Configuration
- **SMB Path**: Update `BASE_SMB_PATH` in `app.py` to match your SMB base path.
- **Service Commands**: Ensure `sudo` permissions are properly configured for managing services like `openvpn` and `squid`.

## Screenshots
### Login Page
![image](https://github.com/user-attachments/assets/8e220441-2050-4002-9b6d-4d4089ad8244)


### Dashboard Overview
![Schermafbeelding 2024-11-04 222303](https://github.com/user-attachments/assets/b5b52103-871c-43b5-867f-0fc025f1d70c)
![Schermafbeelding 2024-11-04 222556](https://github.com/user-attachments/assets/56da0fc0-9e90-41eb-9014-68be472f27b7)
![Schermafbeelding 2024-11-04 222626](https://github.com/user-attachments/assets/dae9e1c5-653d-4944-b894-22f8e676d539)


- **System Monitoring**
- **User Profile**
- **Service Controls**
- **Live Chat**
- **SMB File Sharing**

### User Management Overview
![image](https://github.com/user-attachments/assets/2edc0d8b-b667-4620-8f84-41fdb064e363)

### Edit Profile Overview
![image](https://github.com/user-attachments/assets/6a5ddb7e-b688-48bf-a8f3-e57a76eb7b0e)


## Security Considerations
- **Secret Key**: Change `app.secret_key` for production environments.
- **Password Storage**: Use secure methods for storing user passwords (e.g., hashing with `bcrypt`).
- **Access Control**: Ensure only trusted users can access administrative features and run commands.

## Contributing
Contributions are welcome! Please submit issues and pull requests to help improve the project.

## License
This project is licensed under the MIT License. See the `LICENSE` file for more details.

## Contact
For any questions or feedback, feel free to contact me.

