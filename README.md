# esxi-tools

Tools for interacting with [VMware ESXi][] directly.

## Usage

The contents of the top level of this directory is executable, and you'd likely
want to drop them into somewhere helpful in the `$PATH` on an ESXi box.

It's tested (manually) on ESXi 6.0 only, but the scripts themselves have tests
where possible.

### `clonevm`

Clones a disk image that's in `/vmfs/volumes` (to the same volume), ready to be
added again in the ESXi management UI.

[VMware ESXi]: https://www.vmware.com/products/vsphere-hypervisor.html
