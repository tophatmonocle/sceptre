# -*- coding: utf-8 -*-

from sceptre.hooks import Hook
from sceptre.exceptions import InvalidHookArgumentTypeError
from sceptre.exceptions import InvalidHookArgumentSyntaxError
from sceptre.exceptions import InvalidHookArgumentValueError


class ASGScalingProcesses(Hook):
    """
    Resumes or suspends autoscaling group scaling processes. This is
    useful as scheduled actions must be suspended when updating stacks with
    autoscaling groups.
    """

    def __init__(self, *args, **kwargs):
        super(ASGScalingProcesses, self).__init__(*args, **kwargs)

    def run(self):
        """
        Either suspends or resumes any scaling processes on all autoscaling
        groups within the current stack.

        :raises: InvalidHookArgumentSyntaxError, when syntax is not using "::".
        :raises: InvalidHookArgumentTypeError, if argument is not a string.
        :raises: InvalidHookArgumentValueError, if not using resume or suspend.
        """

        if not isinstance(self.argument, basestring):
            raise InvalidHookArgumentTypeError(
                'The argument "{0}" is the wrong type - asg_scaling_processes '
                'hooks require arguments of type string.'.format(self.argument)
            )
        if "::" not in str(self.argument):
            raise InvalidHookArgumentSyntaxError(
                'Wrong syntax for the argument "{0}" - asg_scaling_processes '
                'hooks use:'
                '- !asg_scaling_processes <suspend|resume>::<process-name>'
                .format(self.argument)
            )

        action, scaling_processes = self.argument.split("::")

        if action not in ["resume", "suspend"]:
            raise InvalidHookArgumentValueError(
                'The argument "{0}" is invalid - valid arguments for '
                'asg_scaling_processes hooks are "resume" or "suspend".'
                .format(action)
            )

        action += "_processes"

        autoscaling_group_names = self._find_autoscaling_groups()
        for autoscaling_group in autoscaling_group_names:
            self.connection_manager.call(
                service="autoscaling",
                command=action,
                kwargs={
                    "AutoScalingGroupName": autoscaling_group,
                    "ScalingProcesses": [scaling_processes]
                }
            )

    def _get_stack_resources(self):
        """
        Retrieves all resources in stack.
        :return: list
        """
        full_stack_name = "-".join([
            self.environment_config["project_code"],
            self.environment_config.environment_path,
            self.stack_config.name
        ]).replace("/", "-")
        response = self.connection_manager.call(
            service="cloudformation",
            command="describe_stack_resources",
            kwargs={"StackName": full_stack_name}
        )
        return response.get("StackResources", [])

    def _find_autoscaling_groups(self):
        """
        Retrieves all the autoscaling groups
        :return: list [str]
        """
        asg_names = []
        resources = self._get_stack_resources()
        resource_type = "AWS::AutoScaling::AutoScalingGroup"
        for resource in resources:
            if resource.get("ResourceType", False) == resource_type:
                asg_names.append(resource["PhysicalResourceId"])

        return asg_names
