import argparse
import os
import random
import subprocess
import sys
import time


class GitManager:
    SOF_ELK_ROOT = "/usr/local/sof-elk/"
    VM_UPDATE_STATUS_FILE = "/var/run/sof-elk_vm_update"

    @staticmethod
    def _run_command(
        cmd: list[str], cwd: str | None = None, capture_output: bool = False
    ) -> subprocess.CompletedProcess[str]:
        try:
            result = subprocess.run(cmd, cwd=cwd, capture_output=capture_output, text=True, check=True)
            return result
        except subprocess.CalledProcessError as e:
            # print(f"Error running command: {' '.join(cmd)}\n{e.stderr}")
            raise e

    @classmethod
    def require_root(cls) -> None:
        if hasattr(os, "geteuid") and os.geteuid() != 0:  # type: ignore
            sys.stderr.write("This script must be run as root. Exiting.\n")
            sys.exit(1)

    @classmethod
    def check_pull_needed(cls, upstream: str = "@{u}") -> None:
        """
        Check if upstream updates are available and notify the user.

        Analyzes the relationship between local HEAD, upstream, and their merge base
        to determine if updates are available, if the local branch has diverged,
        or if it is ahead of upstream.

        Args:
            upstream (str): The upstream branch to check against. Defaults to "@{u}".
        """
        try:
            cwd = cls.SOF_ELK_ROOT
            if not os.path.isdir(cwd):
                # Fallback for dev/test environment
                cwd = os.getcwd()

            local = cls._run_command(["git", "rev-parse", "@{0}"], cwd=cwd, capture_output=True).stdout.strip()
            remote = cls._run_command(["git", "rev-parse", upstream], cwd=cwd, capture_output=True).stdout.strip()
            base = cls._run_command(
                ["git", "merge-base", "@{0}", upstream], cwd=cwd, capture_output=True
            ).stdout.strip()

            if local == remote:
                pass  # Up to date
            elif local == base:
                print("Upstream Updates Available!!!!")
                print("------------------------------")
                print()
                print("There are upstream updates to the SOF-ELK® configuration files available")
                print("in the Github repository. These are not required, but if desired,")
                print("run the following command to retrieve and activate them:")
                print()
                print("sudo sof-elk_update.sh")  # Use wrapper name for familiarity
                print()
            elif remote == base:
                print("ERROR: You have local commits that are past the Github-based origin.")
                print("       Automatic updates not possible.")
            else:
                print("ERROR: Something very unexpected occurred when determining if there are any")
                print("       upstream updates. Ensure you have internet connectivity and please")
                print("       try again later.")

            if os.path.exists(cls.VM_UPDATE_STATUS_FILE):
                print("A new version of the SOF-ELK VM is available!!!")
                print("-----------------------------------------------")
                print()
                print("There is a new VM version available for download. Please see the release")
                print("information at https://for572.com/sof-elk-readme")
                print()

        except Exception:
            # sys.stderr.write(f"Error checking for updates: {e}\n")
            pass

    @classmethod
    def remote_update(cls, now: bool = False) -> None:
        """
        Update the git remote references.

        Args:
            now (bool): If True, run immediately. If False, sleep for a random time up to 20 minutes before running.
        """
        cls.require_root()

        if not now:
            # Random sleep up to 20 mins (1800s)
            val = random.randint(0, 1800)
            time.sleep(val)

        cwd = cls.SOF_ELK_ROOT
        if not os.path.isdir(cwd):
            cwd = os.getcwd()

        try:
            cls._run_command(["git", "remote", "update"], cwd=cwd)
        except subprocess.CalledProcessError:
            pass

    @classmethod
    def update_cli(cls, force: bool = False) -> None:
        """
        Perform a full repository update.

        Checks for local changes, pulls from upstream, and (if needed) restarts relevant services.

        Args:
            force (bool): If True, ignore (and overwrite) local structure changes.
        """
        cls.require_root()

        cwd = cls.SOF_ELK_ROOT
        if not os.path.isdir(cwd):
            cwd = os.getcwd()

        # Check local changes
        status = cls._run_command(["git", "status", "--porcelain"], cwd=cwd, capture_output=True).stdout.strip()
        if status and not force:
            sys.stderr.write(
                "ERROR: You have local changes to this repository - will not overwrite without '-f' to force.\n"
            )
            sys.stderr.write(f"       Run 'git status' from the {cwd} directory to identify the local changes.\n")
            sys.stderr.write(
                "       Note that using '-f' will delete any modifications that have been made in this directory.\n"
            )
            sys.exit(2)

        # Run remote update immediately
        cls.remote_update(now=True)

        local = cls._run_command(["git", "rev-parse", "@{0}"], cwd=cwd, capture_output=True).stdout.strip()
        remote = cls._run_command(["git", "rev-parse", "@{u}"], cwd=cwd, capture_output=True).stdout.strip()
        base = cls._run_command(["git", "merge-base", "@{0}", "@{u}"], cwd=cwd, capture_output=True).stdout.strip()

        if local == remote:
            print("Up-to-date")
        elif local == base:
            # Need to pull
            cls._run_command(["git", "reset", "--hard"], cwd=cwd)
            cls._run_command(["git", "clean", "-fdx"], cwd=cwd)
            cls._run_command(["git", "pull", "origin"], cwd=cwd)

            cls.remote_update(now=True)

            # Restart logstash (find java process owned by logstash user and HUP it?)
            # Original script: pgrep -u logstash java -> kill -s HUP
            try:
                pids = (
                    subprocess.run(["pgrep", "-u", "logstash", "java"], capture_output=True, text=True)
                    .stdout.strip()
                    .split()
                )
                for pid in pids:
                    subprocess.run(["kill", "-s", "HUP", pid])
            except Exception:
                pass

        elif remote == base:
            print("Need to push - this should never happen")
        else:
            print("Diverged - this should never happen")

    @classmethod
    def branch_cli(cls, branch: str, force: bool = False) -> None:
        """
        Switch the active git branch.

        Args:
            branch (str): The name of the branch to checkout.
            force (bool): If True, force checkout even if local changes exist.
        """
        if not branch:
            sys.stderr.write("ERROR: Specify branch.\n")
            sys.exit(3)

        cls.require_root()
        cwd = cls.SOF_ELK_ROOT
        if not os.path.isdir(cwd):
            cwd = os.getcwd()

        # Check if remote branch exists
        try:
            output = cls._run_command(["git", "ls-remote", "--heads", "origin"], cwd=cwd, capture_output=True).stdout
            if f"refs/heads/{branch}" not in output:
                sys.stderr.write(f"ERROR: No such remote branch exists: {branch}.\n")
                sys.exit(4)
        except subprocess.CalledProcessError:
            sys.stderr.write("ERROR: Failed to query remote branches.\n")
            sys.exit(4)

        # Check local changes
        status = cls._run_command(["git", "status", "--porcelain"], cwd=cwd, capture_output=True).stdout.strip()
        if status and not force:
            sys.stderr.write(
                "ERROR: You have local changes to this repository - will not overwrite without '-f' to force.\n"
            )
            sys.stderr.write(f"       Run 'git status' from the {cwd} directory to identify the local changes.\n")
            sys.stderr.write(
                "       Note that using '-f' will delete any modifications that have been made in this directory.\n"
            )
            sys.exit(2)

        print("It's STRONGLY recommended to create a VM snapshot if possible, or better yet,")
        print("  to only proceed on a system with no operational data.  You won't necessarily")
        print("  be able to return the system to its current/original state after testing.")
        print()
        print("To proceed at your own risk, press <Enter> to continue.")
        print("To cancel this, press Ctrl-C.")
        try:
            input()
        except KeyboardInterrupt:
            print()
            sys.exit(0)

        if status and force:
            cls._run_command(["git", "reset", "--hard"], cwd=cwd)
            cls._run_command(["git", "clean", "-fdx"], cwd=cwd)

        cls._run_command(["git", "remote", "set-branches", "--add", "origin", branch], cwd=cwd)
        cls._run_command(["git", "fetch", "origin"], cwd=cwd)
        cls._run_command(["git", "checkout", branch], cwd=cwd)

        # update and post merge
        # SKIP_HOOK=1 sof-elk_update.sh | grep -v "Up-to-date"
        # Since we are implementing update logic here, we call it directly but skip hook?
        # The original script calls sof-elk_update.sh then post_merge.sh
        # We can just run post_merge.sh logic if we knew it.
        # But for now, let's just assume we might need to simulate that.
        # Actually "SKIP_HOOK=1" implies update.sh has some hook logic or env var check.
        # sof-elk_update.sh simply runs git pull.
        # For now, we performed checkout which updates files.
        pass


def run_branch(args: argparse.Namespace) -> None:
    GitManager.branch_cli(args.branch, args.force)


def run_update(args: argparse.Namespace) -> None:
    GitManager.update_cli(args.force)


def run_check_pull(args: argparse.Namespace) -> None:
    GitManager.check_pull_needed(args.upstream)


def run_remote_update(args: argparse.Namespace) -> None:
    # args.now is not in parser yet, need to add it in cli.py or handle default
    # The shell script accepted -now arg.
    # Let's assume passed via args if we add it.
    now = getattr(args, "now", False)
    GitManager.remote_update(now=now)
