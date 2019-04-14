import os
from asyncio.subprocess import create_subprocess_exec
from subprocess import check_output, CalledProcessError

from jinja2 import Environment, PackageLoader
from jupyterhub.spawner import Spawner
from tornado import gen
from traitlets import Unicode


class TerraformSpawner(Spawner):
    """A Spawner for JupyterHub that uses Terraform to run each user's server"""

    tf_bin = Unicode("terraform",
        help="""
        The location of the terraform binary.
        
        defaults to terraform.
        """
    ).tag(config=True)

    tf_dir = Unicode(".",
        help="""
        Path to location where the terraform files will be generated.

        defaults to current working directory.
        """
    ).tag(config=True)

    tf_module = Unicode('sodre/jupyterhub-singleuser/null',
        help="""
        The Terraform Module name for the Spawner

        defaults to sodre/terraform-null-jupyterhub-singleuser module
        """
    ).tag(config=True)

    tf_jinja_env = Environment(
        loader=PackageLoader("terraformspawner", "templates")
    )

    @gen.coroutine
    def start(self):
        """
           Generate a terraform module config file
           call terraform apply
           extract the IP and PORT from terraform output section
        """

        # create module
        self._write_tf_module()

        # (Re)Initialize Terraform
        yield self.tf_check_call('init')

        # Terraform Apply (locally)
        yield self.tf_apply()

        (ip, port) = (None, None)
        while ip is None or port is None:
            # Terraform Refresh (globally)
            yield self.tf_check_call('refresh')
            try:
                ip = self.tf_output('ip')
                port = int(self.tf_output('port'))
            except:
                pass

        return ip, port

    @gen.coroutine
    def stop(self, now=False):
        """
        """
        module_id = self.get_module_id()
        module_file = self.get_module_file()

        if os.path.exists(module_file):
            self.tf_destroy()
            os.remove(module_file)

    @gen.coroutine
    def poll(self):
        """Check if the single-user process is running
           return None if it is, an exit status (0 if unknown) if it is not.
        """

        module_file = self.get_module_file()
        if not os.path.exists(module_file):
            return 0

        yield self.tf_check_call('refresh')

        # Get state from terraform
        state = self.tf_output('state')

        return int(state) if state != "" else None

    def get_module_id(self):
        return self.user.escaped_name

    def get_module_file(self):
        return os.path.join(self.tf_dir, self.get_module_id() + ".tf")

    def _write_tf_module(self):
        """
        Writes the module.tf file to the tf_dir directory.
        :return:
        """
        module_tf_content = self._build_tf_module()
        with open(self.get_module_file(), 'w') as f:
            f.write(module_tf_content)

    def _build_tf_module(self):
        """
        Creates a Terraform configuration for this Spawner

        :return: rendered module_tf content
        """
        tf_template = self.tf_jinja_env.get_or_select_template('single_user.tf')
        return tf_template.render(spawner=self)

    @gen.coroutine
    def tf_check_call(self, *args, **kwargs):
        proc = yield create_subprocess_exec(self.tf_bin, *args, **kwargs, cwd=self.tf_dir)
        yield proc.wait()
        if proc.returncode != 0:
            raise CalledProcessError(proc.returncode, self.tf_bin)

    @gen.coroutine
    def tf_apply(self):
        module_id = self.get_module_id()
        yield self.tf_check_call('apply', '-auto-approve', '-target', 'module.%s' % module_id)

    @gen.coroutine
    def tf_destroy(self):
        module_id = self.get_module_id()
        yield self.tf_check_call('destroy', '-auto-approve', '-target', 'module.%s' % module_id)

    def tf_output(self, variable):
        """
           Returns the Terraform variable output for the current module
        """
        module_id = self.get_module_id()
        return check_output([self.tf_bin, 'output', '-module', module_id, variable],
                            cwd=self.tf_dir).strip().decode('utf-8')
