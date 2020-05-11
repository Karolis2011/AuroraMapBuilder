from flask import Flask, send_from_directory
app = Flask(__name__)
import os
import subprocess
import glob
import hmac
import hashlib
import threading

import git
from git import Repo
import wget

import urllib.request

build_locks = {}

def get_dmmtools():
    if os.name == 'nt':
        if not os.path.isfile("dmm-tools.exe"):
            wget.download("https://github.com/SpaceManiac/SpacemanDMM/releases/download/suite-1.4/dmm-tools.exe", "dmm-tools.exe")
        return "dmm-tools.exe"
    else:
        if not os.path.isfile("dmm-tools"):
            wget.download("https://github.com/SpaceManiac/SpacemanDMM/releases/download/suite-1.4/dmm-tools", "dmm-tools")
        return "dmm-tools"

def verify_hmac_hash(data, signature):
    secret = os.getenv('GITHUB_SECRET')
    if not secret:
        return True
    github_secret = bytes(secret, 'UTF-8')
    mac = hmac.new(github_secret, msg=data, digestmod=hashlib.sha1)
    return hmac.compare_digest('sha1=' + mac.hexdigest(), signature)

@app.route('/<string:secret>')
def ping(secret):
    trueSecret = os.getenv('GITHUB_SECRET')
    if trueSecret and secret != trueSecret:
        return 'Invalid SECRET'
    path = os.path.join(os.getcwd(), "__cache", "Aurorastation/Aurora.3")
    th = threading.Thread(target=handle_generation, args=(path, "https://github.com/Aurorastation/Aurora.3.git"))
    th.start()
    return 'OK'

@app.route("/payload", methods=['POST'])
def github_payload():
    signature = request.headers.get('X-Hub-Signature')
    data = request.data
    if verify_hmac_hash(data, signature):
        if request.headers.get('X-GitHub-Event') == "push":
            payload = request.get_json()
            path = os.path.join(os.getcwd(), "__cache", payload["full_name"])
            th = threading.Thread(target=handle_generation, args=(path,payload["clone_url"]))
            th.start()
            return 'OK'

def handle_generation(path, remote, ref = None):
    if not path in build_locks:
        build_locks[path] = threading.Lock()
    with build_locks[path]:
        print("Started build task for {}.".format(remote))
        repo = None
        if not os.path.isdir(path):
            repo = Repo.clone_from(remote, path)
        else:
            repo = Repo(path)
            for remote in repo.remotes:
                remote.fetch()
            if ref:
                repo.git.checkout(ref)
            else:
                repo.remotes.origin.pull()

        maps = glob.glob(os.path.join(repo.working_tree_dir, "maps", "**", "*.dmm"))
        args = [os.path.abspath(get_dmmtools()), "minimap", "--disable", "icon-smoothing,fancy-layers"]
        for m in maps:
            a = []
            a.extend(args)
            a.append(m)
            subprocess.run(a, cwd=repo.working_tree_dir)

@app.route('/mapfile/<string:a>/<string:b>/<string:c>')
def send_mapfile(a, b, c):
    path = os.path.join(os.getcwd(), "__cache", a, b, "data", "minimaps")
    return send_from_directory(path, c)

if __name__ == "__main__":
    print("Current secret is {}, use it while setting up webhook.".format(os.getenv('GITHUB_SECRET')))
    app.run()
    # path = os.path.join(os.getcwd(), "__cache", "Aurorastation/Aurora.3")
    # handle_generation(path, "https://github.com/Aurorastation/Aurora.3.git", "")