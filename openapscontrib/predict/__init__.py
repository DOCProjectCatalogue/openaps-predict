"""
predict - tools for predicting glucose trends


"""
from .version import __version__

import argparse
from dateutil.parser import parse
import json

from openaps.uses.use import Use

from predict import Schedule
from predict import foo


# set_config is needed by openaps for all vendors.
# set_config is used by `device add` commands so save any needed
# information.
# See the medtronic builtin module for an example of how to use this
# to save needed information to establish sessions (serial numbers,
# etc).
def set_config(args, device):
    # no special config
    return


# display_device allows our custom vendor implementation to include
# special information when displaying information about a device using
# our plugin as a vendor.
def display_device(device):
    # no special information needed to run
    return ''


# openaps calls get_uses to figure out how how to use a device using
# agp as a vendor.  Return a list of classes which inherit from Use,
# or are compatible with it:
def get_uses(device, config):
    return [glucose]


def _opt_date(timestamp):
    """Parses a date string if defined

    :param timestamp: The date string to parse
    :type timestamp: basestring
    :return: A datetime object if a timestamp was specified
    :rtype: datetime.datetime|NoneType
    """
    if timestamp:
        return parse(timestamp)


def _json_file(filename):
    return json.load(argparse.FileType('r')(filename))


def _opt_json_file(filename):
    """Parses a filename as JSON input if defined

    :param filename: The path to the file to parse
    :type filename: basestring
    :return: A decoded JSON object if a filename was specified
    :rtype: dict|list|NoneType
    """
    if filename:
        return _json_file(filename)


class glucose(Use):
    """Predict glucose

    """
    def configure_app(self, app, parser):
        """Define command arguments.

        Only primitive types should be used here to allow for serialization and partial application
        in via openaps-report.
        """
        parser.add_argument(
            'normalized-history',
            help='JSON-encoded history data file, normalized by openapscontrib.mmhistorytools'
        )

        parser.add_argument(
            'normalized-glucose',
            help='JSON-encoded glucose data file, normalized by openapscontrib.glucosetools'
        )

        parser.add_argument(
            '--settings',
            nargs=argparse.OPTIONAL,
            help='JSON-encoded pump settings file, optional if --idur is set'
        )

        parser.add_argument(
            '--insulin-action-curve', '--idur',
            nargs=argparse.OPTIONAL,
            type=float,
            choices=range(3, 7),
            help='Insulin action curve, optional if --settings is set'
        )

        parser.add_argument(
            '--insulin-sensitivities', '--sensf',
            help='JSON-encoded insulin sensitivities schedule file'
        )

        parser.add_argument(
            '--carb-ratios', '--cratio',
            help='JSON-encoded carb ratio schedule file'
        )

        parser.add_argument(
            '--basal-dosing-end',
            nargs=argparse.OPTIONAL,
            help='The timestamp at which temp basal dosing should be assumed to end, '
                 'as a JSON-encoded pump clock file'
        )

    def get_params(self, args):
        params = dict(**args.__dict__)

        if params.get('settings') is None:
            params.pop('settings', None)

        if params.get('insulin_action_curve') is None:
            params.pop('insulin_action_curve', None)

        if params.get('basal_dosing_end') is None:
            params.pop('basal_dosing_end', None)

        params.pop('use', None)
        params.pop('action', None)
        params.pop('report', None)

        return params

    def get_program(self, params):
        """Parses params into history parser constructor arguments

        :param params:
        :type params: dict
        :return:
        :rtype: tuple(list, dict)
        """
        args = (
            _json_file(params['normalized-history']),
            _json_file(params.get['normalized-glucose']),
            params.get('insulin_action_curve', None) or
            _opt_json_file(params.get('settings', ''))['insulin_action_curve'],
            Schedule(_json_file(params['insulin_sensitivities'])['sensitivities']),
            Schedule(_json_file(params['carb_ratios'])['schedule']),
        )

        return args, dict(basal_dosing_end=_opt_date(_opt_json_file(params.get('basal_dosing_end'))))

    def main(self, args, app):
        args, kwargs = self.get_program(self.get_params(args))

        return foo(*args, **kwargs)
