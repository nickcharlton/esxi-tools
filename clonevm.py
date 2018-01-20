#!/usr/bin/env python

import getopt
import sys
import re
import os
import subprocess


def merge_dict(x, y):
    z = x.copy()
    z.update(y)

    return z


class VmdkClone(object):
    def __init__(self, opts={}):
        self.opts = merge_dict({"snapshot": None, "disk-format": "thin"}, opts)

    def run(self, source, destination):
        source_disk_image = self._source_disk_image(source,
                                                    self.opts["snapshot"])

        if source_disk_image is None:
            raise Exception("Source directory ({0} in /vmfs/volumes) must "
                            "exist".format(source))
            return

        destination_path = self._destination_path(source, destination)
        destination_directory = os.path.dirname(destination_path)

        if os.path.exists(destination_directory):
            raise Exception("Destination directory ({0}) must not "
                            "already exist".format(destination_directory))
            return

        os.makedirs(destination_directory)

        subprocess.check_call(["vmkfstools",
                               "-i",
                               source_disk_image,
                               destination_path,
                               "-d", self.opts["disk-format"]])

    def _disk_paths(self):
        return [os.path.join(dirpath, f)
                for dirpath, dirnames, files in os.walk("/vmfs/volumes")
                for f in files if f.endswith(".vmdk")]

    def _source_disk_image(self, source, snapshot=None):
        if snapshot is not None:
            return self._snapshot_image(source, snapshot)
        else:
            return self._base_disk_image(source)

    def _base_disk_image(self, source):
        m = re.search("^[a-z0-9-/]+(?<=" + source +
                      ")[a-z0-9-/]+(?<![0-9]{6})(?<!flat)(?<!delta)\.vmdk$",
                      "\n".join(self._disk_paths()),
                      re.MULTILINE)

        return m.group() if m else None

    def _snapshot_image(self, source, snapshot):
        snapshot_number = "{0}".format(snapshot).zfill(6)
        m = re.search("^[a-z0-9-/]+(?<={0})[a-z0-9-/]+(?<={1})\.vmdk$".format(
            source, snapshot_number),
            "\n".join(self._disk_paths()), re.MULTILINE)

        return m.group() if m else None

    def _destination_path(self, source, destination):
        source_disk_image = self._source_disk_image(source,
                                                    self.opts["snapshot"])
        source_directory = os.path.dirname(source_disk_image)
        source_volume = re.sub(source, destination, source_directory)

        return "{0}/disk.vmdk".format(source_volume)


def usage():
    print """{0} [sdh] [src] [dest]

Clone a VMware ESXi virtual machine.

Options:
  -s/--snapshot Clone from a snapshot number (e.g.: 1)
  -d/--disk-format Disk format type (e.g.: zeroedthick, thin). Default: thin
  -h/--help Show this help
""".format(os.path.basename(sys.argv[0]))


def main(argv):
    clone_opts = {}

    try:
        opts, args = getopt.getopt(argv, "hs:d:", ["help", "snapshot=",
                                                   "disk-format="])
    except getopt.GetoptError:
        usage()
        sys.exit(1)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-s", "--snapshot"):
            clone_opts["snapshot"] = arg
        elif opt in ("-d", "--disk-format"):
            clone_opts["disk-format"] = arg

    if len(args) < 2:
        usage()
        sys.exit(2)

    dc = VmdkClone(opts=clone_opts)

    try:
        dc.run(args[0], args[1])
    except Exception as e:
        print(e)
        sys.exit(3)

if __name__ == "__main__":
    main(sys.argv[1:])
