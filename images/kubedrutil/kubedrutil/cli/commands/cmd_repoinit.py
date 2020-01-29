
import os
import pprint
import subprocess
import time

import click

from kubedrutil.cli import context
from kubedrutil.common import kubeclient

def validate_env(envlist):
    for name in envlist:
        val = os.environ.get(name, None)
        if not val:
            raise Exception("Env variable {} is not set".format(name))

@click.command()
@context.pass_context
def cli(ctx):
    """Initialize a backup repository.

    """

    validate_env(["AWS_ACCESS_KEY", "AWS_SECRET_KEY", "RESTIC_PASSWORD", 
                  "RESTIC_REPO", "KDR_BACKUPLOC_NAME", ])
    backuploc_api = kubeclient.BackupLocationAPI("kubedr-system")
    name = os.environ["KDR_BACKUPLOC_NAME"]

    statusdata = {
        "initStatus": "Completed", 
        "initErrorMessage": "",
        "initTime": time.asctime()
    }

    cmd = ["restic", "-r", os.environ["RESTIC_REPO"], "--verbose", "init"]
    print("Running the init command: ({})".format(cmd))
    resp = subprocess.run(cmd, stderr=subprocess.PIPE)
    pprint.pprint(resp)

    if resp.returncode != 0:
        # Initialization failed.
        errMsg = resp.stderr.decode("utf-8")
        statusdata["initStatus"] = "Failed"
        statusdata["initErrorMessage"] = errMsg
        backuploc_api.patch_status(name, {"status": statusdata})

        raise Exception("Initialization failed, reason: {}".format(errMsg))

    print("Setting the annotation...")
    cmd = ["kubectl", "annotate", "backuplocation", name,
           "initialized.annotations.kubedr.catalogicsoftware.com=true"]
    resp = subprocess.run(cmd)
    backuploc_api.patch_status(name, {"status": statusdata})
    subprocess.run(["kubectl", "get", "backuplocation", name, "-o", "yaml"])



