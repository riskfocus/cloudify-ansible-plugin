cloudify-ansible-plugin
========================

### Please note this plugin is under development and not yet officially supported. Use with Care!

The Ansible plugin can be used to run Ansible Playbooks against a single node in a Cloudify Blueprint.

## Usage

See [Ansible Plugin](http://getcloudify.org/guide/3.2/plugins-ansible.html) for Cloudify original plugin details.

## Usage example
```
  ansiblefied_node.type:
    derived_from: cloudify.nodes.Root
    properties:
      key1:
        type: string
        default: { get_input: value1 }
      key2:
        type: string
        default: { get_attribute: value2 }
    interfaces:
      cloudify.interfaces.lifecycle:
        configure:
          implementation: ansible.ansible_plugin.tasks.configure
          inputs:
            user:
              default: ansibleuser
        start:
          implementation: ansible.ansible_plugin.tasks.ansible_playbook
          inputs:
            inventory:
              default:
                - { get_attribute: [ ansiblefied_node, ip ] }
            playbooks:
              default:
                - resources/ansible/os/site.yaml
                - resources/ansible/app1/site.yaml
            extravars:
              default: {concat [ 'key1=', { get_attribute: [ ansiblefied_node, value1 ] } ,' key2=', { get_attribute: [ ansiblefied_node, value2 ] }]}
```
### ansible_playbook inputs:
* inventory - required
* playbooks - required
* extravars - optional
