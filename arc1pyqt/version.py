import os.path
import requests
import semver


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
        url = "http://files.arc-instruments.co.uk/release/version.txt"
        response = requests.get(url, stream=True, timeout=2)

        if response.status_code >= 400:
            raise Exception("Invalid response from server")

        return str(response.text.split("\n")[1])

    def update_available(self):
        return vercmp(self.local, self.remote) > 0
