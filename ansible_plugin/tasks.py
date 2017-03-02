########
# Copyright (c) 2017 Riskfocus LV Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

# Built-in Imports
import os
import shutil
import shlex

# Third-party Imports

# Cloudify imports
from cloudify import ctx
from ansible_plugin import utils
from cloudify.decorators import operation


@operation
def configure(user=None, key=None, **kwargs):

    agent_key_path = utils.get_keypair_path(key)

    configuration = '[defaults]\n' \
                    'host_key_checking=False\n' \
                    'private_key_file={}\n'.format(agent_key_path)

    ctx.logger.info('Configuring Anisble.')
    file_path = utils.write_configuration_file(configuration)
    ctx.logger.info('Configured Ansible.')

    os.environ['ANSIBLE_CONFIG'] = file_path
    os.environ['USER'] = utils.get_agent_user(user)
    os.environ['HOME'] = home = os.path.expanduser("~")

    if os.path.exists(os.path.join(home, '.ansible')):
        shutil.rmtree(os.path.join(home, '.ansible'))

    os.makedirs(os.path.join(home, '.ansible'))


@operation
def ansible_playbook(playbooks, inventory=list(), extravars='', **kwargs):
    """ Runs a playbook as part of a Cloudify lifecycle operation """

    inventory_path = utils.get_inventory_path(inventory)
    ctx.logger.info('Inventory path: {}.'.format(inventory_path))
    extraargs = ' --extra-vars "{}"'.format(extravars) if extravars else ''
    for playbook in playbooks:
        playbook_path = utils.get_playbook_path(playbook)
        ctx.logger.info('Playbook path: {}.'.format(playbook_path))
        user = utils.get_agent_user()
        # command = ['ansible-playbook', '--sudo', '-u', user,
        #            '-i', inventory_path, '--timeout=60', '-vvvv']
        # if extraargs:
        #     command += shlex.split(extraargs)
        # command += shlex.split(playbook_path)
        command = 'ansible-playbook --sudo -u {} -i {} {} --timeout=60 -vvvv{}'.format(user,inventory_path,playbook_path,extraargs if extraargs else '')
        ctx.logger.info('Running command: {}.'.format(command))
        output = utils.run_command(command)
        ctx.logger.info('Command Output: {}.'.format(output))
        ctx.logger.info('Finished running the Ansible Playbook.')
