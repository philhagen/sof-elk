- TODO: need the VM vitals
- Ubuntu 24.01 LTS Server ISO
- English
- Update to new installer
- Keyboard: English (US) / English (US)
- Type of installation: Ubuntu Server (minimized)
- Network: DHCP via NAT
- No Proxy
- Disk/partition setup:
    - Guided storage configuration
        - Use an entire disk
        - Set up this disk as an LVM group
    - Storage configuration
        - Create 4GB swap LV named `swap`
        - Create 250GB ext4 LV named `root` mounted on `/`
        - Create remainder of space as ext4 LV named `elasticsearch` mounted on `/var/lib/elasticsearch`
- Profile configuration
    - Your name: ansible
    - Your servers name: sof-elk
    - Pick a username: ansible
    - Choose/confirm password: forensics
- Ubuntu Pro: Skip for now
- SSH configuration:
    - Install OpenSSH server
- Featured server snaps: none

- When installation is complete, select "Reboot Now"


after reboot:
- apt install ansible git
- git clone repo
- ansible-playbook -K -i 127.0.0.1, --connection=local /tmp/sof-elk/ansible/sof-elk_single_vm.yml

TODO:
- elk_user homedir not created