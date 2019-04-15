import os
import shutil
import sys
from subprocess import CalledProcessError
from unittest.mock import Mock

import pytest
from jupyterhub.objects import Hub, Server

from terraformspawner import TerraformSpawner


class MockUser(Mock):
    name = 'myname'
    escaped_name = 'myname'
    server = Server()

    @property
    def url(self):
        return self.server.url


@pytest.fixture()
def spawner(tmpdir):
    rv = TerraformSpawner(hub=Hub(), user=MockUser())
    rv.tf_bin = os.path.join(sys.base_exec_prefix, 'bin', 'terraform')
    rv.tf_dir = tmpdir.dirname
    rv.tf_module_source = os.path.join(os.path.dirname(__file__), 'terraform-mock-jupyterhub-singleuser')

    return rv


def test__build_tf_module(spawner):
    # Configure Spawner
    spawner.tf_module_source = 'sodre/jupyterhub-singleuser/triton'

    # Create the module_tf
    module_tf = spawner._build_tf_module()

    # Check it contains some of the expected data
    assert spawner.tf_module_source in module_tf
    assert spawner.get_module_id() in module_tf

    assert 'JUPYTERHUB_API_TOKEN' in module_tf


def test__build_tf_module_inheritance(spawner):
    # Create Inherited template
    user_template_dir = os.path.join(spawner.tf_dir, "templates")
    src_inherited_template = os.path.join(os.path.dirname(__file__), 'templates', 'singleuser_inheritance.tf')
    dst_inherited_template = os.path.join(user_template_dir, 'singleuser.tf')

    # Copy the src template to the destination
    os.makedirs(user_template_dir)
    shutil.copyfile(src_inherited_template, dst_inherited_template)

    # Create the module_tf
    module_tf = spawner._build_tf_module()

    assert 'this is from pytest' in module_tf


def test__write_tf_module(spawner):
    tf_module = spawner._build_tf_module()

    spawner._write_tf_module()

    with open(spawner.get_module_file()) as f:
        assert tf_module == f.read()


@pytest.mark.asyncio
def test_tf_check_call(spawner):
    yield from spawner.tf_check_call('-help')

    with pytest.raises(CalledProcessError):
        yield from spawner.tf_check_call('does-not-exist')


@pytest.mark.asyncio
def test_start(spawner):
    # noinspection PyTupleAssignmentBalance
    (ip, port) = yield from spawner.start()
    assert os.path.exists(spawner.get_module_file())
    assert port == 8888
    assert ip == '127.0.0.1'


@pytest.mark.asyncio
def test_stop(spawner):
    yield from spawner.start()

    yield from spawner.stop()
    assert not os.path.exists(spawner.get_module_file())


@pytest.mark.asyncio
def test_poll(spawner):
    # If poll is called before start, the state is unknown
    state = yield from spawner.poll()
    assert state == 0

    # Now we actually start it
    yield from spawner.start()

    state = yield from spawner.poll()
    assert state is None
