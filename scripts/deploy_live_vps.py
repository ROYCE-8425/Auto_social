"""Deploy the current Git HEAD to a VPS without committing runtime secrets.

Required environment variables:
  SEOTRUM_VPS_HOST
  SEOTRUM_VPS_PASSWORD or SEOTRUM_VPS_KEY_FILE

Optional:
  SEOTRUM_VPS_PORT, SEOTRUM_VPS_USER, SEOTRUM_REMOTE_ROOT,
  SEOTRUM_RESTART_COMMAND
"""
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

import paramiko


ROOT = Path(__file__).resolve().parents[1]
VPS_HOST = os.getenv("SEOTRUM_VPS_HOST")
VPS_PORT = int(os.getenv("SEOTRUM_VPS_PORT", "22"))
VPS_USER = os.getenv("SEOTRUM_VPS_USER", "root")
VPS_PASS = os.getenv("SEOTRUM_VPS_PASSWORD")
VPS_KEY_FILE = os.getenv("SEOTRUM_VPS_KEY_FILE")
REMOTE_ROOT = os.getenv("SEOTRUM_REMOTE_ROOT", "/root/Auto_social")
RESTART_COMMAND = os.getenv("SEOTRUM_RESTART_COMMAND", "systemctl restart javis.service")


def _connect() -> paramiko.SSHClient:
    if not VPS_HOST:
        raise SystemExit("Set SEOTRUM_VPS_HOST before running this script.")
    if not VPS_PASS and not VPS_KEY_FILE:
        raise SystemExit("Set SEOTRUM_VPS_PASSWORD or SEOTRUM_VPS_KEY_FILE before running this script.")

    kwargs = {
        "hostname": VPS_HOST,
        "port": VPS_PORT,
        "username": VPS_USER,
        "timeout": 30,
    }
    if VPS_KEY_FILE:
        kwargs["key_filename"] = VPS_KEY_FILE
    else:
        kwargs["password"] = VPS_PASS

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(**kwargs)
    return ssh


def _run(ssh: paramiko.SSHClient, command: str) -> None:
    stdin, stdout, stderr = ssh.exec_command(command)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    if out.strip():
        print(out.strip())
    if code != 0:
        raise RuntimeError(f"Remote command failed ({code}): {command}\n{err}")
    if err.strip():
        print(err.strip())


def _make_archive() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="seotrum-deploy-")) / "source.tar"
    subprocess.run(["git", "archive", "--format=tar", "-o", str(tmp), "HEAD"], cwd=ROOT, check=True)
    return tmp


def main() -> None:
    archive = _make_archive()
    remote_archive = "/tmp/seotrum-source.tar"
    ssh = _connect()
    try:
        print(f"Uploading source archive to {VPS_HOST}:{REMOTE_ROOT}")
        sftp = ssh.open_sftp()
        try:
            sftp.put(str(archive), remote_archive)
        finally:
            sftp.close()

        _run(ssh, f"mkdir -p {REMOTE_ROOT}")
        _run(ssh, f"tar -xf {remote_archive} -C {REMOTE_ROOT}")
        _run(ssh, f"rm -f {remote_archive}")
        if RESTART_COMMAND:
            _run(ssh, RESTART_COMMAND)
        print("Deploy finished.")
    finally:
        ssh.close()


if __name__ == "__main__":
    main()
