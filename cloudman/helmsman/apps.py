import subprocess
import os
import logging as log
from django.apps import AppConfig
from .helm.client import HelmClient


class HelmsmanConfig(AppConfig):
    name = 'helmsman'

    def ready(self):
        try:
            if os.environ.get("HELMSMAN_AUTO_DEPLOY"):
                galaxy_repo = {"galaxyproject":
                                   {"url":
                                       "https://raw.githubusercontent.com/"
                                       "CloudVE/helm-charts/master/",
                                    "name": "galaxy-stable"}}
                pulsar_repo = {"pulsar":
                                   {"url":
                                       "https://raw.githubusercontent.com/"
                                       "CloudVE/helm-charts/master/",
                                    "name": "pulsar-stable"}}
                pulsar_token = os.environ.pop("PULSAR_TOKEN")
                repos = {}
                if pulsar_token:
                    repos.update(pulsar_repo)
                else:
                    repos.update(galaxy_repo)
                self.setup_helmsman(repos)
        except Exception as e:
            log.exception("HelmsManConfig.ready()->setup_helmsman(): An error"
                          " occurred while setting up HelmsMan!!: ")
            print("HelmsManConfig.ready()->setup_helmsman(): An error occurred"
                  " while setting up HelmsMan!!: ", e)

    def setup_helmsman(self, repos):
        client = HelmClient()
        print("Initializing kube roles for tiller...")
        # FIXME: Check whether tiller role exists instead of ignoring exception
        try:
            cmd = (
                "kubectl create serviceaccount --namespace kube-system tiller"
                " && kubectl create clusterrolebinding tiller-cluster-rule"
                " --clusterrole=cluster-admin"
                " --serviceaccount=kube-system:tiller")
            subprocess.check_output(cmd, shell=True)
        except Exception:
            log.exception("Could not create tiller role bindings")
        print("Initializing tiller...")
        client.helm_init(service_account="tiller", wait=True)
        print("Adding default repos...")
        for key in repos.keys():
            print("Adding default repo: " + key)
            info = repos.get(key)
            client.repositories.create(
                key,
                info.get("url"))
            self.add_default_charts(client, key, info.get('name'))

    def add_default_charts(self, client, repo_name, chart_name):
        print("Installing default charts: ...")
        self.install_if_not_exist(client, repo_name, chart_name)

    def install_if_not_exist(self, client, repo_name, chart_name):
        existing_release = [r for r in client.releases.list()
                            if chart_name in r.get('CHART')]
        if existing_release:
            print(f"Chart {repo_name}/{chart_name} already installed.")
        else:
            client.repositories.update()
            print(f"Installing chart {repo_name}/{chart_name} into namespace"
                  " default")
            client.releases.create(f"{repo_name}/{chart_name}", "default")
