from tornado import gen
from subprocess import check_call, check_output

from jupyterhub.spawner import Spawner
from traitlets import Int

import json

class TerraformSpawner(Spawner):
    """A Spawner for JupyterHub that uses Terraform to run each user's server"""

    tf_dir = '/Users/sodre/git/sodre/terraform-null-jupyterhub-singleuser'

    @gen.coroutine
    def start(self):
        """
           Generate a terraform config file
           call terraform apply
        """

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
        ip = check_output(['terraform', 'output', 'ip'],
                          cwd=self.tf_dir).strip().decode('utf-8')
        port = int(check_output(['terraform', 'output', 'port'],
                            cwd=self.tf_dir).strip().decode('utf-8'))

        return (ip, port)

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
        check_call([
            'terraform',
            'apply',
            '-auto-approve',
            '-var', 'api_token={}'.format(self.api_token)],
            cwd=self.tf_dir)

        state = check_output(['terraform', 'output', 'state'],
                             cwd=self.tf_dir).strip().decode('utf-8')

        return int(state) if state != "" else None

