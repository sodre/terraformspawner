from unittest.mock import Mock

from jupyterhub.objects import Hub, Server

from terraformspawner import TerraformSpawner


class MockUser(Mock):
    name = 'myname'
    escaped_name = "myname"
    server = Server()

    @property
    def url(self):
        return self.server.url


def test__build_tf_module():
    spawner = TerraformSpawner(hub=Hub(), user=MockUser())

    # Configure Spawner
    spawner.tf_module = "sodre/jupyterhub-singleuser/triton"

    # Create the module_tf
    module_tf = spawner._build_tf_module()

    # Check it contains some of the expected data
    assert spawner.tf_module in module_tf
    assert spawner.get_module_id() in module_tf

    assert 'JUPYTERHUB_API_TOKEN' in module_tf
