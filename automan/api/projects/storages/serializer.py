import json
from datetime import datetime
from django.db.models import Q
from django.core.exceptions import FieldError
from rest_framework import serializers
from .models import Storage
from api.settings import PER_PAGE, SORT_KEY, MOUNT_PATH, VOLUME_NAME, CLAIM_NAME
from api.common import validation_check


class StorageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Storage
        # fields = '__all__'
        fields = ('storage_type', 'storage_config', 'project')

    def create(self, validated_data):
        # FIXME storage_type validation
        storage_config = validated_data.pop('storage_config')
        if validated_data.get('storage_type') == 'LOCAL_NFS':
            if MOUNT_PATH:
                storage_config = self.__local_storage_config(validated_data.get('project').id)
            else:
                raise Exception  # FIXME
        elif validated_data.get('storage_type') == 'AWS_S3':
            storage_config = self.__aws_s3_config(
                storage_config, validated_data.get('project').id)
        else:
            raise NotImplementedError  # FIXME

        new_storage = Storage(storage_config=storage_config, **validated_data)
        new_storage.save()
        return new_storage

    @classmethod
    def list(
            cls, project_id, sort_key=SORT_KEY, is_reverse=False,
            per_page=PER_PAGE, page=1, search_keyword=""):
        validation_check(per_page, page)
        begin = per_page * (page - 1)
        try:
            if is_reverse is False:
                storages = Storage.objects.order_by(sort_key).filter(
                    Q(project_id=project_id),
                    Q(storage_type__contains=search_keyword) | Q(storage_config__contains=search_keyword)
                )[begin:begin + per_page]
            else:
                storages = Storage.objects.order_by(sort_key).reverse().filter(
                    Q(project_id=project_id),
                    Q(storage_type__contains=search_keyword) | Q(storage_config__contains=search_keyword)
                )[begin:begin + per_page]
        except FieldError:
            storages = Storage.objects.order_by("id").filter(
                Q(project_id=project_id),
                Q(storage_type__contains=search_keyword) | Q(storage_config__contains=search_keyword)
            )[begin:begin + per_page]
        records = []
        for storage in storages:
            record = {}
            record['id'] = storage.id
            record['storage_type'] = storage.storage_type
            record['updated_at'] = str(storage.updated_at)
            record['storage_config'] = storage.storage_config
            records.append(record)
        contents = {}
        contents['count'] = cls.storage_total_count(project_id)
        contents['records'] = records
        return contents

    @classmethod
    def storage_total_count(cls, project_id):
        storages = Storage.objects.filter(project_id=project_id)
        return storages.count()

    def get_storage(self, project_id, storage_id):
        storage = Storage.objects.filter(id=storage_id, project_id=project_id).first()
        record = {
            'id': storage.id,
            'storage_type': storage.storage_type,
            'storage_config': json.loads(storage.storage_config),
        }
        return record

    def get_storages(self, project_id):
        storages = Storage.objects.filter(project_id=project_id)
        records = []
        for storage in storages:
            record = {
                'id': storage.id,
                'storage_type': storage.storage_type,
                'storage_config': json.loads(storage.storage_config),
            }
            print(record)
            records.append(record)
        return records

    def __local_storage_config(self, project_id):
        return json.dumps({
            'mount_path': MOUNT_PATH,
            'volume_name': VOLUME_NAME,
            'claim_name': CLAIM_NAME,
            'base_dir': '/' + str(project_id),
        })

    def __aws_s3_config(self, storage_config_json, project_id):
        config = json.loads(storage_config_json)
        return json.dumps({
            'bucket': config['bucket'],
            'base_dir': '/' + str(project_id),
        })
