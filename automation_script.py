import sys
import csv
import json
from gvm.connections import UnixSocketConnection
from gvm.errors import GvmError
from gvm.protocols.gmp import Gmp
from gvm.transforms import EtreeCheckCommandTransform
from argparse import Namespace
from tabulate import tabulate
from base64 import b64decode
from pathlib import Path
import time

# Function to list all scanners
def list_scanners(gmp):
    response_xml = gmp.get_scanners(filter_string="rows=-1")
    scanners_xml = response_xml.xpath("scanner")

    heading = ["#", "Name", "Id", "Host"]
    rows = []
    number_rows = 0

    print("Listing scanners.\n")

    for scanner in scanners_xml:
        number_rows += 1
        row_number = str(number_rows)
        name = "".join(scanner.xpath("name/text()"))
        scanner_id = scanner.get("id")
        host = "".join(scanner.xpath("host/text()"))

        rows.append([row_number, name, scanner_id, host])

    print(tabulate(rows, headers=heading))

    # Return the ID of the OpenVAS default scanner
    for scanner in rows:
        if "OpenVAS Default" in scanner[1]:  # Adjust the name to match your environment
            return scanner[2]

    return None

# Function to list all scan configurations
def list_scan_configs(gmp):
    response_xml = gmp.get_scan_configs(filter_string="rows=-1")
    configs_xml = response_xml.xpath("config")

    heading = ["#", "Name", "Id"]
    rows = []
    number_rows = 0

    print("Listing scan configurations.\n")

    for config in configs_xml:
        number_rows += 1
        row_number = str(number_rows)
        name = "".join(config.xpath("name/text()"))
        config_id = config.get("id")

        rows.append([row_number, name, config_id])

    print(tabulate(rows, headers=heading))

    # Return the ID of the OpenVAS default scan config
    for config in rows:
        if "Full and fast" in config[1]:  # Adjust the name to match your environment
            return config[2]

    return None

# Function to create a target with specified ports
def create_target(gmp, name, hosts, ports):
    try:
        port_range = ports
        response = gmp.create_target(name=name, hosts=[hosts], port_range=port_range)
        target_id = response.xpath('.//@id')[0]
        return target_id
    except GvmError as e:
        print(f'Failed to create target: {e}')
        return None

# Function to create a task for the created target
def create_task(gmp, name, scanner_id, target_id, config_id):
    try:
        response = gmp.create_task(name=name, scanner_id=scanner_id, target_id=target_id, config_id=config_id)
        task_id = response.xpath('.//@id')[0]
        return task_id
    except GvmError as e:
        print(f'Failed to create task: {e}')
        return None

# Function to start a task
def start_task(gmp, task_id):
    try:
        gmp.start_task(task_id=task_id)
        print(f'Task {task_id} started successfully.')
    except GvmError as e:
        print(f'Failed to start task: {e}')

# Function to check if a task is completed
def is_task_completed(gmp, task_id):
    response = gmp.get_task(task_id)
    status = response.find('.//status').text
    return status == 'Done'

# Function to get the report ID of a completed task
def get_report_id(gmp, task_id):
    response = gmp.get_task(task_id)
    report_id = response.find('.//last_report/report').get('id')
    return report_id

# Function to export the report as PDF
def export_report_pdf(gmp, report_id, pdf_filename):
    try:
        pdf_report_format_id = "c402cc3e-b531-11e1-9163-406186ea4fc5"
        response = gmp.get_report(
            report_id=report_id, report_format_id=pdf_report_format_id, ignore_pagination=True, details=True
        )

        report_element = response.find("report")
        content = report_element.find("report_format").tail

        if not content:
            print(
                "Requested report is empty. Either the report does not contain any "
                "results or the necessary tools for creating the report are "
                "not installed.",
                file=sys.stderr,
            )
            return

        binary_base64_encoded_pdf = content.encode("ascii")
        binary_pdf = b64decode(binary_base64_encoded_pdf)
        pdf_path = Path(pdf_filename).expanduser()
        pdf_path.write_bytes(binary_pdf)

        print(f"Done. PDF created: {pdf_path}")
        return str(pdf_path)  # Return the path of the created PDF
    except GvmError as e:
        print(f"Failed to export report: {e}")
        return None

# Function to export the report as CSV
def export_report_csv(gmp, report_id, csv_filename):
    try:
        csv_report_format_id = "c1645568-627a-11e3-a660-406186ea4fc5"
        response = gmp.get_report(
            report_id=report_id, report_format_id=csv_report_format_id, ignore_pagination=True, details=True
        )

        report_element = response.find("report")
        content = report_element.find("report_format").tail

        if not content:
            print(
                "Requested report is empty. Either the report does not contain any "
                "results or the necessary tools for creating the report are "
                "not installed.",
                file=sys.stderr,
            )
            return

        binary_base64_encoded_csv = content.encode("ascii")
        binary_csv = b64decode(binary_base64_encoded_csv)
        csv_path = Path(csv_filename).expanduser()
        csv_path.write_bytes(binary_csv)

        print(f"Done. CSV created: {csv_path}")
        return str(csv_path)  # Return the path of the created CSV
    except GvmError as e:
        print(f"Failed to export report: {e}")
        return None

# Function to convert CSV to JSON
def csv_to_json(csv_filename, json_filename):
    try:
        data = []
        with open(csv_filename, mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                data.append(row)

        with open(json_filename, mode='w') as json_file:
            json.dump(data, json_file, indent=4)

        print(f"Done. JSON created: {json_filename}")
        return str(json_filename)  # Return the path of the created JSON
    except Exception as e:
        print(f"Failed to convert CSV to JSON: {e}")
        return None

# Function to get the task progress
def get_task_progress(gmp, task_id):
    response = gmp.get_task(task_id)
    progress = response.find('.//progress').text
    return int(progress)

# Function to orchestrate the workflow
def main(ip, ports, target_name, task_name):
    try:
        path = '/run/gvmd/gvmd.sock'
        connection = UnixSocketConnection(path=path)
        transform = EtreeCheckCommandTransform()
        username = ''    # Enter the admin username here provided by greenbone
        password = ''    # Enter the admin password here provided by greenbone

        with Gmp(connection=connection, transform=transform) as gmp:
            gmp.authenticate(username, password)
            
            # List scanners and get the OpenVAS default scanner ID
            scanner_id = list_scanners(gmp)
            if not scanner_id:
                print('No scanners found.')
                sys.exit(1)

            # List scan configurations and get the OpenVAS default scan config ID
            config_id = list_scan_configs(gmp)
            if not config_id:
                print('No scan configurations found.')
                sys.exit(1)

            # Create a target
            target_id = create_target(gmp, target_name, ip, ports)
            if target_id:
                print(f'Target {target_name} created successfully. ID: {target_id}')

                # Create a task using the created target and OpenVAS default scan config
                task_id = create_task(gmp, task_name, scanner_id, target_id, config_id)
                if task_id:
                    print(f'Task {task_name} created successfully. ID: {task_id}')

                    # Start the task
                    start_task(gmp, task_id)

                    # Wait for the task to complete
                    while not is_task_completed(gmp, task_id):
                        progress = get_task_progress(gmp, task_id)
                        print(f"Scanning is in progress... {progress}% complete.")
                        time.sleep(30)  # Wait for 30 seconds before checking again

                    print(f'Task {task_name} completed.')

                    # Get the report ID
                    report_id = get_report_id(gmp, task_id)
                    if not report_id:
                        print(f"Failed to find report for task {task_name}")
                        sys.exit(1)
                        
                    pdf_filename = f"{task_name}_report.pdf"
                    pdf_path = export_report_pdf(gmp, report_id, pdf_filename)


                    # Export the report as CSV
                    csv_filename = f"{task_name}_report.csv"
                    csv_path = export_report_csv(gmp, report_id, csv_filename)
                    
                    json_filename = f"{task_name}_report.json"
                    json_path = csv_to_json(csv_filename, json_filename)

                    return csv_path
                else:
                    print(f'Failed to create task {task_name}.')
            else:
                print(f'Failed to create target {target_name}.')
    
    except GvmError as e:
        print(f'An error occurred: {e}')
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python3 automation_script.py <target_ip> <ports> <target_name> <task_name>")
        sys.exit(1)
    
    ip = sys.argv[1]
    ports = sys.argv[2]
    target_name = sys.argv[3]
    task_name = sys.argv[4]
    main(ip, ports, target_name, task_name)

