from tornado import gen
from subprocess import check_call, check_output

from jupyterhub.spawner import Spawner
from traitlets import Int

import json
import pdb

class TerraformSpawner(Spawner):
    """A Spawner for JupyterHub that uses Terraform to run each user's server"""

    tf_dir = '/Users/sodre/git/sodre/terraform-null-jupyterhub-singleuser'
    http_timeout = Int(30)
    start_timeout = Int(60)

    @gen.coroutine
    def start(self):
        """
           Generate a terraform config file
           call terraform apply
        """

        #pdb.set_trace()
        # Create the terraform configuration
        env = self.get_env()

        # terraform init

        # terraform apply
        check_call([
            'terraform',
            'apply',
            '-auto-approve',
            '-var', 'api_token={}'.format(self.api_token)],
            cwd=self.tf_dir)

        # Get state from terraform
        self.ip = check_output(['terraform', 'output', 'ip'],
                          cwd=self.tf_dir).strip().decode('utf-8')
        self.port = int(check_output(['terraform', 'output', 'port'],
                            cwd=self.tf_dir).strip().decode('utf-8'))

        return (self.ip, self.port)

    @gen.coroutine
    def stop(self, now=False):
        check_call([
          'terraform',
          'destroy',
          '-auto-approve',
          '-var', 'api_token={}'.format(self.api_token)],
          cwd=self.tf_dir)

    @gen.coroutine
    def poll(self):
        """Check if the single-user process is running
           return None if it is, an exit status (0 if unknown) if it is not.
        """
        state = check_output(['terraform', 'output', 'state'],
                             cwd=self.tf_dir).strip().decode('utf-8')

        return int(state) if state != "" else None

