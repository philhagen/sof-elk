# SOF-ELK Classroom VM Preparation Steps

These are the steps used to create a SOF-ELK instance as used in the FOR572 courseware.  These steps may be a good starting point for those wishing to deploy their own SOF-ELK capabilities across multiple systems via the included Ansible playbooks.

1. Virtual Machine configuration
    * Name: `FOR572 SOF-ELK`
    * 4 cores
    * 4096 MB RAM
    * Enable hypervisor applications
    * Disable 3D graphics acceleration
    * USB 3.0 Controller
    * Remove Sound
    * Remove Printer
    * Remove Camera
    * Hardware (compatibility) version so $current-1 is supported
    * 500GB SCSI HDD, single file, named `FOR572 SOF-ELK.vmdk`
2. CentOS 7 network install
    * I had to append `vga=794` to the install command line or the windows got cut off
    * Enable networking (DHCP)
    * Hostname: `sof-elk`
    * Timezone: `Etc/Coordinated Universal Time` (**NOT GMT**), network time enabled
    * Install via network, URL: `http://mirrors.sonic.net/centos/7/os/x86_64/`
    * Software selection: Minimal
    * Installation destination: ~500GB HDD, but select "I will configure partitions"
      * Click "Click here to create them automatically"
      * Change `/home` to 100GB
      * Create `/var/lib/elasticsearch` partition and leave size blank - should auto-fill disk at ~350GB
    * Set a strong root password.  It is recommended to *disable* direct use of this account after the system is installed.
    * During install, create a user
      * Full name: `SOF-ELK User`
      * Username: `elk_user`
      * Select "Make this user an administrator"
      * Set password as desired - for class, this is `forensics`.  This weak password will requires you to click "Done" twice.
    * You may need to manually remove the installation ISO file from the VMX file when initial installation is complete.
    * Reboot the VM.
3. `yum -y install git ansible` (as root or with sudo)
4. `git clone https://github.com/philhagen/sof-elk /tmp/sof-elk` (as root or with sudo)
    * Change to the desired branch in the cloned repository, e.g.`git branch public/v20200229`.  This branch will be the same as what is deployed in the completed installation.
5. `ansible-playbook -i 127.0.0.1, --connection=local /tmp/sof-elk/ansible/sof-elk_preload.yml`
    * This has to take place in two stages because the ansible in the CentOS core repo has a broken `command` module (and maybe others). This step ensures a version of ansible that works and is needed for several steps in the `sof-elk_single_vm_.yml` playbook below.
6. `ansible-playbook -i 127.0.0.1, --connection=local /tmp/sof-elk/ansible/sof-elk_single_vm.yml`
    * You will need a free GeoIP account to download the City and ASN databases.  [You can learn more about the GeoLite2 databases, as well as sign up for a free MaxMind account by clicking here](https://dev.maxmind.com/geoip/geoip2/geolite2/).
7. `rm -rf /tmp/sof-elk`
8. Stage evidence as required.
   1. Classroom VM (evidence not distributed publicly)
      * Lab 2.3 (Logs)
      * Lab 3.1 (NetFlow) - load with `nfdump2sof-elk.sh` script, as prescribed by the lab text.
   2. Public VM
      * Old Lab 2.3 (Logs)
      * New Lab 3.1 (NetFlow)
9. Reboot the VM.  (Technically not required, but ensures all is set up to start on boot.)
