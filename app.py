from flask import Flask, render_template_string, request, session, redirect, url_for, send_file, flash, jsonify
import subprocess
import psutil
import os
import socket
import requests
from datetime import datetime, timedelta
from threading import Thread
import time
import shutil
import random

app = Flask(__name__)
app.secret_key = 'super_secret_key'
BASE_SMB_PATH = '/mnt/smb'  # Set this to your SMB path

# Simpele lijst om berichten tijdelijk op te slaan (gebruik in een echte app een database)
CHAT_MESSAGES = []

# Hoofdlogo URL
MAIN_LOGO_URL = 'https://example.com/profile.png'  # Vervang dit door de URL van je logo

# User management - user dictionary
USERS = {
    'root': {'password': 'Admin', 'role': 'Administrator', 'profile_logo': 'https://example.com/profile.png'},
    'test': {'password': 'test', 'role': 'User', 'profile_logo': 'https://example.com/user1.png'}
}

# Styling updated to reflect an Ubuntu Server Dashboard theme
LOGIN_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>Login - Ubuntu Server Dashboard</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
        body {
            font-family: 'Roboto', sans-serif;
            background: linear-gradient(135deg, #77216F, #E95420);
            color: #ffffff;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }
        .login-box {
            background-color: rgba(0, 0, 0, 0.85);
            padding: 40px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.7);
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .login-box img {
            width: 120px;
            margin-bottom: 20px;
            border-radius: 50%;
        }
        h1 {
            font-size: 2.5em;
            color: #E95420;
            margin-bottom: 20px;
        }
        input[type="text"], input[type="password"] {
            width: 90%;
            padding: 15px;
            border-radius: 8px;
            border: none;
            margin-bottom: 20px;
            background-color: #444;
            color: #ffffff;
            text-align: center;
        }
        input[type="text"]:focus, input[type="password"]:focus {
            outline: none;
            border: 2px solid #E95420;
        }
        button {
            width: 90%;
            padding: 15px;
            border-radius: 8px;
            background-color: #E95420;
            color: #ffffff;
            font-weight: bold;
            font-size: 1.2em;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #C34113;
        }
    </style>
</head>
<body>
    <div class="login-box">
        <img src="{{ main_logo }}" alt="Main Logo" style="width: 150px; margin-bottom: 20px;">
        <h1>Login</h1>
        <form method="post" action="{{ url_for('login') }}">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
    </div>
</body>
<style>
    .status-container-fixed {
        position: fixed;
        bottom: 20px;
        right: 20px;
        display: flex;
        gap: 15px;
        align-items: center;
    }
    .status-item {
        display: flex;
        align-items: center;
        background-color: #444;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.3);
    }
    .status-item i {
        font-size: 18px;
        margin-right: 5px;
        color: #ffffff;
    }
    .vpn-status-label {
        font-weight: bold;
        margin-right: 5px;
        color: #ffffff;
    }
    .status-badge {
        padding: 5px 10px;
        border-radius: 50px;
        font-weight: bold;
        color: #ffffff;
        font-size: 0.9em;
    }
    .status-badge.active {
        background-color: #4CAF50;
        box-shadow: 0 0 10px rgba(76, 175, 80, 0.8);
    }
    .status-badge.inactive {
        background-color: #F44336;
        box-shadow: 0 0 10px rgba(244, 67, 54, 0.8);
    }
</style>

<div class="status-container-fixed">
    <!-- OpenVPN Status -->
    <div class="status-item">
        <i class="fas {% if openvpn_status == 'Active' %}fa-check-circle{% else %}fa-times-circle{% endif %}"></i>
        <span class="vpn-status-label">OpenVPN Status:</span>
        <span class="status-badge {% if openvpn_status == 'Active' %}active{% else %}inactive{% endif %}">
            {{ openvpn_status }}
        </span>
    </div>

    <!-- Squid Status -->
    <div class="status-item">
        <i class="fas {% if squid_status == 'Active' %}fa-check-circle{% else %}fa-times-circle{% endif %}"></i>
        <span class="vpn-status-label">Squid Status:</span>
        <span class="status-badge {% if squid_status == 'Active' %}active{% else %}inactive{% endif %}">
            {{ squid_status }}
        </span>
    </div>
</div>
</html>
"""
PROFILE_EDIT_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>Edit Profile - Ubuntu Server Dashboard</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
        body {
            font-family: 'Roboto', sans-serif;
            background: linear-gradient(135deg, #77216F, #E95420);
            color: #ffffff;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }
        .edit-profile-container {
            max-width: 600px;
            width: 100%;
            background-color: rgba(0, 0, 0, 0.85);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .edit-profile-header {
            width: 100%;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .edit-profile-header h2 {
            color: #E95420;
        }
        .back-button {
            background-color: #E95420;
            color: #ffffff;
            padding: 10px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            transition: background-color 0.3s;
        }
        .back-button:hover {
            background-color: #C34113;
        }
        input[type="text"], input[type="email"], input[type="password"] {
            width: 90%;
            padding: 15px;
            margin: 10px 0;
            border: none;
            border-radius: 8px;
            background-color: #444;
            color: #ffffff;
            text-align: center;
        }
        input[type="text"]:focus, input[type="email"]:focus, input[type="password"]:focus {
            outline: none;
            border: 2px solid #E95420;
        }
        button {
            width: 90%;
            padding: 15px;
            margin-top: 15px;
            background-color: #E95420;
            color: #ffffff;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: background-color 0.3s;
            font-weight: bold;
        }
        button:hover {
            background-color: #C34113;
        }
    </style>
</head>
<body>
    <div class="edit-profile-container">
        <div class="edit-profile-header">
            <h2>Edit Profile</h2>
            <button class="back-button" onclick="location.href='{{ url_for('index') }}'">Back to Dashboard</button>
        </div>
        <form method="post" action="{{ url_for('edit_profile') }}">
            <input type="text" name="name" value="{{ user_profile['name'] }}" placeholder="Name" required>
            <input type="email" name="email" value="{{ user_profile['email'] }}" placeholder="Email" required>
            <input type="text" name="role" value="{{ user_profile['role'] }}" placeholder="Role" readonly>
            <input type="text" name="profile_logo" value="{{ user_profile['profile_logo'] }}" placeholder="Profile Image URL" required>
            <input type="password" name="password" placeholder="New Password (optional)">
            <button type="submit">Save Changes</button>
        </form>
    </div>
</body>
<style>
    .status-container-fixed {
        position: fixed;
        bottom: 20px;
        right: 20px;
        display: flex;
        gap: 15px;
        align-items: center;
    }
    .status-item {
        display: flex;
        align-items: center;
        background-color: #444;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.3);
    }
    .status-item i {
        font-size: 18px;
        margin-right: 5px;
        color: #ffffff;
    }
    .vpn-status-label {
        font-weight: bold;
        margin-right: 5px;
        color: #ffffff;
    }
    .status-badge {
        padding: 5px 10px;
        border-radius: 50px;
        font-weight: bold;
        color: #ffffff;
        font-size: 0.9em;
    }
    .status-badge.active {
        background-color: #4CAF50;
        box-shadow: 0 0 10px rgba(76, 175, 80, 0.8);
    }
    .status-badge.inactive {
        background-color: #F44336;
        box-shadow: 0 0 10px rgba(244, 67, 54, 0.8);
    }
</style>

<div class="status-container-fixed">
    <!-- OpenVPN Status -->
    <div class="status-item">
        <i class="fas {% if openvpn_status == 'Active' %}fa-check-circle{% else %}fa-times-circle{% endif %}"></i>
        <span class="vpn-status-label">OpenVPN Status:</span>
        <span class="status-badge {% if openvpn_status == 'Active' %}active{% else %}inactive{% endif %}">
            {{ openvpn_status }}
        </span>
    </div>

    <!-- Squid Status -->
    <div class="status-item">
        <i class="fas {% if squid_status == 'Active' %}fa-check-circle{% else %}fa-times-circle{% endif %}"></i>
        <span class="vpn-status-label">Squid Status:</span>
        <span class="status-badge {% if squid_status == 'Active' %}active{% else %}inactive{% endif %}">
            {{ squid_status }}
        </span>
    </div>
</div>
</html>
"""

SETTINGS_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>User Management - Ubuntu Server Dashboard</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
        body {
            font-family: 'Roboto', sans-serif;
            background: linear-gradient(135deg, #77216F, #E95420);
            color: #eeeeee;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }
        .settings-container {
            max-width: 800px;
            width: 100%;
            background-color: rgba(0, 0, 0, 0.85);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        h2 {
            color: #E95420;
            text-align: center;
            margin-bottom: 20px;
        }
        .nav {
            width: 100%;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: #444;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
            margin-bottom: 20px;
        }
        .nav .nav-buttons {
            display: flex;
            gap: 15px;
        }
        .nav button {
            background-color: #E95420;
            color: #ffffff;
            padding: 10px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            transition: background-color 0.3s;
        }
        .nav button:hover {
            background-color: #C34113;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        table, th, td {
            border: 1px solid #777;
        }
        th, td {
            padding: 10px;
            text-align: center;
        }
        th {
            background-color: #444;
        }
        button {
            background-color: #E95420;
            color: #ffffff;
            padding: 10px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: background-color 0.3s;
            font-weight: bold;
        }
        button:hover {
            background-color: #C34113;
        }
        .form-container {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        input[type="text"], select {
            padding: 10px;
            border: none;
            border-radius: 8px;
            background-color: #555;
            color: #ffffff;
        }
        input[type="text"]:focus, select:focus {
            outline: none;
            border: 2px solid #E95420;
        }
    </style>
</head>
<body>
    <div class="settings-container">
        <div class="nav">
            <div class="nav-buttons">
                <button onclick="location.href='{{ url_for('index') }}'">Dashboard</button>
                <button onclick="location.href='{{ url_for('edit_profile') }}'">Edit Profile</button>
                <button onclick="location.href='{{ url_for('logout') }}'">Logout</button>
            </div>
        </div>
        <h2>User Management</h2>
        <table>
            <thead>
                <tr>
                    <th>Username</th>
                    <th>Role</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
                {% for user, details in users.items() %}
                <tr>
                    <td>{{ user }}</td>
                    <td>{{ details['role'] }}</td>
                    <td>
                        {% if user != 'admin' and session['user_profile']['role'] == 'Administrator' %}
                        <button onclick="location.href='{{ url_for('delete_user', username=user) }}'">Delete</button>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        <div class="form-container">
            {% if session['user_profile']['role'] == 'Administrator' %}
            <form method="post" action="{{ url_for('add_user') }}">
                <input type="text" name="username" placeholder="Username" required>
                <input type="text" name="password" placeholder="Password" required>
                <select name="role" required>
                    <option value="User">User</option>
                    <option value="Administrator">Administrator</option>
                </select>
                <button type="submit">Add User</button>
            </form>
            {% endif %}
        </div>
    </div>
</body>
<style>
    .status-container-fixed {
        position: fixed;
        bottom: 20px;
        right: 20px;
        display: flex;
        gap: 15px;
        align-items: center;
    }
    .status-item {
        display: flex;
        align-items: center;
        background-color: #444;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.3);
    }
    .status-item i {
        font-size: 18px;
        margin-right: 5px;
        color: #ffffff;
    }
    .vpn-status-label {
        font-weight: bold;
        margin-right: 5px;
        color: #ffffff;
    }
    .status-badge {
        padding: 5px 10px;
        border-radius: 50px;
        font-weight: bold;
        color: #ffffff;
        font-size: 0.9em;
    }
    .status-badge.active {
        background-color: #4CAF50;
        box-shadow: 0 0 10px rgba(76, 175, 80, 0.8);
    }
    .status-badge.inactive {
        background-color: #F44336;
        box-shadow: 0 0 10px rgba(244, 67, 54, 0.8);
    }
</style>

<div class="status-container-fixed">
    <!-- OpenVPN Status -->
    <div class="status-item">
        <i class="fas {% if openvpn_status == 'Active' %}fa-check-circle{% else %}fa-times-circle{% endif %}"></i>
        <span class="vpn-status-label">OpenVPN Status:</span>
        <span class="status-badge {% if openvpn_status == 'Active' %}active{% else %}inactive{% endif %}">
            {{ openvpn_status }}
        </span>
    </div>

    <!-- Squid Status -->
    <div class="status-item">
        <i class="fas {% if squid_status == 'Active' %}fa-check-circle{% else %}fa-times-circle{% endif %}"></i>
        <span class="vpn-status-label">Squid Status:</span>
        <span class="status-badge {% if squid_status == 'Active' %}active{% else %}inactive{% endif %}">
            {{ squid_status }}
        </span>
    </div>
</div>

</html>
"""

HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>Ubuntu Server Dashboard</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
        body {
            font-family: 'Roboto', sans-serif;
            background: linear-gradient(135deg, #77216F, #E95420);
            color: #eeeeee;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }
        .dashboard-container {
            max-width: 1200px;
            width: 100%;
            background-color: rgba(0, 0, 0, 0.85);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 20px; /* Ruimte tussen secties */
        }
        .nav {
            width: 100%;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: #444;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
        }
        .nav .nav-buttons {
            display: flex;
            gap: 15px;
        }
        .nav button, .nav input[type="text"] {
            padding: 10px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: background-color 0.3s;
            font-weight: bold;
        }
        .nav button {
            background-color: #E95420;
            color: #ffffff;
        }
        .nav button:hover {
            background-color: #C34113;
        }
        .nav input[type="text"] {
            background-color: #ffffff;
            color: #333;
            width: 300px;
            border: 2px solid #E95420;
        }
        h1 {
            color: #E95420;
            text-align: center;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        h1 img {
            border-radius: 50%; /* Logo rond maken */
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
        }
        .profile-box {
            width: 100%;
            background-color: #444;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }
        .profile-box h3 {
            color: #E95420;
            margin-bottom: 10px;
        }
        .system-info {
            width: 100%;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }
        .info-box {
            background-color: #444;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }
        .info-box h3 {
            color: #E95420;
            margin-bottom: 10px;
        }
        .chat-container {
            width: 100%;
            background-color: #333;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }
        #chat-box {
            height: 200px;
            overflow-y: scroll;
            background-color: #444;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 15px; /* Ruimte onder de chat */
        }
        .chat-form {
            display: flex;
            gap: 10px;
            justify-content: space-between;
            align-items: center;
        }
        .chat-form input[type="text"] {
            flex: 1;
            padding: 10px;
            border-radius: 8px;
            border: 2px solid #E95420;
            background-color: #555;
            color: #ffffff;
        }
        .smb-list {
            width: 100%;
        }
        .smb-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background-color: #555;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.3);
        }
        .smb-item i {
            color: #E95420;
        }
        .smb-link {
            color: #E95420;
            text-decoration: none;
            font-weight: bold;
        }
        .smb-link:hover {
            text-decoration: underline;
        }
        .vpn-status {
            background-color: #444;
            padding: 10px;
            border-radius: 8px;
            font-weight: bold;
            text-align: center;
            color: #ffffff;
        }
        .vpn-status.active {
            color: #4CAF50;
        }
        .vpn-status.inactive {
            color: #F44336;
        }
        .command-line {
            width: 100%;
            background-color: #333;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            display: flex;
            flex-direction: column;
            gap: 15px; /* Ruimte binnen de container */
        }
        .command-line form {
            display: flex;
            gap: 10px;
        }
        .command-line input[type="text"] {
            flex: 1;
            padding: 10px;
            border-radius: 8px;
            border: 2px solid #E95420;
            background-color: #555;
            color: #ffffff;
        }
        .command-line pre {
            background-color: #222;
            padding: 15px;
            border-radius: 8px;
            color: #00FF00;
            margin-top: 15px;
            white-space: pre-wrap;
            word-break: break-all;
            max-height: 300px;
            overflow-y: auto;
        }
        button {
            background-color: #E95420;
            color: #ffffff;
            padding: 15px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: background-color 0.3s;
            font-weight: bold;
        }
        button:hover {
            background-color: #C34113;
        }
    </style>
    <script>
        // JavaScript voor het bijwerken van de chat in real-time
        function loadChatMessages() {
            fetch('/get_chat_messages')
            .then(response => response.json())
            .then(data => {
                const chatBox = document.getElementById('chat-box');
                chatBox.innerHTML = '';  // Leeg de chatbox
                data.forEach(msg => {
                    const msgElem = document.createElement('div');
                    msgElem.textContent = `${msg.username}: ${msg.message}`;
                    msgElem.style.marginBottom = '5px';
                    chatBox.appendChild(msgElem);
                });
                chatBox.scrollTop = chatBox.scrollHeight;  // Scroll naar de onderkant
            });
        }
        setInterval(loadChatMessages, 3000);  // Update de chat elke 3 seconden
        document.addEventListener('DOMContentLoaded', loadChatMessages); // Laad chat bij het starten
    </script>
</head>
<body>
    <div class="dashboard-container">
        <div class="nav">
            <div class="nav-buttons">
                <button onclick="location.href='{{ url_for('index') }}'">Dashboard</button>
                <button onclick="location.href='{{ url_for('edit_profile') }}'">Edit Profile</button>
                <button onclick="location.href='{{ url_for('settings') }}'">User Management</button>
                <button onclick="location.href='{{ url_for('logout') }}'">Logout</button>
            </div>
            <input type="text" placeholder="Search...">
        </div>
        <h1><img src="{{ main_logo }}" alt="Main Logo" style="width: 100px; vertical-align: middle;"> Ubuntu Server Dashboard</h1>
        
  <div class="profile-container">
    <h2>User Profile</h2>
    <div class="profile-card">
        <div class="profile-image">
            <img src="{{ user_profile['profile_logo'] }}" alt="Profile Image">
        </div>
        <div class="profile-details">
            <p><strong>Name:</strong> {{ user_profile['name'] }}</p>
            <p><strong>Email:</strong> {{ user_profile['email'] }}</p>
            <p><strong>Role:</strong> {{ user_profile['role'] }}</p>
        </div>
    </div>
</div>

<style>
    .profile-container {
        width: 100%;
        margin-top: 20px;
        background-color: #333;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        text-align: center;
    }
    .profile-container h2 {
        color: #E95420;
        margin-bottom: 15px;
    }
    .profile-card {
        display: flex;
        flex-direction: column;
        align-items: center;
        background-color: #444;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.3);
    }
    .profile-image img {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
        margin-bottom: 15px;
    }
    .profile-details p {
        color: #ffffff;
        font-size: 1.1em;
        margin: 5px 0;
    }
    .profile-details strong {
        color: #E95420;
    }
</style>


        <div class="system-info-container">
    <h2>System Information</h2>
    <div class="system-info">
        <div class="info-box">
            <h3><i class="fas fa-microchip"></i> CPU Usage</h3>
            <p id="cpu-usage">Loading...</p>
        </div>
        <div class="info-box">
            <h3><i class="fas fa-memory"></i> Memory Usage</h3>
            <p id="memory-usage">Loading...</p>
        </div>
        <div class="info-box">
            <h3><i class="fas fa-hdd"></i> Disk Usage</h3>
            <p id="disk-usage">Loading...</p>
        </div>
        <div class="info-box">
            <h3><i class="fas fa-globe"></i> Public IP</h3>
            <p id="public-ip">Loading...</p>
        </div>
        <div class="info-box">
            <h3><i class="fas fa-network-wired"></i> Private IP</h3>
            <p id="private-ip">Loading...</p>
        </div>
        <div class="info-box">
            <h3><i class="fas fa-server"></i> Server IP</h3>
            <p id="server-ip">Loading...</p>
        </div>
        <div class="info-box">
            <h3><i class="fas fa-desktop"></i> Hostname</h3>
            <p id="hostname">Loading...</p>
        </div>
        <div class="info-box">
            <h3><i class="fas fa-clock"></i> Uptime</h3>
            <p id="uptime">Loading...</p>
        </div>
    </div>
</div>

<style>
    .system-info-container {
        width: 100%;
        margin-top: 20px;
        background-color: #333;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        text-align: center;
    }
    .system-info-container h2 {
        color: #E95420;
        margin-bottom: 15px;
    }
    .system-info {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
    }
    .info-box {
        background-color: #444;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.3);
    }
    .info-box h3 {
        color: #E95420;
        margin-bottom: 10px;
    }
    .info-box i {
        margin-right: 5px;
    }
</style>

<script>
    function updateSystemInfo() {
        fetch('/get_system_info')
        .then(response => response.json())
        .then(data => {
            document.getElementById('cpu-usage').textContent = data.cpu_percent + '%';
            document.getElementById('memory-usage').textContent = data.memory_percent + '%';
            document.getElementById('disk-usage').textContent = data.disk_percent + '%';
            document.getElementById('public-ip').textContent = data.public_ip;
            document.getElementById('private-ip').textContent = data.private_ip;
            document.getElementById('server-ip').textContent = data.server_ip;
            document.getElementById('hostname').textContent = data.hostname;
            document.getElementById('uptime').textContent = data.uptime;
        });
    }

    setInterval(updateSystemInfo, 1000); // Update every 5 seconds
    document.addEventListener('DOMContentLoaded', updateSystemInfo); // Initial load
</script>

        <!-- VPN Status en Controls -->
  <!-- Verbeterde HTML voor statusweergave met aantrekkelijke badges -->
<div class="status-container">
    <!-- OpenVPN Status -->
    <div class="status-item">
        <i class="fas {% if openvpn_status == 'Active' %}fa-check-circle{% else %}fa-times-circle{% endif %}"></i>
        <span class="vpn-status-label">OpenVPN Status:</span>
        <span class="status-badge {% if openvpn_status == 'Active' %}active{% else %}inactive{% endif %}">
            {{ openvpn_status }}
        </span>
    </div>

    <!-- Squid Status -->
    <div class="status-item">
        <i class="fas {% if squid_status == 'Active' %}fa-check-circle{% else %}fa-times-circle{% endif %}"></i>
        <span class="vpn-status-label">Squid Status:</span>
        <span class="status-badge {% if squid_status == 'Active' %}active{% else %}inactive{% endif %}">
            {{ squid_status }}
        </span>
    </div>
</div>

<style>
    /* Container for all status items */
    .status-container {
        display: flex;
        gap: 20px;
        justify-content: center;
        align-items: center;
        margin-top: 20px;
    }

    /* Individual status item */
    .status-item {
        display: flex;
        align-items: center;
        background-color: #444;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.3);
    }

    /* Icon representing the status */
    .status-item i {
        font-size: 24px;
        margin-right: 10px;
        color: #ffffff;
    }
    
    /* VPN/Squid Status label */
    .vpn-status-label {
        font-weight: bold;
        margin-right: 10px;
    }

    /* Status badge styling */
    .status-badge {
        padding: 5px 15px;
        border-radius: 50px;
        font-weight: bold;
        color: #ffffff;
        font-size: 1em;
    }

    /* Active status badge */
    .status-badge.active {
        background-color: #4CAF50;
        box-shadow: 0 0 10px rgba(76, 175, 80, 0.8);
    }

    /* Inactive status badge */
    .status-badge.inactive {
        background-color: #F44336;
        box-shadow: 0 0 10px rgba(244, 67, 54, 0.8);
    }
</style>

  {% if user_profile['role'] == 'Administrator' %}
<div class="vpn-controls">
    <h2>Service Controls</h2>
    <div class="button-group">
        <button class="service-button" onclick="location.href='{{ url_for('start_openvpn') }}'">
            <i class="fas fa-play"></i> Start OpenVPN
        </button>
        <button class="service-button" onclick="location.href='{{ url_for('stop_openvpn') }}'">
            <i class="fas fa-stop"></i> Stop OpenVPN
        </button>
        <button class="service-button" onclick="location.href='{{ url_for('enable_openvpn') }}'">
            <i class="fas fa-toggle-on"></i> Enable OpenVPN
        </button>
        <button class="service-button" onclick="location.href='{{ url_for('start_squid') }}'">
            <i class="fas fa-play"></i> Start Squid
        </button>
        <button class="service-button" onclick="location.href='{{ url_for('stop_squid') }}'">
            <i class="fas fa-stop"></i> Stop Squid
        </button>
        <button class="service-button" onclick="location.href='{{ url_for('enable_squid') }}'">
            <i class="fas fa-toggle-on"></i> Enable Squid
        </button>
    </div>
</div>
{% endif %}
<style>
    .vpn-controls {
        width: 100%;
        text-align: center;
        margin-top: 20px;
        background-color: #333;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    .vpn-controls h2 {
        color: #E95420;
        margin-bottom: 15px;
    }
    .button-group {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        justify-content: center;
    }
    .service-button {
        background-color: #444;
        color: #ffffff;
        padding: 10px 20px;
        border: none;
        border-radius: 8px;
        font-size: 1em;
        display: flex;
        align-items: center;
        gap: 8px;
        cursor: pointer;
        transition: background-color 0.3s;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
    }
    .service-button:hover {
        background-color: #C34113;
    }
    .service-button i {
        font-size: 1.2em;
    }
</style>

        <!-- Live chat sectie -->
        <div class="chat-container">
            <h3 style="color: #E95420; margin-bottom: 10px;">Live Chat</h3>
            <div id="chat-box">
                <!-- Chatberichten verschijnen hier -->
            </div>
            <form class="chat-form" id="chat-form" action="{{ url_for('send_chat_message') }}" method="post">
                <input type="text" name="message" placeholder="Type your message...">
                <button type="submit">Send</button>
            </form>
        </div>

        <!-- SMB Shares -->
        <!-- SMB Shares -->
<div class="smb-container">
    <h2>SMB Shares</h2>
    {% if smb_files %}
        <div class="smb-list">
            {% for item in smb_files %}
            <div class="smb-item">
                <i class="fas {% if item['type'] == 'directory' %}fa-folder{% elif item['type'] == 'file' %}fa-file{% else %}fa-exclamation-circle{% endif %}"></i>
                <div class="smb-info">
                    {% if item['type'] == 'directory' %}
                    <a href="{{ url_for('browse_smb', path=item['path']) }}" class="smb-link">{{ item['name'] }}/</a>
                    {% elif item['type'] == 'file' %}
                    <span>{{ item['name'] }}</span>
                    <a href="{{ url_for('smb_download', filename=item['path']) }}" class="smb-link"><i class="fas fa-download"></i> Download</a>
                    {% elif item['type'] == 'error' %}
                    <span class="error-text">{{ item['name'] }}</span>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
    {% else %}
        <p class="no-smb-message">No SMB shares available or directory is empty.</p>
    {% endif %}
</div>

<style>
    .smb-container {
        width: 100%;
        background-color: #333;
        padding: 20px;
        border-radius: 10px;
        margin-top: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    .smb-container h2 {
        color: #E95420;
        text-align: center;
        margin-bottom: 15px;
    }
    .smb-list {
        display: flex;
        flex-direction: column;
        gap: 15px;
    }
    .smb-item {
        display: flex;
        align-items: center;
        background-color: #444;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s;
    }
    .smb-item:hover {
        transform: translateY(-5px);
    }
    .smb-item i {
        font-size: 24px;
        margin-right: 15px;
        color: #E95420;
    }
    .smb-info {
        display: flex;
        flex-grow: 1;
        justify-content: space-between;
        align-items: center;
    }
    .smb-link {
        color: #4CAF50;
        font-weight: bold;
        text-decoration: none;
    }
    .smb-link:hover {
        text-decoration: underline;
    }
    .error-text {
        color: #F44336;
        font-weight: bold;
    }
    .no-smb-message {
        color: #CCCCCC;
        text-align: center;
        margin-top: 15px;
        font-style: italic;
    }
</style>
        <!-- Command Line -->
        {% if user_profile['role'] == 'Administrator' %}
        <div class="command-line">
            <h2>Command Line</h2>
            <form method="post" action="{{ url_for('execute_command') }}">
                <input type="text" name="command" placeholder="Enter command">
                <button type="submit">Execute</button>
            </form>
            <pre>{{ cmd_output }}</pre>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = USERS.get(username)
        if user and user['password'] == password:
            session['logged_in'] = True
            session['user_profile'] = user
            session['username'] = username
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials. Please try again.')
    return render_template_string(LOGIN_TEMPLATE, main_logo=MAIN_LOGO_URL, user_profile={"profile_logo": "https://example.com/profile.png"}, openvpn_status=get_openvpn_status(), squid_status=get_squid_status())
@app.route('/login', methods=['GET', 'POST'])


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template_string(
        HTML_TEMPLATE,
        main_logo=MAIN_LOGO_URL,
        system_info=get_system_info(),
        smb_files=get_smb_files(BASE_SMB_PATH),
        cmd_output="",
        openvpn_status=get_openvpn_status(),
        squid_status=get_squid_status(),
        user_profile=session.get('user_profile', {"name": "admin", "email": "admin@example.com", "role": "Administrator", "profile_logo": 'https://example.com/profile.png'})
    )


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        user_profile = session.get('user_profile', {})
        user_profile['name'] = request.form.get('name')
        user_profile['email'] = request.form.get('email')
        user_profile['profile_logo'] = request.form.get('profile_logo')
        if request.form.get('password'):
            user_profile['password'] = request.form.get('password')
        USERS[session['username']].update(user_profile)
        session['user_profile'] = user_profile
        flash('Profile updated successfully!')
        return redirect(url_for('index'))
    return render_template_string(PROFILE_EDIT_TEMPLATE, user_profile=session.get('user_profile', {"name": "admin", "email": "admin@example.com", "role": "Administrator", "profile_logo": 'https://example.com/profile.png'}), openvpn_status=get_openvpn_status(), squid_status=get_squid_status())

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if not session.get('logged_in') or session.get('user_profile', {}).get('role') not in ['Administrator', 'User']:
        return redirect(url_for('login'))
    return render_template_string(SETTINGS_TEMPLATE, users=USERS, openvpn_status=get_openvpn_status(), squid_status=get_squid_status())

@app.route('/add_user', methods=['POST'])
def add_user():
    if not session.get('logged_in') or session.get('user_profile', {}).get('role') != 'Administrator':
        return redirect(url_for('login'))
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')
    if username and password and role:
        USERS[username] = {'password': password, 'role': role, 'profile_logo': 'https://example.com/profile.png'}
    return redirect(url_for('settings'))

@app.route('/delete_user/<username>', methods=['GET'])
def delete_user(username):
    if not session.get('logged_in') or session.get('user_profile', {}).get('role') != 'Administrator':
        return redirect(url_for('login'))
    if username in USERS and username != 'admin':
        del USERS[username]
    return redirect(url_for('settings'))

@app.route('/execute_command', methods=['POST'])
def execute_command():
    if not session.get('logged_in') or session.get('user_profile', {}).get('role') != 'Administrator':
        return redirect(url_for('login'))
    command = request.form.get('command')
    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT).decode()
    except subprocess.CalledProcessError as e:
        output = e.output.decode()
    except Exception as e:
        output = f"Unexpected error occurred: {str(e)}"
    return render_template_string(
        HTML_TEMPLATE,
        main_logo=MAIN_LOGO_URL,
        system_info=get_system_info(),
        smb_files=get_smb_files(BASE_SMB_PATH),
        cmd_output=output,
        openvpn_status=get_openvpn_status(),
        user_profile=session.get('user_profile', {"name": "admin", "email": "admin@example.com", "role": "Administrator", "profile_logo": 'https://example.com/profile.png'})
    )

@app.route('/start_openvpn')
def start_openvpn():
    if not session.get('logged_in') or session.get('user_profile', {}).get('role') != 'Administrator':
        return redirect(url_for('login'))
    subprocess.call(['sudo', 'systemctl', 'start', 'openvpn'])
    flash('OpenVPN started successfully!')
    return redirect(url_for('index'))

@app.route('/stop_openvpn')
def stop_openvpn():
    if not session.get('logged_in') or session.get('user_profile', {}).get('role') != 'Administrator':
        return redirect(url_for('login'))
    subprocess.call(['sudo', 'systemctl', 'stop', 'openvpn'])
    flash('OpenVPN stopped successfully!')
    return redirect(url_for('index'))

@app.route('/enable_openvpn')
def enable_openvpn():
    if not session.get('logged_in') or session.get('user_profile', {}).get('role') != 'Administrator':
        return redirect(url_for('login'))
    subprocess.call(['sudo', 'systemctl', 'enable', 'openvpn'])
    flash('OpenVPN enabled successfully!')
    return redirect(url_for('index'))

@app.route('/start_squid')
def start_squid():
    if not session.get('logged_in') or session.get('user_profile', {}).get('role') != 'Administrator':
        return redirect(url_for('login'))
    subprocess.call(['sudo', 'systemctl', 'start', 'squid'])
    flash('Squid started successfully!')
    return redirect(url_for('index'))

@app.route('/stop_squid')
def stop_squid():
    if not session.get('logged_in') or session.get('user_profile', {}).get('role') != 'Administrator':
        return redirect(url_for('login'))
    subprocess.call(['sudo', 'systemctl', 'stop', 'squid'])
    flash('Squid stopped successfully!')
    return redirect(url_for('index'))

@app.route('/enable_squid')
def enable_squid():
    if not session.get('logged_in') or session.get('user_profile', {}).get('role') != 'Administrator':
        return redirect(url_for('login'))
    subprocess.call(['sudo', 'systemctl', 'enable', 'squid'])
    flash('Squid enabled successfully!')
    return redirect(url_for('index'))

@app.route('/browse_smb')
def browse_smb():
    path = request.args.get('path', '')
    directory = os.path.join(BASE_SMB_PATH, path)
    try:
        items = os.listdir(directory)
        smb_files = []
        for item in items:
            item_path = os.path.join(path, item)
            if os.path.isdir(os.path.join(BASE_SMB_PATH, item_path)):
                smb_files.append({'name': item, 'path': item_path, 'type': 'directory'})
            else:
                smb_files.append({'name': item, 'path': item_path, 'type': 'file'})
        return render_template_string(HTML_TEMPLATE, smb_files=smb_files, main_logo=MAIN_LOGO_URL, system_info=get_system_info(), cmd_output="", openvpn_status=get_openvpn_status(), user_profile=session.get('user_profile', {"name": "admin", "email": "admin@example.com", "role": "Administrator"}))
    except FileNotFoundError:
        flash('Directory not found')
        return redirect(url_for('index'))


@app.route('/smb_download', methods=['GET'])
def smb_download():
    filename = request.args.get('filename')
    if not filename:
        flash('No filename specified')
        return redirect(url_for('index'))
    file_path = os.path.join(BASE_SMB_PATH, filename)
    try:
        return send_file(file_path, as_attachment=True)
    except FileNotFoundError:
        flash('File not found.')
        return redirect(url_for('index'))

@app.route('/send_chat_message', methods=['POST'])
def send_chat_message():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    message = request.form.get('message')
    if message:
        CHAT_MESSAGES.append({'username': session['username'], 'message': message})
    return redirect(url_for('index'))

@app.route('/get_chat_messages')
def get_chat_messages():
    return jsonify(CHAT_MESSAGES)

# Utility Functions
def get_system_info():
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    uptime = str(timedelta(seconds=int(datetime.now().timestamp() - psutil.boot_time())))
    try:
        public_ip = requests.get("https://api.ipify.org").text if requests.get("https://api.ipify.org").status_code == 200 else 'Unavailable'
    except requests.RequestException:
        public_ip = "Unavailable"
    hostname = socket.gethostname()
    private_ip = socket.gethostbyname(hostname)
    server_ip = socket.gethostbyname(socket.gethostname())
    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "disk_percent": disk.percent,
        "public_ip": public_ip,
        "private_ip": private_ip,
        "server_ip": server_ip,
        "hostname": hostname,
        "uptime": uptime
    }

def get_squid_status():
    try:
        output = subprocess.check_output(['sudo', 'systemctl', 'is-active', 'squid']).decode().strip()
        return "Active" if output == "active" else "Inactive"
    except subprocess.CalledProcessError:
        return "Inactive"
    except Exception as e:
        return f"Error checking Squid status: {str(e)}"

def get_openvpn_status():
    try:
        output = subprocess.check_output(['sudo', 'systemctl', 'is-active', 'openvpn']).decode().strip()
        return "Active" if output == "active" else "Inactive"
    except subprocess.CalledProcessError:
        return "Inactive"
    except Exception as e:
        return f"Error checking VPN status: {str(e)}"

def get_smb_files(path):
    try:
        output = os.listdir(path)
        return [{'name': item, 'type': 'directory' if os.path.isdir(os.path.join(path, item)) else 'file', 'path': item} for item in output]
    except FileNotFoundError:
        return []
    except Exception as e:
        return [{"name": f"Error retrieving SMB shares: {str(e)}", "type": "error", "path": ""}]

@app.route('/get_system_info')
def get_system_info_json():
    return jsonify(get_system_info())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
