
CMD_WAIT = 2

import paramiko
import time


def get_ssh_cmd_output(host, user, password, config_cmds, cmd_wait=CMD_WAIT):
    """
    Utility to execute commands on device and return the output

    Args:
        host(str): IP address of device.
        user(str): username for device login.
        password(str): password for device login.
        config_cmds(list): list of commands to execute on the device.
    Returns:
        str: output of command executed on the device
    """
    ssh = get_ssh_connection(host, user, password)
    output = run_commands_ssh(ssh, config_cmds, cmd_wait)
    ssh.close()
    return output


def get_ssh_connection(host, user, pwd):
    """
    Utility to get ssh connection object
    Args:
        host(str): IP address of device.
        user(str): username for device login.
        pwd(str): password for device login
    Returns:
        obj: ssh connection object
    """
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        paramiko.util.log_to_file("filename.log")
        ssh.connect(hostname=host, username=user, password=pwd)
        return ssh
    except paramiko.AuthenticationException:
        print("Authentication failed, please verify your credentials")
        return None


def run_commands_ssh(ssh, cmd_list, cmd_wait=CMD_WAIT):
    """
    Utility to run commands using paramiko ssh connection
    Args:
        ssh(obj): ssh connection object
        cmd_list(list): list of commands
    Returns:
        str: Output of show command
    """
    try:
        channel = ssh.invoke_shell()
        for cmd in cmd_list:
            channel.send(cmd)
            time.sleep(cmd_wait)
        out = channel.recv(99999999)
        result = out.decode("ascii")
    except paramiko.AuthenticationException:
        result = None
    return result
