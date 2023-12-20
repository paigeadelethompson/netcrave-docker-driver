from flask import Flask, request, Response
from werkzeug.serving import run_simple
import os

flask_app = Flask(__name__)


@flask_app.errorhandler(NotImplementedError)
def handle_invalid_usage(error):
    pass


@flask_app.route('/Plugin.Activate', methods=['POST'])
def plugin_activate():
    pass


@flask_app.route('/NetworkDriver.GetCapabilities', methods=['POST'])
def plugin_get_capabilities():
    pass


@flask_app.route('/NetworkDriver.CreateNetwork', methods=['POST'])
def plugin_create_network():
    pass


@flask_app.route('/NetworkDriver.DeleteNetwork', methods=['POST'])
def plugin_delete_network():
    pass


@flask_app.route('/NetworkDriver.CreateEndpoint', methods=['POST'])
def plugin_create_endpoint():
    pass


@flask_app.route('/NetworkDriver.EndpointOperInfo', methods=['POST'])
def plugin_endpoint_oper_info():
    pass


@flask_app.route('/NetworkDriver.DeleteEndpoint', methods=['POST'])
def plugin_delete_endpoint():
    pass


@flask_app.route('/NetworkDriver.Join', methods=['POST'])
def plugin_join():
    pass


@flask_app.route('/NetworkDriver.Leave', methods=['POST'])
def plugin_leave():
    pass


@flask_app.route('/NetworkDriver.DiscoverNew', methods=['POST'])
def plugin_discover_new():
    pass


@flask_app.route('/NetworkDriver.DiscoverDelete', methods=['POST'])
def plugin_discover_delete():
    pass


@flask_app.route('/NetworkDriver.ProgramExternalConnectivity',
                 methods=['POST'])
def program_external_connectivity():
    pass


@flask_app.route('/NetworkDriver.RevokeExternalConnectivity', methods=['POST'])
def revoke_external_connectivity():
    pass


def main():
    run_simple(
        hostname='unix:///run/netcrave/ipam/sock',
        application=flask_app,
        use_reloader=True)


def main():
    if os.environ.get("IFCONFIG_SOCK") is None:
        path = "/run/docker/plugins"
        os.makedirs(path, exist_ok=True)
        path = "unix://{}/ifconfig".format(path)
    else:
        path = os.environ.get("ifconfig_SOCK")

    run_simple(
        hostname=path,
        port=0,
        application=flask_app,
        use_reloader=True)
