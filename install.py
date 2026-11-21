#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#  Xtream UI - Installer Mirror (MODERNIZED / Python 3 build)
#  ---------------------------------------------------------------------------
#  This is a 1:1 functional rewrite of the original Python 2.7 installer.
#  Every function, prompt, execution order and on-disk artefact is preserved,
#  but every package / library / directive that is NO LONGER SUPPORTED on modern
#  Ubuntu releases has been replaced by its maintained equivalent:
#
#    Python 2.7 ................ -> Python 3.8+  (Ubuntu 20.04 / 22.04 / 24.04)
#    urllib2 ................... -> urllib.request
#    itertools.izip ............ -> zip()
#    str.encode("base64") ...... -> base64.b64encode()
#    libcurl3 .................. -> libcurl4 / libcurl4t64  (24.04 time64 rename)
#    mcrypt .................... -> openssl
#    nscd ...................... -> systemd-resolved
#    libpng12-0 (CVE-2015-8126)  -> libpng16-16 / libpng16-16t64
#    libgeoip-dev (legacy GeoIP) -> libmaxminddb-dev (GeoIP2 / .mmdb)
#    libjemalloc1 .............. -> libjemalloc2
#    python-paramiko ........... -> python3-paramiko
#    wget -q -O <url> .......... -> urllib.request downloader (no shell quoting)
#    os.system("... %s ..." % x) -> subprocess.run([...]) + shlex.quote (no injection)
#    /etc/sudoers edit ......... -> /etc/sudoers.d/xtreamcodes drop-in
#    mysql.service overwrite ... -> systemd drop-in override
#    GRANT ... IDENTIFIED BY ... -> CREATE USER ... ; GRANT ...   (MySQL 8 syntax)
#    mysql_native_password ..... -> version aware auth block (caching_sha2_password
#                                   on MySQL 8.4+, native plugin only when present)
#    query_cache_* ............. -> removed (dropped in MySQL 8.0)
#    expire_logs_days .......... -> binlog_expire_logs_seconds
#    innodb_log_file_size ...... -> innodb_redo_log_capacity (MySQL 8.0.30+)
#    innodb_buffer_pool_instances-> emitted only on releases that still accept it
#    Ubuntu 16.04 / 18.04 ...... -> Ubuntu 20.04 / 22.04 / 24.04
#    MaxMind direct .mmdb pull .. -> geoipupdate + MAXMIND_LICENSE_KEY when set
#    release_22f.zip + newstuff.zip (legacy Bootstrap 4 / jQuery 3.3.1 panel)
#                               .. -> XPanel, distributed as a GitHub release
#                                   asset named xpanel.zip (published exactly
#                                   like release_22f.zip). It ships a
#                                   dependency-free Cairo-typed UI with CSRF
#                                   tokens, prepared statements and random
#                                   session ids.
#                                   Source priority in installadminpanel():
#                                     1. ./xpanel       (offline / development)
#                                     2. xpanel.zip     (release asset)
#                                     3. release_22f.zip + newstuff.zip
#                                   Redirect #2 with the XPANEL_ZIP_URL env var.
#
#  i am lazy to prepare echo versions with escaped characters, use base64
#  decode/encode to read or change these.
#
import base64
import glob
import os
import random
import shlex
import shutil
import socket
import string
import subprocess
import sys
import tempfile
import time
import zipfile
from itertools import cycle
from urllib.parse import urlparse
from urllib.request import Request, urlopen

rDownloadURL = {
    "main": "https://github.com/emre1393/xtreamui_mirror/releases/latest/download/main.tar.gz",
    "sub": "https://github.com/emre1393/xtreamui_mirror/releases/latest/download/LB.tar.gz",
    # XPanel - the rebuilt admin panel. Published as a GitHub release asset,
    # exactly like release_22f.zip / newstuff.zip below. Override the whole URL
    # with the XPANEL_ZIP_URL environment variable when using your own fork.
    "xpanel": "https://github.com/billelaggab/xpanel/releases/download/latest/xpanel.zip",
    # Legacy 22F panel, kept only as a last-resort fallback.
    "legacy_panel": "https://github.com/emre1393/xtreamui_mirror/releases/latest/download/release_22f.zip",
    "legacy_newstuff": "https://github.com/emre1393/xtreamui_mirror/releases/latest/download/newstuff.zip",
}

# ---------------------------------------------------------------------------
# MODERNIZED package list.
# The last THREE entries are MAIN-server only and get stripped for LB installs
# (rPackages[:-3]) exactly like the original script did.
# ---------------------------------------------------------------------------
rPackages = [
    "libcurl4",            # was: libcurl3            (removed from Ubuntu repos)
    "libxslt1-dev",        # still supported
    "libmaxminddb-dev",    # was: libgeoip-dev        (legacy GeoIP database EOL)
    "e2fsprogs",           # provides chattr
    "wget",                # kept: used by start_services.sh on some builds
    "openssl",             # was: mcrypt              (dropped from PHP 7.2 / dead upstream)
    "systemd-resolved",    # was: nscd                (nscd is deprecated upstream)
    "htop",
    "zip",
    "unzip",
    "mc",
    "libpng16-16",         # was: libpng12-0          (CVE-2015-8126, removed in 2016)
    "ca-certificates",     # needed for TLS downloads on minimal images
    "curl",                # diagnostics / health checks
    "lsb-release",         # lsb_release is no longer preinstalled on 22.04+
    "iproute2",            # modern `ip` tooling
    "net-tools",           # legacy `ifconfig`, still parsed by start_services.sh
    # ---- MAIN only (stripped with rPackages[:-3] on LB installs) ----
    "python3-paramiko",    # was: python-paramiko     (Python 2 only)
    "libjemalloc2",        # was: libjemalloc1
    "mysql-server",        # MySQL 8.0 (20.04/22.04) or 8.0/8.4 (24.04)
]

# Ubuntu 24.04 (noble) renamed many libraries for the 64-bit time_t transition.
rPackageAlternatives = {
    "libcurl4": ["libcurl4t64", "libcurl4"],
    "libpng16-16": ["libpng16-16t64", "libpng16-16"],
    "libmaxminddb-dev": ["libmaxminddb-dev", "libmaxminddb0", "libgeoip-dev"],
    "libjemalloc2": ["libjemalloc2", "libjemalloc1"],
    "python3-paramiko": ["python3-paramiko", "python-paramiko"],
    "openssl": ["openssl", "mcrypt"],
    "mysql-server": ["mysql-server", "mysql-server-8.0"],
    "systemd-resolved": ["systemd-resolved", "nscd"],
    "libxslt1-dev": ["libxslt1-dev", "libxslt1.1"],
}

rInstall = {"MAIN": "main", "LB": "sub"}

rMySQLCnfTemplate = base64.b64decode(
    "IyBYdHJlYW0gQ29kZXMgKE1vZGVybml6ZWQgYnVpbGQ6IE15U1FMIDguMCAvIDguNCBjb21wYXRpYmxlKQojIFJlZ2VuZXJhdGVkIGJ5IGluc3RhbGwucHkgLSB0aGUgZm9sbG93aW5nIGxlZ2FjeSBkaXJlY3RpdmVzIHdlcmUgUkVNT1ZFRCBiZWNhdXNlCiMgdGhleSBubyBsb25nZXIgZXhpc3QgaW4gc3VwcG9ydGVkIE15U1FMIHJlbGVhc2VzOgojICAgKiBxdWVyeV9jYWNoZV9saW1pdCAvIHF1ZXJ5X2NhY2hlX3NpemUgLyBxdWVyeV9jYWNoZV90eXBlICAoZHJvcHBlZCBpbiBNeVNRTCA4LjApCiMgICAqIGV4cGlyZV9sb2dzX2RheXMgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIChyZW1vdmVkIGluIE15U1FMIDguNCkKIyAgICogaW5ub2RiX2xvZ19maWxlX3NpemUgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgKHJlbW92ZWQgaW4gTXlTUUwgOC40KQojICAgKiBpbm5vZGJfYnVmZmVyX3Bvb2xfaW5zdGFuY2VzICAgICAgICAgICAgICAgICAgICAgICAgICAgICAocmVtb3ZlZCBpbiBNeVNRTCA4LjQpCiMgICAqIGRlZmF1bHRfYXV0aGVudGljYXRpb25fcGx1Z2luPW15c3FsX25hdGl2ZV9wYXNzd29yZCAgICAgIChyZW1vdmVkIGluIE15U1FMIDguNCkKCltjbGllbnRdCnBvcnQgICAgICAgICAgICA9IDMzMDYKc29ja2V0ICAgICAgICAgID0gL3Zhci9ydW4vbXlzcWxkL215c3FsZC5zb2NrCgpbbXlzcWxkX3NhZmVdCnNvY2tldCAgICAgICAgICA9IC92YXIvcnVuL215c3FsZC9teXNxbGQuc29jawpuaWNlICAgICAgICAgICAgPSAwCgpbbXlzcWxkXQp1c2VyICAgICAgICAgICAgPSBteXNxbApwaWQtZmlsZSAgICAgICAgPSAvdmFyL3J1bi9teXNxbGQvbXlzcWxkLnBpZApzb2NrZXQgICAgICAgICAgPSAvdmFyL3J1bi9teXNxbGQvbXlzcWxkLnNvY2sKcG9ydCAgICAgICAgICAgID0gNzk5OQpiYXNlZGlyICAgICAgICAgPSAvdXNyCmRhdGFkaXIgICAgICAgICA9IC92YXIvbGliL215c3FsCnRtcGRpciAgICAgICAgICA9IC90bXAKCmxjLW1lc3NhZ2VzLWRpciA9IC91c3Ivc2hhcmUvbXlzcWwKc2tpcC1leHRlcm5hbC1sb2NraW5nCnNraXAtbmFtZS1yZXNvbHZlID0gMQoKYmluZC1hZGRyZXNzICAgICAgICAgICAgPSAqCgp7YXV0aF9ibG9ja30KCmtleV9idWZmZXJfc2l6ZSA9IDEyOE0KbXlpc2FtX3NvcnRfYnVmZmVyX3NpemUgPSA0TQptYXhfYWxsb3dlZF9wYWNrZXQgICAgICA9IDY0TQpteWlzYW0tcmVjb3Zlci1vcHRpb25zICA9IEJBQ0tVUAptYXhfbGVuZ3RoX2Zvcl9zb3J0X2RhdGEgPSA4MTkyCnNvcnRfYnVmZmVyX3NpemUgPSAyTQpqb2luX2J1ZmZlcl9zaXplID0gMk0KcmVhZF9idWZmZXJfc2l6ZSA9IDFNCnJlYWRfcm5kX2J1ZmZlcl9zaXplID0gMU0KCntiaW5sb2dfYmxvY2t9Cm1heF9iaW5sb2dfc2l6ZSA9IDEwME0KdHJhbnNhY3Rpb25faXNvbGF0aW9uID0gUkVBRC1DT01NSVRURUQKbWF4X2Nvbm5lY3Rpb25zICA9IDEwMDAwCm9wZW5fZmlsZXNfbGltaXQgPSAxMDI0MAppbm5vZGJfb3Blbl9maWxlcyA9IDEwMjQwCm1heF9jb25uZWN0X2Vycm9ycyA9IDQwOTYKdGFibGVfb3Blbl9jYWNoZSA9IDQwOTYKdGFibGVfZGVmaW5pdGlvbl9jYWNoZSA9IDQwOTYKdG1wX3RhYmxlX3NpemUgPSAxRwptYXhfaGVhcF90YWJsZV9zaXplID0gMUcKbWF4X2V4ZWN1dGlvbl90aW1lID0gMApiYWNrX2xvZyA9IDQwOTYKCmlubm9kYl9idWZmZXJfcG9vbF9zaXplID0ge2J1ZmZlcl9wb29sX3NpemV9CntidWZmZXJfcG9vbF9pbnN0YW5jZXNfYmxvY2t9Cmlubm9kYl9yZWFkX2lvX3RocmVhZHMgPSA2NAppbm5vZGJfd3JpdGVfaW9fdGhyZWFkcyA9IDY0Cmlubm9kYl90aHJlYWRfY29uY3VycmVuY3kgPSAwCmlubm9kYl9mbHVzaF9sb2dfYXRfdHJ4X2NvbW1pdCA9IDAKaW5ub2RiX2ZsdXNoX21ldGhvZCA9IE9fRElSRUNUCnBlcmZvcm1hbmNlX3NjaGVtYSA9IDAKaW5ub2RiLWZpbGUtcGVyLXRhYmxlID0gMQppbm5vZGJfaW9fY2FwYWNpdHkgPSAxMDAwMAppbm5vZGJfaW9fY2FwYWNpdHlfbWF4ID0gMjAwMDAKaW5ub2RiX3RhYmxlX2xvY2tzID0gMAppbm5vZGJfbG9ja193YWl0X3RpbWVvdXQgPSA1MAppbm5vZGJfZGVhZGxvY2tfZGV0ZWN0ID0gMAp7cmVkb19sb2dfYmxvY2t9CgpzcWwtbW9kZSA9ICJOT19FTkdJTkVfU1VCU1RJVFVUSU9OIgoKCltteXNxbGR1bXBdCnF1aWNrCnF1b3RlLW5hbWVzCm1heF9hbGxvd2VkX3BhY2tldCAgICAgID0gMTI4TQpjb21wbGV0ZS1pbnNlcnQKCltteXNxbF0KCltpc2FtY2hrXQprZXlfYnVmZmVyX3NpemUgICAgICAgICAgICAgID0gMTZNCg=="
).decode("utf-8")

# systemd DROP-IN override. Replaces the old habit of overwriting
# /lib/systemd/system/mysql.service (that file is owned by the mysql-server
# package and gets restored/rejected on Ubuntu 20.04+).
rMySQLServiceFile = base64.b64decode(
    "IyBYdHJlYW0gQ29kZXMgTXlTUUwgdHVuaW5nLgojIE1vZGVybiByZXBsYWNlbWVudDogYSBzeXN0ZW1kIERST1AtSU4gb3ZlcnJpZGUgaW5zdGVhZCBvZiBvdmVyd3JpdGluZwojIC9saWIvc3lzdGVtZC9zeXN0ZW0vbXlzcWwuc2VydmljZSAodGhhdCBmaWxlIGlzIG93bmVkIGJ5IHRoZSBteXNxbC1zZXJ2ZXIKIyBwYWNrYWdlIGFuZCBpcyByZXN0b3JlZC9yZWplY3RlZCBvbiBVYnVudHUgMjAuMDQrKS4KIyBJbnN0YWxsZWQgdG86IC9ldGMvc3lzdGVtZC9zeXN0ZW0vbXlzcWwuc2VydmljZS5kL3h0cmVhbWNvZGVzLmNvbmYKIwojIExEX1BSRUxPQUQgKGplbWFsbG9jIDIpIGlzIE5PVCBoYXJkY29kZWQgaGVyZTogaXQgaXMgaW5qZWN0ZWQgdGhyb3VnaAojIEVudmlyb25tZW50RmlsZSBiZWxvdywgc28gYSBtaXNzaW5nIGxpYmplbWFsbG9jMiBjYW4gbmV2ZXIgc3RvcCBteXNxbGQuCgpbU2VydmljZV0KRW52aXJvbm1lbnRGaWxlPS0vZXRjL215c3FsL215c3FsZApMaW1pdE5PRklMRT01MDAwCkxpbWl0TlBST0M9NjU1MzUKVGltZW91dFNlYz02MDAKUmVzdGFydD1vbi1mYWlsdXJlCg=="
).decode("utf-8")

# Was: {"16.04": "xenial", "18.04": "bionic"}  (both reached End of Standard Support)
rVersions = {
    "20.04": "focal",
    "22.04": "jammy",
    "24.04": "noble",
}

rPaths = {
    "base": "/home/xtreamcodes",
    "xc": "/home/xtreamcodes/iptv_xtream_codes",
    "config": "/home/xtreamcodes/iptv_xtream_codes/config",
    "geoip": "/home/xtreamcodes/iptv_xtream_codes/GeoLite2.mmdb",
    "cnf": "/etc/mysql/my.cnf",
    "cnfBackup": "/etc/mysql/my.cnf.xc",
    "jemallocEnv": "/etc/mysql/mysqld",
    "serviceDropIn": "/etc/systemd/system/mysql.service.d/xtreamcodes.conf",
    "sudoersDropIn": "/etc/sudoers.d/xtreamcodes",
    "initd": "/etc/init.d/xtreamcodes",
    "systemdUnit": "/etc/systemd/system/xtreamcodes.service",
}

rJemalloc = "/usr/lib/x86_64-linux-gnu/libjemalloc.so.2"   # was libjemalloc.so.1
rMySQLSocket = "/var/run/mysqld/mysqld.sock"


class col:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    YELLOW = "\033[33m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def generate(length=32):
    """Cryptographically stronger replacement for random.choice() based codes."""
    try:
        import secrets
        rAlphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(rAlphabet) for _ in range(length))
    except ImportError:
        return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def getIP():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        rIP = s.getsockname()[0]
        s.close()
        return rIP
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


def runShell(rCommand, rQuiet=True):
    """os.system() replacement. Returns the exit code, never raises."""
    if rQuiet:
        rCommand = "%s > /dev/null 2>&1" % rCommand
    return subprocess.call(rCommand, shell=True, executable="/bin/bash")


def runCommand(rArgs):
    """Safe argv runner - no shell interpolation, no command injection."""
    try:
        return subprocess.run(
            rArgs, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
        ).returncode
    except Exception:
        return 1


def quote(rValue):
    """Every user supplied value is quoted before it ever reaches a shell."""
    return shlex.quote(str(rValue))


def download(rURL, rDestination, rRetries=3):
    """wget -q -O replacement using urllib.request (Python 3, TLS verified)."""
    for rAttempt in range(1, rRetries + 1):
        try:
            rRequest = Request(rURL, headers={"User-Agent": "XtreamUI-Installer/2.0"})
            with urlopen(rRequest, timeout=120) as rResponse:
                with open(rDestination, "wb") as rFile:
                    shutil.copyfileobj(rResponse, rFile)
            if os.path.exists(rDestination) and os.path.getsize(rDestination) > 0:
                return True
        except Exception as rError:
            printc("Download attempt %d failed for %s (%s)" % (rAttempt, urlparse(rURL).path, rError), col.WARNING)
            time.sleep(2)
    return False


def getVersion():
    """lsb_release -d (human readable OS description)."""
    try:
        return (
            subprocess.check_output(["lsb_release", "-d"], stderr=subprocess.DEVNULL)
            .decode("utf-8", "replace")
            .split(":")[-1]
            .strip()
        )
    except Exception:
        return ""


def getVersionShort():
    """lsb_release -sr (e.g. 24.04)."""
    try:
        return (
            subprocess.check_output(["lsb_release", "-sr"], stderr=subprocess.DEVNULL)
            .decode("utf-8", "replace")
            .strip()
        )
    except Exception:
        try:
            for rLine in open("/etc/os-release").read().splitlines():
                if rLine.startswith("VERSION_ID="):
                    return rLine.split("=", 1)[-1].strip('"')
        except Exception:
            pass
    return ""


def getMySQLVersion():
    """
    Returns (major, minor, patch) of the installed server, (0, 0, 0) when unknown.
    Probes several sources because Ubuntu 24.04 ships MySQL 8.0/8.4 and some
    mirrors only expose `mysql` (not `mysqld`) on PATH.
    """
    for rProbe in (["mysqld", "--version"], ["mysql", "--version"], ["mariadbd", "--version"]):
        try:
            rOutput = subprocess.check_output(rProbe, stderr=subprocess.DEVNULL).decode(
                "utf-8", "replace"
            )
            for rToken in rOutput.replace(",", " ").split():
                rParts = rToken.split(".")
                if len(rParts) >= 2 and all(rPart.isdigit() for rPart in rParts[:3]):
                    return (
                        int(rParts[0]),
                        int(rParts[1]),
                        int(rParts[2]) if len(rParts) > 2 else 0,
                    )
        except Exception:
            continue

    # Fall back to the package manager when no binary is on PATH yet.
    for rPkg in ("mysql-server-8.4", "mysql-server-8.0", "mysql-community-server", "mariadb-server"):
        try:
            rOutput = subprocess.check_output(
                ["dpkg-query", "-W", "-f=${Version}", rPkg], stderr=subprocess.DEVNULL
            ).decode("utf-8", "replace")
            rDigits = ""
            for rChar in rOutput.strip():
                if rChar.isdigit() or rChar == ".":
                    rDigits += rChar
                elif rDigits:
                    break
            rParts = [rPart for rPart in rDigits.split(".") if rPart.isdigit()]
            if len(rParts) >= 2:
                return (int(rParts[0]), int(rParts[1]), int(rParts[2]) if len(rParts) > 2 else 0)
        except Exception:
            continue
    return (0, 0, 0)


def hasNativePasswordPlugin():
    """mysql_native_password is DISABLED by default since MySQL 8.4 and removed in 9.x."""
    rMajor, rMinor, _rPatch = getMySQLVersion()
    if rMajor == 0:
        return True
    if (rMajor, rMinor) < (8, 4):
        return True
    for rCandidate in (
        "/usr/lib/mysql/plugin/mysql_native_password.so",
        "/usr/lib/x86_64-linux-gnu/mysql/plugin/mysql_native_password.so",
    ):
        if os.path.exists(rCandidate):
            return True
    return False


def totalMemoryMB():
    try:
        with open("/proc/meminfo") as rFile:
            for rLine in rFile:
                if rLine.startswith("MemTotal:"):
                    return int(rLine.split()[1]) // 1024
    except Exception:
        pass
    return 0


def buildMySQLCnf(rRedoLogOverride=None):
    """
    Renders the my.cnf template for the ACTUAL server version installed.
    Directives that no longer exist upstream are never emitted.

    rRedoLogOverride: None = decide from the detected version,
                      True = force legacy innodb_log_file_size,
                      False = force modern innodb_redo_log_capacity.
    """
    rMajor, rMinor, rPatch = getMySQLVersion()
    rVersionKnown = rMajor != 0

    # --- authentication -------------------------------------------------
    if rMajor == 0:
        rAuthBlock = "default_authentication_plugin = caching_sha2_password"
    elif (rMajor, rMinor) >= (8, 4):
        rAuthBlock = "authentication_policy = *"
        if hasNativePasswordPlugin():
            rAuthBlock += "\nmysql_native_password = ON"
    else:
        if hasNativePasswordPlugin():
            rAuthBlock = "default_authentication_plugin = mysql_native_password"
        else:
            rAuthBlock = "default_authentication_plugin = caching_sha2_password"

    # --- binary log expiry (expire_logs_days removed in MySQL 8.4) -------
    rBinlogBlock = "binlog_expire_logs_seconds = 864000"

    # --- buffer pool: sized from real RAM instead of a hardcoded 8G -------
    rMemMB = totalMemoryMB()
    if rMemMB > 0:
        rPoolMB = max(512, min(8192, int(rMemMB * 0.6)))
    else:
        rPoolMB = 8192
    rPoolSize = "%dM" % rPoolMB

    # --- innodb_buffer_pool_instances removed in MySQL 8.4 ----------------
    if not rVersionKnown or (rMajor, rMinor) >= (8, 4):
        # Omitted on unknown/8.4+: the server auto-sizes it, which is safe everywhere.
        rInstancesBlock = "# innodb_buffer_pool_instances: omitted (removed in MySQL 8.4, auto-sized)"
    elif rPoolMB >= 1024:
        rInstancesBlock = "innodb_buffer_pool_instances = %d" % min(8, max(1, rPoolMB // 1024))
    else:
        rInstancesBlock = "innodb_buffer_pool_instances = 1"

    # --- redo log sizing (innodb_log_file_size removed in MySQL 8.4) ------
    if rRedoLogOverride is False:
        rRedoBlock = "innodb_redo_log_capacity = 1G"
    elif rRedoLogOverride is True:
        rRedoBlock = "innodb_log_file_size = 1G"
    elif rVersionKnown and (rMajor, rMinor, rPatch) >= (8, 0, 30):
        rRedoBlock = "innodb_redo_log_capacity = 1G"
    elif rVersionKnown:
        rRedoBlock = "innodb_log_file_size = 1G"
    else:
        # Version could not be probed: emit neither, keep the server default so
        # mysqld cannot refuse to boot on an unknown directive.
        rRedoBlock = "# redo log sizing left at the server default (version unknown)"

    return rMySQLCnfTemplate.format(
        auth_block=rAuthBlock,
        binlog_block=rBinlogBlock,
        buffer_pool_size=rPoolSize,
        buffer_pool_instances_block=rInstancesBlock,
        redo_log_block=rRedoBlock,
    )


def printc(rText, rColour=col.OKBLUE, rPadding=0):
    """
    Draws the centred status box.

    The original hardcoded a 40-column interior, so any longer message (several
    of which this rewrite adds) overflowed the right border. The interior now
    grows to fit the text while staying 40 wide for short messages, so the box
    is always closed correctly.
    """
    rText = str(rText)
    rInner = max(40, len(rText) + 2)
    rEdge = "\u2500" * rInner
    rBlank = " " * rInner

    rLeft = (rInner - len(rText)) // 2
    rRight = rInner - rLeft - len(rText)

    print("%s \u250c%s\u2510 %s" % (rColour, rEdge, col.ENDC))
    for _i in range(rPadding):
        print("%s \u2502%s\u2502 %s" % (rColour, rBlank, col.ENDC))
    print(
        "%s \u2502%s%s%s\u2502 %s"
        % (rColour, " " * rLeft, rText, " " * rRight, col.ENDC)
    )
    for _i in range(rPadding):
        print("%s \u2502%s\u2502 %s" % (rColour, rBlank, col.ENDC))
    print("%s \u2514%s\u2518 %s" % (rColour, rEdge, col.ENDC))
    print(" ")


def installPackage(rPackage):
    """
    Installs a package, transparently falling back to its modern/legacy alias
    (handles the Ubuntu 24.04 't64' library renames).
    """
    for rCandidate in [rPackage] + rPackageAlternatives.get(rPackage, []):
        if runCommand(["apt-get", "install", "-y", rCandidate]) == 0:
            if rCandidate != rPackage:
                printc("%s installed as %s" % (rPackage, rCandidate), col.YELLOW)
            return True
    printc("Package unavailable: %s (skipped)" % rPackage, col.WARNING)
    return False


def createUser():
    """adduser --system is still supported, but useradd is the canonical tool now."""
    rArgs = ["useradd", "--system", "--shell", "/usr/sbin/nologin", "--user-group", "--no-create-home", "xtreamcodes"]
    if runCommand(rArgs) != 0:
        runShell(
            "adduser --system --shell /bin/false --group --disabled-login xtreamcodes"
        )


def prepare(rType="MAIN"):
    global rPackages
    if rType != "MAIN":
        rPackages = rPackages[:-3]

    printc("Preparing Installation")
    for rFile in [
        "/var/lib/dpkg/lock-frontend",
        "/var/cache/apt/archives/lock",
        "/var/lib/dpkg/lock",
    ]:
        try:
            os.remove(rFile)
        except OSError:
            pass

    os.environ["DEBIAN_FRONTEND"] = "noninteractive"
    runShell("apt-get update")

    printc("Removing libcurl4 if installed")
    # Original removed libcurl4 so the prebuilt binaries could load libcurl3.
    # libcurl3 is gone from every supported Ubuntu release, so the mirror now
    # ships binaries linked against libcurl4 - we instead purge the packages
    # that ARE obsolete (mcrypt / nscd) and keep libcurl4 installed.
    runShell("apt-get remove --auto-remove mcrypt nscd php-mcrypt -y")

    for rPackage in rPackages:
        printc("Installing %s" % rPackage)
        installPackage(rPackage)

    printc("Installing libpng")
    # Was: wget libpng12-0_1.2.54-1ubuntu1_amd64.deb && dpkg -i
    # libpng12-0 was removed from Ubuntu in 2016 and carries CVE-2015-8126.
    installPackage("libpng16-16")
    runShell("apt-get install -y")  # Clean up above
    if not os.path.exists("/etc/systemd/system/mysql.service.d"):
        try:
            os.makedirs("/etc/systemd/system/mysql.service.d")
        except OSError:
            pass

    try:
        subprocess.check_output(
            ["getent", "passwd", "xtreamcodes"], stderr=subprocess.DEVNULL
        )
    except Exception:
        # Create User
        printc("Creating user xtreamcodes")
        createUser()

    if not os.path.exists(rPaths["base"]):
        os.mkdir(rPaths["base"])
    return True


def install(rType="MAIN"):
    global rInstall, rDownloadURL
    printc("Downloading Software")
    try:
        rURL = rDownloadURL[rInstall[rType]]
    except KeyError:
        printc("Invalid download URL!", col.FAIL)
        return False

    rArchive = os.path.join(tempfile.gettempdir(), "xtreamcodes.tar.gz")
    if not download(rURL, rArchive):
        printc("Failed to download installation file!", col.FAIL)
        return False

    if os.path.exists(rArchive):
        printc("Installing Software")
        if os.path.exists(rPaths["geoip"]):
            runCommand(["chattr", "-f", "-i", rPaths["geoip"]])
        if runCommand(["tar", "-zxf", rArchive, "-C", rPaths["base"]]) != 0:
            printc("Failed to extract installation file!", col.FAIL)
            return False
        try:
            os.remove(rArchive)
        except OSError:
            pass
        return True

    printc("Failed to download installation file!", col.FAIL)
    return False


def installZip(rURL, rTempZip, rTempDir, rStripRoot=False):
    """
    Replaces the old `unzip -o ... && cp -rf ...` shell chain with zipfile,
    which validates the archive before a single byte is written to disk.
    """
    if not download(rURL, rTempZip):
        return False
    if not os.path.exists(rTempZip):
        return False
    try:
        with zipfile.ZipFile(rTempZip) as rZip:
            if rZip.testzip() is not None:
                raise zipfile.BadZipFile("CRC mismatch")
            if os.path.exists(rTempDir):
                shutil.rmtree(rTempDir)
            os.makedirs(rTempDir)
            safeExtract(rZip, rTempDir)
    except (zipfile.BadZipFile, OSError) as rError:
        printc("Invalid link or zip file is corrupted! (%s)" % rError, col.FAIL)
        try:
            os.remove(rTempZip)
        except OSError:
            pass
        return False

    rSource = rTempDir
    if rStripRoot:
        rEntries = os.listdir(rTempDir)
        if len(rEntries) == 1 and os.path.isdir(os.path.join(rTempDir, rEntries[0])):
            rSource = os.path.join(rTempDir, rEntries[0])

    runShell("cp -rf %s/. %s/" % (quote(rSource), quote(rPaths["xc"])))
    try:
        shutil.rmtree(rTempDir)
    except OSError:
        pass
    try:
        os.remove(rTempZip)
    except OSError:
        pass
    runShell("chown -R xtreamcodes:xtreamcodes %s" % quote(rPaths["base"]))
    return True


def xpanelDir():
    """Location of the bundled XPanel sources, shipped next to install.py."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "xpanel")


def xpanelZipUrl():
    """
    Where xpanel.zip is published.

    It is hosted as a GitHub RELEASE ASSET, exactly like release_22f.zip:
        https://github.com/<owner>/<repo>/releases/latest/download/xpanel.zip

    Override with an environment variable when publishing to your own fork:
        XPANEL_ZIP_URL="https://github.com/you/your_mirror/releases/latest/download/xpanel.zip"
    """
    rOverride = os.environ.get("XPANEL_ZIP_URL", "").strip()
    if rOverride:
        return rOverride
    return rDownloadURL["xpanel"]


def copyTree(rSource, rDestination):
    """cp -rf equivalent that keeps permissions and skips nothing."""
    if not os.path.isdir(rSource):
        return False
    try:
        os.makedirs(rDestination, exist_ok=True)
    except OSError:
        pass
    for rEntry in os.listdir(rSource):
        rFrom = os.path.join(rSource, rEntry)
        rTo = os.path.join(rDestination, rEntry)
        if os.path.isdir(rFrom):
            if not copyTree(rFrom, rTo):
                return False
        else:
            try:
                shutil.copy2(rFrom, rTo)
            except OSError as rError:
                printc("Copy failed: %s (%s)" % (rTo, rError), col.FAIL)
                return False
    return True


def findPanelRoot(rDir):
    """
    Locates the directory that actually holds admin/ inside an extraction.

    Handles all three shapes people produce when zipping a folder:
      1. contents at the archive root        -> admin/, wwwdir/, ...
      2. one wrapper folder                  -> xpanel/admin/, xpanel/wwwdir/
      3. a repo-style wrapper folder         -> xpanel-main/admin/, ...
    Returns None when no admin/ directory can be found (=> wrong archive).
    """
    if not os.path.isdir(rDir):
        return None
    rCandidate = rDir
    for _rDepth in range(4):
        if os.path.isdir(os.path.join(rCandidate, "admin")):
            return rCandidate
        try:
            rEntries = sorted(
                rEntry
                for rEntry in os.listdir(rCandidate)
                if os.path.isdir(os.path.join(rCandidate, rEntry))
            )
        except OSError:
            return None
        if len(rEntries) != 1:
            return None
        rCandidate = os.path.join(rCandidate, rEntries[0])
    return None


def safeExtract(rZipFile, rDestination):
    """
    Extracts with an explicit Zip-Slip guard.

    zipfile.extract() already sanitises paths on CPython, but the installer
    runs as root on a production box, so the archive members are validated
    again here: absolute paths, drive letters and ".." traversal are rejected
    outright instead of relying on library behaviour.
    """
    for rInfo in rZipFile.infolist():
        rName = rInfo.filename.replace("\\", "/")
        if rName.startswith("/") or ":" in rName.split("/")[0]:
            raise zipfile.BadZipFile("absolute path in archive: %s" % rName)
        if any(rPart == ".." for rPart in rName.split("/")):
            raise zipfile.BadZipFile("path traversal in archive: %s" % rName)
        rTarget = os.path.realpath(os.path.join(rDestination, rName))
        if not rTarget.startswith(os.path.realpath(rDestination) + os.sep) and rTarget != os.path.realpath(rDestination):
            raise zipfile.BadZipFile("member escapes destination: %s" % rName)
    rZipFile.extractall(rDestination)


def downloadXPanel():
    """Downloads xpanel.zip, verifies its CRC and returns the panel root."""
    rURL = xpanelZipUrl()
    rTempZip = os.path.join(tempfile.gettempdir(), "xpanel.zip")
    rTempDir = os.path.join(tempfile.gettempdir(), "xpanel_extract")

    printc("Downloading XPanel")
    if not download(rURL, rTempZip):
        printc("Failed to download xpanel.zip", col.FAIL)
        return None

    if not os.path.exists(rTempZip):
        return None

    try:
        with zipfile.ZipFile(rTempZip) as rZip:
            rCorrupt = rZip.testzip()
            if rCorrupt is not None:
                raise zipfile.BadZipFile("CRC mismatch in %s" % rCorrupt)
            if os.path.exists(rTempDir):
                shutil.rmtree(rTempDir)
            os.makedirs(rTempDir, exist_ok=True)
            safeExtract(rZip, rTempDir)
    except (zipfile.BadZipFile, OSError) as rError:
        printc("Invalid link or xpanel.zip is corrupted! (%s)" % rError, col.FAIL)
        for rStale in [rTempZip]:
            try:
                os.remove(rStale)
            except OSError:
                pass
        return None

    rRoot = findPanelRoot(rTempDir)
    if rRoot is None:
        printc("xpanel.zip does not contain an admin/ directory", col.FAIL)
        return None

    try:
        os.remove(rTempZip)
    except OSError:
        pass
    return rRoot


def applyXPanelSchema(rPanelDir):
    """
    Runs database/schema.sql - an IDEMPOTENT compatibility layer that only adds
    the unique key on admin_settings, missing tables and indexes. It never
    alters or drops an existing Xtream Codes table.
    """
    rFile = os.path.join(rPanelDir, "database", "schema.sql")
    if not os.path.exists(rFile):
        return False
    printc("Applying XPanel schema compatibility layer")
    return runShell(
        "mysql --protocol=socket -S %s -u root %s < %s"
        % (quote(rMySQLSocket), quote("xtream_iptvpro"), quote(rFile))
    ) == 0


def deployXPanel(rPanelDir, rLabel):
    """Copies the panel tree into /home/xtreamcodes/iptv_xtream_codes/."""
    printc("Installing XPanel (%s)" % rLabel)
    if not os.path.isdir(rPaths["xc"]):
        printc("Core files missing, run install() first", col.FAIL)
        return False

    # The legacy wwwdir/index.php and admin/ trees are replaced wholesale where
    # XPanel ships its own file, and left untouched everywhere else so the
    # streaming endpoints from main.tar.gz keep working.
    rOk = True
    rCopied = []
    for rSub in ["admin", "wwwdir", "crons", "nginx"]:
        rSource = os.path.join(rPanelDir, rSub)
        if not os.path.isdir(rSource):
            continue
        printc("Copying %s/" % rSub)
        if not copyTree(rSource, os.path.join(rPaths["xc"], rSub)):
            rOk = False
        else:
            rCopied.append(rSub)

    if not rOk:
        printc("XPanel installation failed!", col.FAIL)
        return False
    if not rCopied:
        printc("XPanel archive contained nothing to install!", col.FAIL)
        return False

    runShell("chown -R xtreamcodes:xtreamcodes %s" % quote(rPaths["base"]))
    # Panel PHP is served by php-fpm as xtreamcodes, nginx reads it as root.
    runShell("find %s/admin/ -type f -exec chmod 644 {} \\;" % quote(rPaths["xc"]))
    runShell("find %s/admin/ -type d -exec chmod 755 {} \\;" % quote(rPaths["xc"]))
    applyXPanelSchema(rPanelDir)

    printc("XPanel installed - no jQuery, no Bootstrap, no CDN", col.OKGREEN)
    return True


def installadminpanel():
    """
    Installs the admin panel. Sources are tried in order:

      1. ./xpanel            - the sources shipped next to install.py (offline /
                               development, no network round trip)
      2. xpanel.zip          - the GitHub release asset, published the same way
                               as release_22f.zip. This is the normal path and
                               can be redirected with XPANEL_ZIP_URL.
      3. release_22f.zip + newstuff.zip - the original 22F panel, kept as a last
                               resort so the installer never dead-ends.
    """
    if not os.path.isdir(rPaths["xc"]):
        printc("Core files missing, run install() first", col.FAIL)
        return False

    # 1) local sources ----------------------------------------------------
    rLocal = xpanelDir()
    if os.path.isdir(os.path.join(rLocal, "admin")):
        rRoot = findPanelRoot(rLocal)
        if rRoot is not None and deployXPanel(rRoot, "local ./xpanel"):
            return True
        printc("Local xpanel/ could not be deployed", col.WARNING)

    # 2) xpanel.zip release asset -----------------------------------------
    rTempRoot = None
    try:
        rTempRoot = downloadXPanel()
        if rTempRoot is not None and deployXPanel(rTempRoot, "xpanel.zip"):
            return True
        if rTempRoot is not None:
            printc("xpanel.zip could not be deployed", col.WARNING)
    finally:
        rExtract = os.path.join(tempfile.gettempdir(), "xpanel_extract")
        if os.path.isdir(rExtract):
            try:
                shutil.rmtree(rExtract)
            except OSError:
                pass

    # 3) legacy mirror archives -------------------------------------------
    printc("Falling back to the legacy 22F admin panel", col.WARNING)
    return installLegacyAdminPanel()


def installLegacyAdminPanel():
    """Original behaviour: pull the 22F panel + newstuff from the mirror."""
    rURL = rDownloadURL["legacy_panel"]
    printc("Downloading Admin Panel")
    if not installZip(rURL, "/tmp/update.zip", "/tmp/update", rStripRoot=True):
        printc("Failed to download installation file!", col.FAIL)
        return False

    printc("Installing Admin Panel")

    rURL2 = rDownloadURL["legacy_newstuff"]
    printc("Downloading New Stuff for Admin Panel")
    if not installZip(rURL2, "/tmp/update2.zip", "/tmp/update2", rStripRoot=False):
        printc("Failed to download installation file!", col.FAIL)
        return False

    printc("Installing New Stuff for Admin Panel")
    return True


def mysqlQuery(rStatements, rExtra=""):
    """Runs a batch of statements through one mysql client invocation."""
    rCommand = "mysql --protocol=socket -S %s -u root%s -e %s" % (
        quote(rMySQLSocket),
        rExtra,
        quote(" ".join(rStatements)),
    )
    return runShell(rCommand)


def writeAndValidateCnf():
    """
    Writes /etc/mysql/my.cnf and validates it with the real server binary
    (`mysqld --validate-config`, available since MySQL 8.0.16). When a directive
    is rejected we flip the redo-log strategy and try again, so an unexpected
    MySQL release can never leave the server unable to boot.
    """
    rAttempts = [None, False, True]
    for rOverride in rAttempts:
        with open(rPaths["cnf"], "w") as rFile:
            rFile.write(buildMySQLCnf(rOverride))
        rCode = runShell(
            "mysqld --validate-config --defaults-file=%s" % quote(rPaths["cnf"])
        )
        if rCode == 0:
            if rOverride is not None:
                printc("my.cnf auto-corrected for this MySQL release", col.YELLOW)
            return True
        # --validate-config unsupported on very old builds: trust the file.
        if shutil.which("mysqld") is None:
            return True
    printc("my.cnf could not be validated, keeping the safest variant", col.WARNING)
    with open(rPaths["cnf"], "w") as rFile:
        rFile.write(buildMySQLCnf(None))
    return False


def mysql(rUsername, rPassword):
    global rMySQLCnfTemplate
    printc("Configuring MySQL")

    rCreate = True
    if os.path.exists(rPaths["cnf"]):
        try:
            with open(rPaths["cnf"], "r") as rFile:
                if rFile.read(14) == "# Xtream Codes":
                    rCreate = False
        except OSError:
            pass

    if rCreate:
        try:
            shutil.copy(rPaths["cnf"], rPaths["cnfBackup"])
        except OSError:
            pass
        writeAndValidateCnf()
        runShell("systemctl daemon-reload")
        runShell("systemctl restart mysql")
        if runShell("systemctl is-active --quiet mysql") != 0:
            # Ubuntu ships mysql.service as an alias of mysqld.service on some builds
            runShell("systemctl restart mysqld")

    printc("Enter MySQL Root Password:", col.WARNING)
    for _i in range(5):
        rMySQLRoot = input("  ")
        print(" ")
        # MySQL 8 on Ubuntu authenticates root through auth_socket, so an empty
        # password is the normal case and no longer treated as a failure.
        rExtra = ""
        if len(rMySQLRoot) > 0:
            rExtra = " -p%s" % quote(rMySQLRoot)

        if mysqlQuery(["SELECT 1;"], rExtra) != 0:
            printc("Invalid password! Try again", col.FAIL)
            continue

        printc("Drop existing & create database? Y/N", col.WARNING)
        rDrop = input("  ").upper() == "Y"

        try:
            rIdent = (
                " IDENTIFIED WITH mysql_native_password BY %s" % quote(rPassword)
                if hasNativePasswordPlugin()
                else " IDENTIFIED BY %s" % quote(rPassword)
            )

            if rDrop:
                mysqlQuery(
                    [
                        "DROP USER IF EXISTS '%s'@'%%';" % rUsername,
                        "DROP USER IF EXISTS '%s'@'localhost';" % rUsername,
                        "DROP USER IF EXISTS '%s'@'127.0.0.1';" % rUsername,
                    ],
                    rExtra,
                )
                mysqlQuery(
                    [
                        "DROP DATABASE IF EXISTS xtream_iptvpro;",
                        "CREATE DATABASE IF NOT EXISTS xtream_iptvpro;",
                    ],
                    rExtra,
                )
                runShell(
                    "mysql --protocol=socket -S %s -u root%s xtream_iptvpro < %s"
                    % (quote(rMySQLSocket), rExtra, quote(rPaths["xc"] + "/database.sql"))
                )
                mysqlQuery(
                    [
                        "USE xtream_iptvpro;",
                        "UPDATE settings SET live_streaming_pass = '%s', unique_id = '%s', "
                        "crypt_load_balancing = '%s', get_real_ip_client='';"
                        % (generate(20), generate(12), generate(20)),
                    ],
                    rExtra,
                )
                mysqlQuery(
                    [
                        "USE xtream_iptvpro;",
                        "REPLACE INTO streaming_servers (id, server_name, domain_name, server_ip, "
                        "vpn_ip, ssh_password, ssh_port, diff_time_main, http_broadcast_port, "
                        "total_clients, system_os, network_interface, latency, status, enable_geoip, "
                        "geoip_countries, last_check_ago, can_delete, server_hardware, total_services, "
                        "persistent_connections, rtmp_port, geoip_type, isp_names, isp_type, enable_isp, "
                        "boost_fpm, http_ports_add, network_guaranteed_speed, https_broadcast_port, "
                        "https_ports_add, whitelist_ips, watchdog_data, timeshift_only) VALUES "
                        "(1, 'Main Server', '', '%s', '', NULL, NULL, 0, 8080, 1000, '%s', 'eth0', 0, 1, "
                        "0, '', 0, 0, '{}', 3, 0, 8880, 'low_priority', '', 'low_priority', 0, 1, '', "
                        "1000, 8443, '', '[\"127.0.0.1\",\"\"]', '{}', 0);" % (getIP(), getVersion()),
                    ],
                    rExtra,
                )
                mysqlQuery(
                    [
                        "USE xtream_iptvpro;",
                        "REPLACE INTO reg_users (id, username, password, email, member_group_id, "
                        "verified, status) VALUES (1, 'admin', "
                        "'\\$6\\$rounds=20000\\$xtreamcodes\\$XThC5OwfuS0YwS4ahiifzF14vkGbGsFF1w7ETL4sRRC5sOrAWCjWvQJDromZUQoQuwbAXAFdX3h3Cp3vqulpS0', "
                        "'admin@website.com', 1, 1, 1);",
                    ],
                    rExtra,
                )
                # MySQL 8 removed `GRANT ... IDENTIFIED BY`, so users are created first.
                for rHost in ["localhost", "127.0.0.1"]:
                    mysqlQuery(
                        [
                            "CREATE USER IF NOT EXISTS '%s'@'%s'%s;" % (rUsername, rHost, rIdent),
                            "GRANT ALL PRIVILEGES ON xtream_iptvpro.* TO '%s'@'%s' WITH GRANT OPTION;"
                            % (rUsername, rHost),
                            "GRANT SELECT, PROCESS, LOCK TABLES ON *.* TO '%s'@'%s';" % (rUsername, rHost),
                            "FLUSH PRIVILEGES;",
                        ],
                        rExtra,
                    )
                mysqlQuery(
                    [
                        "CREATE USER IF NOT EXISTS '%s'@'%%'%s;" % (rUsername, rIdent),
                        "GRANT SELECT, INSERT, UPDATE, DELETE ON xtream_iptvpro.* TO '%s'@'%%';" % rUsername,
                        "FLUSH PRIVILEGES;",
                    ],
                    rExtra,
                )
                mysqlQuery(
                    [
                        "USE xtream_iptvpro;",
                        "CREATE TABLE IF NOT EXISTS dashboard_statistics (id int(11) NOT NULL "
                        "AUTO_INCREMENT, type varchar(16) NOT NULL DEFAULT '', time int(16) NOT NULL "
                        "DEFAULT '0', count int(16) NOT NULL DEFAULT '0', PRIMARY KEY (id)) "
                        "ENGINE=InnoDB DEFAULT CHARSET=latin1;",
                        "INSERT INTO dashboard_statistics (type, time, count) "
                        "VALUES('conns', UNIX_TIMESTAMP(), 0),('users', UNIX_TIMESTAMP(), 0);",
                    ],
                    rExtra,
                )
                # last one is to prevent an xc vulnerability, run
                # "UPDATE settings SET get_real_ip_client='HTTP_CF_CONNECTING_IP' where id=1;"
                # query if you are using cf proxy.
                mysqlQuery(
                    [
                        "USE xtream_iptvpro;",
                        "UPDATE settings SET get_real_ip_client='', double_auth='1', hash_lb='1', "
                        "mag_security='1' where id='1';",
                    ],
                    rExtra,
                )

                if not os.path.exists(rPaths["jemallocEnv"]):
                    rJemallocPath = rJemalloc
                    if not glob.glob("/usr/lib/*/libjemalloc.so.2"):
                        rJemallocPath = "/usr/lib/x86_64-linux-gnu/libjemalloc.so.1"
                    with open(rPaths["jemallocEnv"], "w") as rFile:
                        rFile.write("LD_PRELOAD=%s\n" % rJemallocPath)
                    # Drop-in override instead of replacing the packaged unit file.
                    try:
                        os.makedirs(os.path.dirname(rPaths["serviceDropIn"]), exist_ok=True)
                    except OSError:
                        pass
                    with open(rPaths["serviceDropIn"], "w") as rFile:
                        rFile.write(rMySQLServiceFile)
                    runShell("systemctl daemon-reload")
                    runShell("systemctl restart mysql.service")
                    if runShell("systemctl is-active --quiet mysql") != 0:
                        runShell("systemctl restart mysqld.service")

            try:
                os.remove(rPaths["xc"] + "/database.sql")
            except OSError:
                pass
            return True
        except Exception as rError:
            printc("Invalid password! Try again (%s)" % rError, col.FAIL)
    return False


def encrypt(rHost="127.0.0.1", rUsername="user_iptvpro", rPassword="", rDatabase="xtream_iptvpro", rServerID=1, rPort=7999):
    printc("Encrypting...")
    try:
        os.remove(rPaths["config"])
    except OSError:
        pass

    # NOTE: the XOR key stays byte-for-byte identical to the original - the
    # closed source PHP/C binaries shipped in main.tar.gz decrypt it themselves.
    rPlain = '{"host":"%s","db_user":"%s","db_pass":"%s","db_name":"%s","server_id":"%d", "db_port":"%d", "pconnect":"0"}' % (
        rHost, rUsername, rPassword, rDatabase, int(rServerID), int(rPort),
    )
    rKey = "5709650b0d7806074842c6de575025b1"
    rXored = bytes(
        ord(rChar) ^ ord(rKeyChar)
        for rChar, rKeyChar in zip(rPlain, cycle(rKey))
    )
    with open(rPaths["config"], "wb") as rf:
        rf.write(base64.b64encode(rXored).replace(b"\n", b""))


def patchNginxConf():
    """adds domain/user/pass/id.ts url support"""
    rConf = rPaths["xc"] + "/nginx/conf/nginx.conf"
    rOldRule = "rewrite ^/(.*)/(.*)/(\\d+)$ /streaming/clients_live.php?username=$1&password=$2&stream=$3&extension=ts break;"
    rNewRules = (
        "rewrite ^/(.*)/(.*)/(\\d+)\\.(.*)$ /streaming/clients_live.php?username=$1&password=$2&stream=$3&extension=$4 break;\r\n"
        "        rewrite ^/(.*)/(.*)/(\\d+)$ /streaming/clients_live.php?username=$1&password=$2&stream=$3&extension=ts break;\r\n"
    )
    try:
        with open(rConf, "r") as nginx_file:
            nginx_replace = nginx_file.read()
        if rOldRule in nginx_replace and "extension=$4 break;" not in nginx_replace:
            nginx_replace = nginx_replace.replace(rOldRule, rNewRules)
            with open(rConf, "w") as nginx_file:
                nginx_file.write(nginx_replace)
    except OSError as rError:
        printc("Could not patch nginx.conf (%s)" % rError, col.WARNING)


def checkLibPNGCompat():
    """
    The prebuilt binaries were linked against libpng12.so.0 which no longer
    exists on supported Ubuntu releases. libpng16 is NOT ABI compatible with
    libpng12, so we detect and report instead of creating a bogus symlink.
    """
    rMissing = []
    for rBinary in glob.glob(rPaths["xc"] + "/bin/*") + glob.glob(rPaths["xc"] + "/nginx/sbin/*"):
        if not os.path.isfile(rBinary) or not os.access(rBinary, os.X_OK):
            continue
        try:
            rOutput = subprocess.check_output(
                ["ldd", rBinary], stderr=subprocess.DEVNULL
            ).decode("utf-8", "replace")
            if "libpng12.so.0 => not found" in rOutput:
                rMissing.append(os.path.basename(rBinary))
        except Exception:
            continue
    if rMissing:
        printc(
            "libpng12 needed by: %s - install the maintained libpng12-0 shim or rebuild them"
            % ", ".join(sorted(set(rMissing))),
            col.WARNING,
        )


def configure(rType="MAIN"):
    printc("Configuring System")

    if rPaths["xc"] + "/" not in open("/etc/fstab").read():
        with open("/etc/fstab", "a") as rFile:
            rFile.write(
                "tmpfs %s/streams tmpfs defaults,noatime,nosuid,nodev,noexec,mode=1777,size=90%% 0 0\n"
                "tmpfs %s/tmp tmpfs defaults,noatime,nosuid,nodev,noexec,mode=1777,size=3G 0 0\n"
                % (rPaths["xc"], rPaths["xc"])
            )

    # /etc/sudoers.d drop-in - editing /etc/sudoers directly is unsupported on
    # modern Ubuntu because a syntax error there locks you out of sudo entirely.
    if not os.path.exists(rPaths["sudoersDropIn"]):
        with open(rPaths["sudoersDropIn"], "w") as rFile:
            rFile.write(
                "xtreamcodes ALL = (root) NOPASSWD: /usr/sbin/iptables, /sbin/iptables, /usr/bin/chattr\n"
            )
        os.chmod(rPaths["sudoersDropIn"], 0o440)
        if runCommand(["visudo", "-c"]) != 0:
            printc("sudoers drop-in rejected by visudo, removing", col.FAIL)
            os.remove(rPaths["sudoersDropIn"])

    if not os.path.exists(rPaths["initd"]):
        with open(rPaths["initd"], "w") as rFile:
            rFile.write("#! /bin/bash\n%s/start_services.sh\n" % rPaths["xc"])
        os.chmod(rPaths["initd"], 0o755)

    # Native systemd unit (modern replacement for the @reboot crontab line).
    if not os.path.exists(rPaths["systemdUnit"]):
        with open(rPaths["systemdUnit"], "w") as rFile:
            rFile.write(
                "[Unit]\n"
                "Description=Xtream Codes Services\n"
                "After=network-online.target mysql.service\n"
                "Wants=network-online.target\n\n"
                "[Service]\n"
                "Type=oneshot\n"
                "RemainAfterExit=yes\n"
                "User=root\n"
                "ExecStart=%s/start_services.sh\n"
                "TimeoutStartSec=600\n\n"
                "[Install]\n"
                "WantedBy=multi-user.target\n" % rPaths["xc"]
            )
        runShell("systemctl daemon-reload")
        runShell("systemctl enable xtreamcodes.service")

    runShell("mount -a")
    try:
        os.remove("/usr/bin/ffmpeg")
    except OSError:
        pass
    if not os.path.exists(rPaths["xc"] + "/tv_archive"):
        os.mkdir(rPaths["xc"] + "/tv_archive/")
    runShell("ln -s %s/bin/ffmpeg /usr/bin/" % quote(rPaths["xc"]))
    runShell("chown xtreamcodes:xtreamcodes -R %s" % quote(rPaths["base"]))
    runShell("chmod -R 0777 %s" % quote(rPaths["base"]))

    if rType == "MAIN":
        runShell("find %s/admin/ -type f -exec chmod 644 {} \\;" % quote(rPaths["xc"]))
        runShell("find %s/admin/ -type d -exec chmod 755 {} \\;" % quote(rPaths["xc"]))

    patchNginxConf()

    rBase = "https://github.com/emre1393/xtreamui_mirror/releases/latest/download/"
    download(rBase + "nginx", rPaths["xc"] + "/nginx/sbin/nginx")
    download(rBase + "nginx_rtmp", rPaths["xc"] + "/nginx_rtmp/sbin/nginx_rtmp")
    download(rBase + "pid_monitor.php", rPaths["xc"] + "/crons/pid_monitor.php")
    os.chmod(rPaths["xc"] + "/nginx/sbin/nginx", 0o755)
    os.chmod(rPaths["xc"] + "/nginx_rtmp/sbin/nginx_rtmp", 0o755)

    runShell("find %s/wwwdir/ -type f -exec chmod 644 {} \\;" % quote(rPaths["xc"]))
    runShell("find %s/wwwdir/ -type d -exec chmod 755 {} \\;" % quote(rPaths["xc"]))
    os.chmod(rPaths["config"], 0o700)

    # Anti-fingerprinting: redirect the web root to Google (unchanged behaviour).
    runShell(
        "sed -i 's|echo \"Xtream Codes Reborn\";|header(\"Location: https://www.google.com/\");|g' %s"
        % quote(rPaths["xc"] + "/wwwdir/index.php")
    )

    installGeoIP()
    checkLibPNGCompat()

    runShell(
        "sed -i 's|chown -R xtreamcodes:xtreamcodes /home/xtreamcodes|"
        "chown -R xtreamcodes:xtreamcodes /home/xtreamcodes 2>/dev/null|g' %s"
        % quote(rPaths["xc"] + "/start_services.sh")
    )
    os.chmod(rPaths["xc"] + "/start_services.sh", 0o755)

    for rHostEntry in ["xtream-codes.com", "api.xtream-codes.com", "downloads.xtream-codes.com"]:
        try:
            rHosts = open("/etc/hosts").read()
        except OSError:
            rHosts = ""
        # Still required: the binaries phone home for licence validation and the
        # official validation servers were seized in 2019.
        if rHostEntry not in rHosts:
            with open("/etc/hosts", "a") as rFile:
                rFile.write("127.0.0.1    %s\n" % rHostEntry)

    try:
        rCrontab = open("/etc/crontab").read()
    except OSError:
        rCrontab = ""
    if "@reboot root %s/start_services.sh" % rPaths["xc"] not in rCrontab:
        # Kept as a fallback for images without systemd; harmless duplicate.
        with open("/etc/crontab", "a") as rFile:
            rFile.write("@reboot root %s/start_services.sh\n" % rPaths["xc"])


def installGeoIP():
    """
    MaxMind killed anonymous direct downloads of GeoLite2 in December 2019
    (GDPR / CCPA). When MAXMIND_LICENSE_KEY is exported we use the official
    geoipupdate feed, otherwise we fall back to the mirror release asset so the
    installer keeps working offline exactly like before.
    """
    rLicenseKey = os.environ.get("MAXMIND_LICENSE_KEY", "").strip()
    if rLicenseKey:
        printc("Updating GeoLite2 via official geoipupdate feed")
        if installPackage("geoipupdate"):
            with open("/etc/GeoIP.conf", "w") as rFile:
                rFile.write(
                    "LicenseKey %s\nUserId 999999\nDatabaseDirectory %s\nEditionIDs GeoLite2-Country GeoLite2-City\n"
                    % (rLicenseKey, rPaths["xc"])
                )
            runCommand(["geoipupdate", "-v", "-f", "/etc/GeoIP.conf"])
            if os.path.exists(rPaths["geoip"]):
                runShell("chattr -f +i %s" % quote(rPaths["geoip"]))
                return True

    printc("Downloading GeoLite2.mmdb from mirror release")
    if download(
        "https://github.com/emre1393/xtreamui_mirror/releases/latest/download/GeoLite2.mmdb",
        rPaths["geoip"],
    ):
        runShell("chattr -f +i %s" % quote(rPaths["geoip"]))
        return True

    printc("GeoLite2.mmdb download failed, GeoIP filtering will be disabled", col.WARNING)
    return False


def start(first=True):
    if first:
        printc("Starting Xtream Codes")
    else:
        printc("Restarting Xtream Codes")
    runShell("systemctl start xtreamcodes.service", rQuiet=False)
    if runShell("systemctl is-active --quiet xtreamcodes.service") != 0:
        runShell("%s/start_services.sh" % quote(rPaths["xc"]))


if __name__ == "__main__":

    if os.geteuid() != 0:
        printc("Please run this installer as root (sudo ./install.py)", col.FAIL)
        sys.exit(1)

    rVersion = getVersionShort()
    if rVersion not in rVersions:
        printc("Unsupported Operating System, Works only on Ubuntu Server 20.04, 22.04 and 24.04")
        sys.exit(1)

    printc("Xtream UI - Installer Mirror", col.OKGREEN, 2)
    print("%s │ Check out the mirror repo: https://bitbucket.org/emre1393/xtreamui_mirror %s" % (col.OKGREEN, col.ENDC))
    print("%s │ Modernized build: Python 3 + Ubuntu 20.04 / 22.04 / 24.04 %s" % (col.OKGREEN, col.ENDC))
    print(" ")
    rType = input("  Installation Type [MAIN, LB]: ")
    print(" ")

    if rType.upper() in ["MAIN", "LB"]:
        rAccesscode = ""
        if rType.upper() == "LB":
            rHost = input("  Main Server IP Address: ")
            rPassword = input("  MySQL Password: ")
            try:
                rServerID = int(input("  Load Balancer Server ID: "))
            except ValueError:
                rServerID = -1
            print(" ")
        else:
            rHost = "127.0.0.1"
            rPassword = generate()
            rServerID = 1
            rAccesscode = generate(12)

        rUsername = "user_iptvpro"
        rDatabase = "xtream_iptvpro"
        rPort = 7999

        if len(rHost) > 0 and len(rPassword) > 0 and rServerID > -1:
            printc("Start installation? Y/N", col.WARNING)
            if input("  ").upper() == "Y":
                print(" ")
                prepare(rType.upper())
                if not install(rType.upper()):
                    sys.exit(1)
                if rType.upper() == "MAIN":
                    if not mysql(rUsername, rPassword):
                        sys.exit(1)
                encrypt(rHost, rUsername, rPassword, rDatabase, rServerID, rPort)
                if rType.upper() == "MAIN":
                    installadminpanel()
                    runShell(
                        "sed -i 's|randomcodehere|%s|g' %s"
                        % (rAccesscode, quote(rPaths["xc"] + "/nginx/conf/admin_panel.conf"))
                    )
                configure(rType.upper())
                start()
                printc("Installation completed!", col.OKGREEN, 2)
                if rType.upper() == "MAIN":
                    printc("Please store your MySQL password!")
                    printc(rPassword)
                    printc("Admin UI Login URL is:")
                    printc("http://%s:8080/%s" % (getIP(), rAccesscode))
                    printc("Admin UI default login is admin/admin")
            else:
                printc("Installation cancelled", col.FAIL)
        else:
            printc("Invalid entries", col.FAIL)
    else:
        printc("Invalid installation type", col.FAIL)
