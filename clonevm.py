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
    def __init__(self, source, destination, opts={}):
        self.source = source
        self.destination = destination
        self.opts = merge_dict({"snapshot": None, "disk-format": "thin"}, opts)

    def run(self):
        source_disk_image = self.__find_source_disk_image()

        if source_disk_image is None:
            raise Exception("Source directory ({0} in /vmfs/volumes) must "
                            "exist".format(self.source))
            return

        destination_path = self.__build_destination_path()
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

    def __find_disk_paths(self):
        return [os.path.join(dirpath, f)
                for dirpath, dirnames, files in os.walk("/vmfs/volumes")
                for f in files if f.endswith(".vmdk")]

    def __find_source_disk_image(self):
        if self.opts["snapshot"] is not None:
            return self.__find_snapshot_image()
        else:
            return self.__find_base_disk_image()

    def __find_base_disk_image(self):
        disk_paths = self.__find_disk_paths()
        m = re.search("^[a-z0-9-/]+(?<=" + self.source +
                      ")[a-z0-9-/]+(?<![0-9]{6})(?<!flat)(?<!delta)\.vmdk$",
                      "\n".join(disk_paths),
                      re.MULTILINE)

        return m.group() if m else None

    def __find_snapshot_image(self):
        disk_paths = self.__find_disk_paths()
        snapshot = self.opts["snapshot"]
        snapshot_number = "{0}".format(snapshot).zfill(6)
        m = re.search("^[a-z0-9-/]+(?<={0})[a-z0-9-/]+(?<={1})\.vmdk$".format(
            self.source, snapshot_number),
            "\n".join(disk_paths), re.MULTILINE)

        return m.group() if m else None

    def __build_destination_path(self):
        source_directory = os.path.dirname(self.__find_source_disk_image())
        source_volume = re.sub(self.source, self.destination, source_directory)

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

    dc = VmdkClone(args[0], args[1], opts=clone_opts)

    try:
        dc.run()
    except Exception as e:
        print(e)
        sys.exit(3)

if __name__ == "__main__":
    main(sys.argv[1:])
