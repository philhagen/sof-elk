# SOF-ELK Classroom VM Preparation Steps

These are the steps used to create a SOF-ELK instance as used in the FOR572 courseware.  These steps may be a good starting point for those wishing to deploy their own SOF-ELK capabilities across multiple systems via the included Ansible playbooks.

1. Virtual Machine configuration
    * Name: `FOR572 SOF-ELK`
    * 4 cores
    * 4096 MB RAM
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
    * During install, create a user
      * Full name: `SOF-ELK User`
      * Username: `elk_user`
      * Set password as desired - for class, this is `forensics`.  This weak password will requires you to click "Done" twice.
    * **Do not** set a root password - skipping this will create a password-less root user which can not be used directly
3. `yum -y install git ansible` (as root or with sudo)
4. `git clone https://github.com/philhagen/sof-elk /tmp/sof-elk` (as root or with sudo)
5. `ansible-playbook -i 127.0.0.1, --connection=local /tmp/sof-elk/sof-elk_preload.yml`
    * This has to take place in two stages because the ansible in the CentOS core repo has a broken `command` module (and maybe others). This step ensures a version of ansible that works and is needed for several steps in the `sof-elk_single_vm_.yml` playbook below.
6. `ansible-playbook -i 127.0.0.1, --connection=local /tmp/sof-elk/sof-elk_single_vm.yml`
7. `rm -rf /tmp/sof-elk`
8. Stage evidence as required.
   1. Classroom VM (evidence not distributed publicly)
      * Lab 2.3
      * Lab 3.1
   2. Public VM
      * Old Lab 2.3 (Logs)
      * New Lab 3.1 (NetFlow)
9. Reboot the VM.  (Technically not required, but ensures all is set up to start on boot.)
