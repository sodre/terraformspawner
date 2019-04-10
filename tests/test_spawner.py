import os
from unittest.mock import Mock

import pytest
from jupyterhub.objects import Hub, Server

from terraformspawner import TerraformSpawner


class MockUser(Mock):
    name = 'myname'
    escaped_name = "myname"
    server = Server()

    @property
    def url(self):
        return self.server.url


@pytest.fixture()
def spawner(tmpdir):
    rv = TerraformSpawner(hub=Hub(), user=MockUser())
    rv.tf_dir = tmpdir.dirname

    return rv


def test__build_tf_module(spawner):
    # Configure Spawner
    spawner.tf_module = "sodre/jupyterhub-singleuser/triton"

    # Create the module_tf
    module_tf = spawner._build_tf_module()

    # Check it contains some of the expected data
    assert spawner.tf_module in module_tf
    assert spawner.get_module_id() in module_tf

    assert 'JUPYTERHUB_API_TOKEN' in module_tf


def test__write_tf_module(spawner):
    tf_module = spawner._build_tf_module()

    spawner._write_tf_module()

    tf_module_file = os.path.join(spawner.tf_dir, spawner.get_module_file())
    with open(tf_module_file) as f:
        assert tf_module == f.read()
