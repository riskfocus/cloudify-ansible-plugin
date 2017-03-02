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
import re
import tempfile
import requests
from subprocess import Popen, PIPE

# Third-party Imports

# Cloudify imports
from cloudify import ctx
from cloudify import exceptions

CLOUDIFY_MANAGER_PRIVATE_KEY_PATH = 'CLOUDIFY_MANAGER_PRIVATE_KEY_PATH'


def _download_playbook_templates(playbook, playbook_local_path):
    cloudify_url = os.environ['MANAGER_FILE_SERVER_BLUEPRINTS_ROOT_URL']
    ctx.logger.debug('cloudify_url: {}'.format(cloudify_url))
    blueprint_id = ctx.blueprint.id
    ctx.logger.debug('blueprint_id: {}'.format(blueprint_id))
    cloudify_playbook_url = os.path.dirname(playbook)
    ctx.logger.debug('cloudify_playbook_url: {}'.format(cloudify_playbook_url))
    playbook_templates_url = '{}/{}/{}/templates'.format(cloudify_url, blueprint_id, cloudify_playbook_url)
    ctx.logger.debug('playbook_templates_url: {}'.format(playbook_templates_url))
    playbook_local_dir = os.path.dirname(playbook_local_path)
    ctx.logger.debug('playbook_local_dir: {}'.format(playbook_local_dir))

    template_file_pattern = re.compile(r'href=\"(\w.*)\"')

    if os.path.isdir(playbook_local_dir):
        playbook_templates_local_path = '{}/templates'.format(playbook_local_dir)
        os.makedirs(playbook_templates_local_path)
    else:
        raise exceptions.NonRecoverableError(
            'Could not find playbook directory {}.'.format(playbook_local_dir))

    directory_listing_response = requests.get('{}'.format(playbook_templates_url))
    ctx.logger.debug('directory_listing_response: {}'.format(directory_listing_response.text))
    if directory_listing_response.status_code == requests.codes.ok:
        ctx.logger.info('{} template folder found on source server:'.format(cloudify_playbook_url))

        for template_file in template_file_pattern.findall(directory_listing_response.content):
            remote_template_file = '{}/{}'.format(playbook_templates_url, template_file)
            ctx.logger.debug('remote_template_file: {}'.format(remote_template_file))
            template_file_response = requests.get(remote_template_file)
            if template_file_response.status_code == requests.codes.ok:
                template_file_local_path = '{}/{}'.format(playbook_templates_local_path, template_file)
                ctx.logger.debug('template_file_local_path: {}'.format(template_file_local_path))
                try:
                    template_file_write = open(template_file_local_path, 'wb')
                    template_file_write.write(template_file_response.content)
                    template_file_write.close()
                    ctx.logger.info('Downloaded template {}'.format(template_file_local_path))
                except:
                    raise exceptions.NonRecoverableError(
                        'Issue creating template {}'.format(template_file_local_path))
            else:
                raise exceptions.NonRecoverableError(
                    'Issue downloading template {}'.format(template_file))
    else:
        ctx.logger.warn('Template folder for playbook {} not found on source server'.format(playbook))


def get_playbook_path(playbook):
    try:
        path_to_file = ctx.download_resource(playbook)
    except exceptions.HttpException as e:
        raise exceptions.NonRecoverableError(
            'Could not get playbook file: {}.'.format(str(e)))

    _download_playbook_templates(playbook, path_to_file)

    return path_to_file


def get_inventory_path(inventory):
    if not inventory:
        inventory.append(ctx.instance.host_ip)

    _, path_to_file = tempfile.mkstemp()

    with open(path_to_file, 'w') as f:
        for host in inventory:
            f.write('{0}\n'.format(host))

    return path_to_file


def get_agent_user(user=None):
    if not user:
        if 'user' not in ctx.instance.runtime_properties:
            user = ctx.bootstrap_context.cloudify_agent.user
            ctx.instance.runtime_properties['user'] = user
        else:
            user = ctx.instance.runtime_properties['user']
    elif 'user' not in ctx.instance.runtime_properties:
        ctx.instance.runtime_properties['user'] = user

    return user


def get_keypair_path(key=None):
    if not key:
        if 'key' in ctx.instance.runtime_properties:
            key = ctx.instance.runtime_properties['key']
        elif CLOUDIFY_MANAGER_PRIVATE_KEY_PATH in os.environ:
            key = os.environ[CLOUDIFY_MANAGER_PRIVATE_KEY_PATH]
        else:
            key = ctx.bootstrap_context.cloudify_agent.agent_key_path

    if 'key' not in ctx.instance.runtime_properties:
        ctx.instance.runtime_properties['key'] = key

    key = os.path.expanduser(key)
    os.chmod(key, 0600)

    return key


def write_configuration_file(config):
    home = os.path.expanduser("~")

    file_path = os.path.join(home, '.ansible.cfg')

    with open(file_path, 'w') as f:
        f.write(config)

    return file_path


def run_command(command):
    try:
        run = Popen(command, stdout=PIPE, stderr=PIPE)
    except Exception as e:
        raise exceptions.NonRecoverableError(
            'Unable to run command. Error {}'.format(str(e)))

    try:
        stdout, stderr = run.communicate()
    except Exception as e:
        raise exceptions.NonRecoverableError(
            'Unable to run command. Error {}'.format(str(e)))

    if run.returncode:
        ctx.logger.info('Non-zero return code. Stderr {}. Stdout {}'.format(stderr, stdout))
        raise exceptions.NonRecoverableError(
            'Non-zero returncode. Stderr {}. Stdout {}.'.format(stderr, stdout))

    return stdout
