"""DRF serializers for the CloudMan Create API endpoints."""

from rest_framework import serializers
from cloudlaunch import serializers as cl_serializers
from .drf_helpers import CustomHyperlinkedIdentityField
from cmcluster.api import CloudManAPI


class CMClusterSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField()
    cluster_type = serializers.CharField()
    connection_settings = cl_serializers.StoredJSONField()
    nodes = CustomHyperlinkedIdentityField(view_name='node-list',
                                           lookup_field='cluster_id',
                                           lookup_url_kwarg='cluster_pk')

    def create(self, valid_data):
        return CloudManAPI().clusters.create(
            valid_data.get('name'), valid_data.get('cluster_type'),
            valid_data.get('connection_settings'))


class CMClusterNodeSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField()
    cluster = CMClusterSerializer(read_only=True)
    instance_type = serializers.CharField(write_only=True)
    deployment = cl_serializers.DeploymentSerializer(read_only=True)

    def create(self, valid_data):
        cluster_id = self.context['view'].kwargs.get("cluster_pk")
        cluster = CloudManAPI().clusters.get(cluster_id)
        return cluster.nodes.create(
            valid_data.get('name'), valid_data.get('instance_type'))