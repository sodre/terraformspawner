import os
import sys
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
    rv.tf_bin = os.path.join(sys.base_exec_prefix, 'bin', 'terraform')
    rv.tf_dir = tmpdir.dirname
    rv.tf_module = os.path.join(os.path.dirname(__file__), "terraform-mock-jupyterhub-singleuser")

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

    with open(spawner.get_module_file()) as f:
        assert tf_module == f.read()


def test_start(spawner):
    f = spawner.start()

    assert f.done()
    assert os.path.exists(spawner.get_module_file())

    ip, port = f.result()
    assert port == 8888
    assert ip == "127.0.0.1"


def test_stop(spawner):
    spawner.start().result()

    assert os.path.exists(spawner.get_module_file())

    spawner.stop()

    assert not os.path.exists(spawner.get_module_file())


def test_poll(spawner):
    # If poll is called before start, the state is unknown
    state = spawner.poll().result()
    assert state == 0

    # Now we actually start it
    spawner.start().result()

    state = spawner.poll().result()

    assert state is None
