import sys
import os.path
import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout
import semver
import json
from json.decoder import JSONDecodeError


def vercmp(local, remote):
    return semver.compare(remote, local)


class VersionInfo:

    @property
    def local(self):
        thisdir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(thisdir, "version.txt"), "r") as f:
            return str(f.read().split("\n")[1])

    @property
    def remote(self):
        url = 'https://api.github.com/repos/arc-instruments/arc1_pyqt/releases/latest'
        response = requests.get(url, stream=True, timeout=2)

        if response.status_code >= 400:
            raise HTTPError("Invalid response from version server")

        ver = str(json.loads(response.content)['tag_name'])
        return ver

    def update_available(self):
        try:
            return vercmp(self.local, self.remote) > 0
        except HTTPError as httperr:
            print("HTTP Error received from version server:", httperr, file=sys.stderr)
            return False
        except (Timeout, ConnectionError) as cerr:
            print("Error when connecting to version server:", cerr, file=sys.stderr)
            return False
        except (JSONDecodeError, IndexError) as jserr:
            print("Could not parse version server response:", jserr, file=sys.stderr)
            return False
        except Exception as exc:
            print("Unknown exception while connecting to version server:",
                type(exc), exc, file=sys.stderr)
            return False
