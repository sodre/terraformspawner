from tornado import gen
from subprocess import check_call, check_output

from jupyterhub.spawner import Spawner
from traitlets import Int, Unicode

import os
import json


class TerraformSpawner(Spawner):
    """A Spawner for JupyterHub that uses Terraform to run each user's server"""

    tf_dir = Unicode(".",
        help="""
        Path to location where the terraform files will be generated.

        defaults to current working directory.
        """
    ).tag(config=True)

    tf_module = Unicode('/Users/sodre/git/sodre/terraform-null-jupyterhub-singleuser',
        help="""
        The Terraform Module name for the Spawner

        defaults to sodre/terraform-null-jupyterhub-singleuser module
        """
    ).tag(config=True)

    @gen.coroutine
    def start(self):
        """
           Generate a terraform module config file
           call terraform apply
           extract the IP and PORT from terraform output section
        """

        # create module
        module_id = self.get_module_id()
        self._create_module()

        # terraform apply
        self.tf_apply()

        # Get state from terraform
        ip = self.tf_output('ip')
        port = int(self.tf_output('port'))

        return (ip, port)

    @gen.coroutine
    def stop(self, now=False):
        """
        """
        module_id = self.get_module_id()
        module_file = self.get_module_file()

        if os.path.exists(module_file):
            check_call(['terraform', 'destroy', '-auto-approve',
                        '-target', 'module.%s' % module_id], cwd=self.tf_dir)
            os.remove(module_file)

    @gen.coroutine
    def poll(self):
        """Check if the single-user process is running
           return None if it is, an exit status (0 if unknown) if it is not.
        """
        module_id = self.get_module_id()
        module_file = self.get_module_file()

        if not os.path.exists(module_file):
            return 0

        self.tf_apply()
        state = self.tf_output('state')

        return int(state) if state != "" else None

    def get_module_id(self):
        return self.user.escaped_name

    def get_module_file(self):
        return os.path.join(self.tf_dir, self.get_module_id() + ".tf")

    def tf_apply(self):
        module_id = self.get_module_id()

        check_call(['terraform', 'apply', '-auto-approve',
                    '-target', 'module.%s'%module_id], cwd=self.tf_dir)

    def tf_output(self, variable):
        """
           Returns the Terraform variable output for the current module
        """

        module_id = self.get_module_id()
        return check_output(['terraform', 'output', '-module', module_id, variable],
                            cwd=self.tf_dir).strip().decode('utf-8')

    def _create_module(self):
        """
           Creates a Terraform configuration for this Spawner

           returns the module_id
        """

        # Create the terraform configuration
        module_id = self.get_module_id()
        module_file = self.get_module_file()

        module_body = {
          "source" : self.tf_module,
          "env" :  self.get_env(),
        }

        with open(module_file, 'w') as f:
            json.dump({ "module" : { module_id : module_body } }, f)

        # Reinitialize Terraform
        check_call(['terraform', 'init'], cwd=self.tf_dir)
