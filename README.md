# OpenVAS Automation Script
A Python-based script to automate OpenVAS tasks such as creating targets, running scans, and exporting reports in PDF, CSV, and JSON formats. Ideal for users looking to streamline vulnerability assessments without a GUI.

## Prerequisites
1. Python 3.7+
2. OpenVAS: Properly installed and configured.
3. Dependencies: Install the required Python packages using requirements.txt.

## Installation
1. Clone the Repository:

       git clone https://github.com/JalilAhmad2004/openvas-automation-script.git
       cd openvas-automation-script

2. Install Python Dependencies:

       pip install -r requirements.txt

3. Ensure OpenVAS is Installed:
    If OpenVAS is not installed, install it using:
   
        sudo apt update
        sudo apt install -y openvas
4. Initialize OpenVAS:

        gvm-setup

## Configuration
1. Update Credentials:
    Edit the script and replace the placeholder credentials with your OpenVAS username and password:

        username = 'your_username'
        password = 'your_password'
2. Start OpenVAS Services:
    Ensure the required services are running:

        sudo systemctl start gvmd
        sudo systemctl start gsad

## Usage
  Run the Script:
    Use the following command to execute the script:

        python3 automation_script.py <target_ip> <ports> <target_name> <task_name>
        
## Features
- Automates Scan Management:
    - Creates a target with specified IP and ports.
    - Configures and starts scans using OpenVAS's default configurations.
- Generates Reports:
    - Exports scan results in PDF, CSV, and JSON formats.

## Troubleshooting
1. Connection Issues:
   - Verify that the required services are running:

          sudo systemctl status gvmd
          sudo systemctl status gsad
   
    - Ensure the Unix socket (/run/gvmd/gvmd.sock) is accessible.
2. Missing Dependencies:
    - Install the required Python packages:

          pip install -r requirements.txt
3. Permissions:
    - Run the script with appropriate permissions if accessing system files or services.
  
## Contributing
Contributions are welcome! Feel free to fork this repository, create a branch, and submit a pull request.

## License
This project is licensed under the MIT License. See the LICENSE file for details.
