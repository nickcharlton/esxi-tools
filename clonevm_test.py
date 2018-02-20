#!/usr/bin/env python

import os
import unittest
import mock
from pyfakefs import fake_filesystem_unittest

from clonevm import VmdkClone


class VmdkCloneTest(fake_filesystem_unittest.TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_run_raises_exception_if_source_is_missing(self):
        with self.assertRaises(Exception) as context:
            dc = VmdkClone("debian-9-x64", "debian-clone")
            dc.run()

        self.assertTrue("Source directory (debian-9-x64 in /vmfs/volumes) "
                        "must exist" in context.exception)

    def test_run_raises_exception_if_destination_exists(self):
        self.stub_disk_image("debian-9-x64/disk.vmdk")
        self.stub_disk_image("debian-clone/disk.vmdk")

        with self.assertRaises(Exception) as context:
            dc = VmdkClone("debian-9-x64", "debian-clone")
            dc.run()

        self.assertTrue("Destination directory "
                        "(/vmfs/volumes/5f9a-fc0f/debian-clone) must not "
                        "already exist" in context.exception)

    @mock.patch("subprocess.check_call")
    def test_run_creates_destination_directory(self, mock_check_call):
        self.stub_disk_image("debian-9-x64/disk.vmdk")

        dc = VmdkClone("debian-9-x64", "debian-clone")
        dc.run()

        destination_path = "/vmfs/volumes/5f9a-fc0f/debian-clone"
        self.assertTrue(os.path.exists(destination_path))

    @mock.patch("subprocess.check_call")
    def test_run_calls_vmkstools_with_the_base_disk(self, mock_check_call):
        self.stub_disk_images([
            "debian-9-x64/debian-9-x64-flat.vmdk",
            "debian-9-x64/debian-9-x64.vmdk",
            "ubuntu-1604-x64/ubuntu-1604-x64-flat.vmdk",
            "ubuntu-1604-x64/ubuntu-1604-x64.vmdk",
            "ubuntu-1604-x64/ubuntu-1604-x64-000001-delta.vmdk",
            "ubuntu-1604-x64/ubuntu-1604-x64-000001.vmdk",
            "ubuntu-1604-x64/ubuntu-1604-x64-000002-delta.vmdk",
            "ubuntu-1604-x64/ubuntu-1604-x64-000002.vmdk"])

        process_mock = mock.Mock()
        attrs = {"communicate.return_value": ('output', 'error')}
        process_mock.configure_mock(**attrs)
        mock_check_call.return_value = process_mock

        dc = VmdkClone("debian-9-x64", "debian-clone")
        dc.run()

        mock_check_call.assert_called_once_with(
            ["vmkfstools",
             "-i",
             "/vmfs/volumes/5f9a-fc0f/debian-9-x64/debian-9-x64.vmdk",
             "/vmfs/volumes/5f9a-fc0f/debian-clone/disk.vmdk",
             "-d",
             "thin"])

    @mock.patch("subprocess.check_call")
    def test_run_with_snapshot_opt_calls_vmkfstools_with_snapshot_disk(
            self, mock_check_call):
        self.stub_disk_images([
            "debian-9-x64/debian-9-x64-flat.vmdk",
            "debian-9-x64/debian-9-x64.vmdk",
            "ubuntu-1604-x64/ubuntu-1604-x64-flat.vmdk",
            "ubuntu-1604-x64/ubuntu-1604-x64.vmdk",
            "ubuntu-1604-x64/ubuntu-1604-x64-000001-delta.vmdk",
            "ubuntu-1604-x64/ubuntu-1604-x64-000001.vmdk",
            "ubuntu-1604-x64/ubuntu-1604-x64-000002-delta.vmdk",
            "ubuntu-1604-x64/ubuntu-1604-x64-000002.vmdk"])

        process_mock = mock.Mock()
        attrs = {"communicate.return_value": ('output', 'error')}
        process_mock.configure_mock(**attrs)
        mock_check_call.return_value = process_mock

        dc = VmdkClone("ubuntu-1604-x64", "ubuntu-clone", opts={"snapshot": 2})
        dc.run()

        mock_check_call.assert_called_once_with(
            ["vmkfstools",
             "-i",
             "/vmfs/volumes/5f9a-fc0f/ubuntu-1604-x64/"
             "ubuntu-1604-x64-000002.vmdk",
             "/vmfs/volumes/5f9a-fc0f/ubuntu-clone/disk.vmdk",
             "-d",
             "thin"])

    @mock.patch("subprocess.check_call")
    def test_run_with_format_opt_calls_vmkfstools_with_disk_format(
            self, mock_check_call):
        self.stub_disk_image("debian-9-x64/debian-9-x64.vmdk")

        process_mock = mock.Mock()
        attrs = {"communicate.return_value": ('output', 'error')}
        process_mock.configure_mock(**attrs)
        mock_check_call.return_value = process_mock

        dc = VmdkClone("debian-9-x64", "debian-clone",
                       opts={"disk-format": "2gbsparse"})
        dc.run()

        mock_check_call.assert_called_once_with(
            ["vmkfstools",
             "-i",
             "/vmfs/volumes/5f9a-fc0f/debian-9-x64/debian-9-x64.vmdk",
             "/vmfs/volumes/5f9a-fc0f/debian-clone/disk.vmdk",
             "-d",
             "2gbsparse"])

    def stub_file(self, path):
        basedir = os.path.dirname(path)
        if not os.path.exists(basedir):
            os.makedirs(basedir)

        open(path, 'a').close()

    def stub_disk_image(self, image_path):
        self.stub_file("/vmfs/volumes/5f9a-fc0f/" + image_path)

    def stub_disk_images(self, image_paths):
        for image_path in image_paths:
            self.stub_disk_image(image_path)


if __name__ == '__main__':
    unittest.main()
