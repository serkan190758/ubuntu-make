# -*- coding: utf-8 -*-
# Copyright (C) 2014 Canonical
#
# Authors:
#  Didier Roche
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; version 3.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

"""Tests for android"""

from . import LargeFrameworkTests
import os
import pexpect
import signal
import subprocess
import tempfile
from udtc.tools import launcher_exists_and_is_pinned


class AndroidStudioTests(LargeFrameworkTests):
    """This will test the Android Studio base"""

    TIMEOUT_INSTALL = 300
    TIMEOUT_START = 60
    TIMEOUT_STOP = 60

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.expanduser("~/tools/android/android-studio")
        self.launcher_path = "android-studio.desktop"

    def test_default_android_studio_install(self):
        """Install android studio from scratch test case"""
        self.child = pexpect.spawnu('./developer-tools-center android android-studio')
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("\[I Accept.*\]")  # ensure we have a license question
        self.child.sendline("a")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL)
        self.wait_and_no_warn()

        # we have an installed launcher, added to the launcher
        self.assertTrue(launcher_exists_and_is_pinned(self.launcher_path))
        self.assertTrue(os.path.exists(self.exec_path))

        # launch it, send SIGTERM and check that it exits fine
        proc = subprocess.Popen(self.exec_path, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        pid = self.pid_for(["java", self.installed_path], wait_before=self.TIMEOUT_START)
        os.kill(pid, signal.SIGTERM)
        self.assertEquals(proc.wait(self.TIMEOUT_STOP), 0)

        # ensure that it's detected as installed:
        self.child = pexpect.spawnu('./developer-tools-center android android-studio')
        self.expect_and_no_warn("Android Studio is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_no_warn()

    def test_no_license_accept_android_studio(self):
        """We don't accept the license (default)"""
        self.child = pexpect.spawnu('./developer-tools-center android android-studio')
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("\[I Accept.*\]")  # ensure we have a license question
        self.accept_default_and_wait()

        self.assertFalse(launcher_exists_and_is_pinned("android-studio.desktop"))
        self.assertFalse(os.path.exists(self.exec_path))

    def test_doesnt_accept_wrong_path(self):
        """We don't accept a wrong path"""
        self.child = pexpect.spawnu('./developer-tools-center android android-studio')
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline(chr(127)*100)
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline(chr(127)*100 + "/")
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path), expect_warn=True)
        self.child.sendcontrol('C')
        self.wait_and_no_warn()

        self.assertFalse(launcher_exists_and_is_pinned(self.launcher_path))
        self.assertFalse(os.path.exists(self.exec_path))

    def test_android_studio_reinstall(self):
        """Reinstall android studio once installed"""
        for loop in ("install", "reinstall"):
            self.child = pexpect.spawnu('./developer-tools-center android android-studio')
            if loop == "reinstall":
                self.expect_and_no_warn("Android Studio is already installed.*\[.*\] ")
                self.child.sendline("y")
            self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
            self.child.sendline("")
            self.expect_and_no_warn("\[.*\] ")
            self.child.sendline("a")
            self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL)
            self.wait_and_no_warn()

            # we have an installed launcher, added to the launcher
            self.assertTrue(launcher_exists_and_is_pinned(self.launcher_path))
            self.assertTrue(os.path.exists(self.exec_path))

            # launch it, send SIGTERM and check that it exits fine
            proc = subprocess.Popen(self.exec_path, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            pid = self.pid_for(["java", self.installed_path], wait_before=self.TIMEOUT_START)
            os.kill(pid, signal.SIGTERM)
            self.assertEquals(proc.wait(self.TIMEOUT_STOP), 0)

    def test_custom_install_path(self):
        """We install android studio in a custom path"""
        # We skip the existing directory prompt
        self.child = pexpect.spawnu('./developer-tools-center android android-studio /tmp/foo')
        self.expect_and_no_warn("\[I Accept.*\]")  # ensure we have a license as the first question
        self.accept_default_and_wait()

    def test_start_install_on_empty_dir(self):
        """We try to install on an existing empty dir"""
        self.installed_path = tempfile.mkdtemp()
        self.child = pexpect.spawnu('./developer-tools-center android android-studio {}'.format(self.installed_path))
        self.expect_and_no_warn("\[I Accept.*\]")  # ensure we have a license as the first question
        self.accept_default_and_wait()

        self.assertFalse(launcher_exists_and_is_pinned(self.launcher_path))
        self.assertFalse(os.path.exists(self.exec_path))

    def test_start_install_on_existing_dir(self):
        """We prompt if we try to install on an existing directory which isn't emtpy"""
        self.installed_path = tempfile.mkdtemp()
        open(os.path.join(self.installed_path, "bar"), 'w').write("foo")
        self.child = pexpect.spawnu('./developer-tools-center android android-studio {}'.format(self.installed_path))
        self.expect_and_no_warn("{} isn't an empty directory.*install there\? \[.*\] ".format(self.installed_path))
        self.accept_default_and_wait()

        self.assertFalse(launcher_exists_and_is_pinned(self.launcher_path))
        self.assertFalse(os.path.exists(self.exec_path))

    def test_is_default_framework(self):
        """Android Studio is chosen as the default framework"""
        self.child = pexpect.spawnu('./developer-tools-center android')
        # we ensure it thanks to installed_path being the android-studio one
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendcontrol('C')
        self.wait_and_no_warn()

    def test_is_default_framework_with_options(self):
        """Android Studio options are sucked in as the default framework"""
        self.child = pexpect.spawnu('./developer-tools-center android /tmp/foo')
        self.expect_and_no_warn("\[I Accept.*\]")  # ensure we have a license as the first question
        self.accept_default_and_wait()