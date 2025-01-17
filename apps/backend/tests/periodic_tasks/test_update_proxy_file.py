# -*- coding: utf-8 -*-
"""
TencentBlueKing is pleased to support the open source community by making 蓝鲸智云-节点管理(BlueKing-BK-NODEMAN) available.
Copyright (C) 2017-2022 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at https://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
"""

import json
import os
import random
import shutil
from typing import Dict

import mock
from django.conf import settings
from django.core.management import call_command
from django.test import override_settings
from mock import patch

from apps.adapters.api import gse
from apps.core.files import constants as core_const
from apps.mock_data import api_mkd, utils
from apps.mock_data.api_mkd.gse.utils import GseApiMockClient
from apps.node_man import constants
from apps.node_man.models import AccessPoint, InstallChannel
from apps.node_man.tests.utils import create_ap, create_cloud_area, create_host
from apps.utils import files
from apps.utils.files import md5sum
from apps.utils.unittest.testcase import CustomBaseTestCase
from env.constants import GseVersion


class JobDemandMock:
    def __init__(self, poll_task_result_return=None):
        self.poll_task_result = mock.MagicMock(return_value=poll_task_result_return)


class StorageMock:
    def __init__(self, get_file_md5_return=None, fast_transfer_file_return=None):
        self.get_file_md5 = mock.MagicMock(return_value=get_file_md5_return)
        self.fast_transfer_file = mock.MagicMock(return_value=fast_transfer_file_return)


FAST_EXECUTE_SCRIPT = {
    "job_instance_name": "API Quick execution script1521100521303",
    "job_instance_id": 10000,
    "step_instance_id": 10001,
}

CHANNEL_TEST_IP = "127.0.0.2"

GET_AGENT_STATUS = {
    f"{constants.DEFAULT_CLOUD}:{utils.DEFAULT_IP}": {
        "ip": utils.DEFAULT_IP,
        "bk_cloud_id": constants.DEFAULT_CLOUD,
        "bk_agent_alive": constants.BkAgentStatus.ALIVE.value,
    },
    f"{constants.DEFAULT_CLOUD}:{CHANNEL_TEST_IP}": {
        "ip": CHANNEL_TEST_IP,
        "bk_cloud_id": constants.DEFAULT_CLOUD,
        "bk_agent_alive": constants.BkAgentStatus.ALIVE.value,
    },
}

POLL_RESULT = {
    "is_finished": True,
    "task_result": {
        "success": [
            {"ip": utils.DEFAULT_IP, "bk_cloud_id": constants.DEFAULT_CLOUD, "log_content": "", "bk_host_id": 1}
        ],
        "pending": [],
        "failed": [],
    },
}

OVERWRITE_OBJ__KV_MAP = {
    "settings": {
        "DOWNLOAD_PATH": "/tmp",
        "STORAGE_TYPE": "FILE_SYSTEM",
        "BKREPO_BUCKET": "bucket",
        "BKREPO_PROJECT": "project",
    }
}


class TestUpdateProxyFile(CustomBaseTestCase):
    download_files = [file_name for file_set in constants.FILES_TO_PUSH_TO_PROXY for file_name in file_set["files"]]

    @classmethod
    def init_proxy_host(cls, alive_number: int = 1, unknown_number: int = 0, ip=None, bk_cloud_id=None):
        if unknown_number:
            create_host(
                number=unknown_number,
                node_type=constants.NodeType.PROXY,
                proc_type=constants.ProcStateType.UNKNOWN,
                ip=ip,
                bk_cloud_id=bk_cloud_id,
                bk_host_id=random.randint(1e2, 1e5),
            )
        if alive_number:
            create_host(
                number=alive_number,
                node_type=constants.NodeType.PROXY,
                ip=ip,
                bk_cloud_id=bk_cloud_id,
                bk_host_id=random.randint(1e2, 1e5),
            )

    @classmethod
    def init_channel_db(cls):
        InstallChannel.objects.create(
            bk_cloud_id=constants.DEFAULT_CLOUD,
            jump_servers=[utils.DEFAULT_IP],
            upstream_servers={
                "taskserver": [CHANNEL_TEST_IP],
                "btfileserver": [CHANNEL_TEST_IP],
                "dataserver": [CHANNEL_TEST_IP],
                "channel_proxy_address": f"http://{CHANNEL_TEST_IP}:{settings.BK_NODEMAN_NGINX_PROXY_PASS_PORT}",
                "agent_download_proxy": False,
            },
        )
        create_host(
            number=1,
            node_type=constants.NodeType.PAGENT,
            ip=CHANNEL_TEST_IP,
            bk_cloud_id=constants.DEFAULT_CLOUD,
            bk_host_id=random.randint(1e2, 1e5),
        )

    @classmethod
    def init_ap_db(cls, number=None, nginx_path=None):
        if not number:
            create_ap(1)
        if not nginx_path:
            AccessPoint.objects.all().update(nginx_path="")
        if nginx_path:
            create_ap(number)
            AccessPoint.objects.exclude(id=1).update(nginx_path=nginx_path)

    @classmethod
    def setUpTestData(cls):
        cls.JOB_MOCK_CLIENT = api_mkd.job.utils.JobApiMockClient(
            utils.MockReturn(return_type=utils.MockReturnType.RETURN_VALUE.value, return_obj=FAST_EXECUTE_SCRIPT)
        )

        cls.JOB_DEMAND_MOCK_CLIENT = JobDemandMock(poll_task_result_return=POLL_RESULT)

    def setUp(self) -> None:
        create_cloud_area(number=5, creator="admin")
        patch("apps.node_man.periodic_tasks.update_proxy_file.JobApi", self.JOB_MOCK_CLIENT).start()

    @patch(
        "apps.node_man.periodic_tasks.update_proxy_file.GseApiHelper",
        gse.get_gse_api_helper(GseVersion.V2.value)(GseVersion.V2.value, GseApiMockClient()),
    )
    def test_file_system_update(self):
        # 不存在proxy
        self.assertIsNone(call_command("update_proxy_file"))

        # 没有存活的proxy
        GET_AGENT_STATUS[f"{constants.DEFAULT_CLOUD}:{utils.DEFAULT_IP}"][
            "bk_agent_alive"
        ] = constants.BkAgentStatus.NOT_ALIVE.value
        self.init_proxy_host(alive_number=0, unknown_number=1)
        self.assertIsNone(call_command("update_proxy_file"))

        OVERWRITE_OBJ__KV_MAP["settings"]["DOWNLOAD_PATH"] = files.mk_and_return_tmpdir()
        with self.settings(
            DOWNLOAD_PATH=OVERWRITE_OBJ__KV_MAP["settings"]["DOWNLOAD_PATH"],
            GSE_VERSION=GseVersion.V2.value,
            BKAPP_ENABLE_DHCP=True,
            STORAGE_TYPE=core_const.StorageType.FILE_SYSTEM.value,
        ):
            local_files_md5_map: Dict[str, str] = {}
            GET_AGENT_STATUS[f"{constants.DEFAULT_CLOUD}:{utils.DEFAULT_IP}"][
                "bk_agent_alive"
            ] = constants.BkAgentStatus.ALIVE.value

            # 创建接入点
            self.init_ap_db()

            # 本地服务器没有相关文件
            self.init_proxy_host(alive_number=1, ip=utils.DEFAULT_IP, bk_cloud_id=constants.DEFAULT_CLOUD)
            self.init_channel_db()
            self.assertRaises(FileExistsError, call_command("update_proxy_file"))

            mock_source_file = self.download_files[random.randint(1, 5)]
            mock_compare_file = self.download_files[random.randint(6, 10)]
            size = random.randint(99, 2000)
            for mock_file in [mock_source_file, mock_compare_file]:
                with open(os.path.join(OVERWRITE_OBJ__KV_MAP["settings"]["DOWNLOAD_PATH"], mock_file), "wb") as e:
                    e.write(os.urandom(size))
            source_file_md5 = md5sum(os.path.join(settings.DOWNLOAD_PATH, mock_source_file))
            compare_file_md5 = md5sum(os.path.join(settings.DOWNLOAD_PATH, mock_compare_file))
            for file in self.download_files:
                local_files_md5_map.update({file: source_file_md5})
            storage_mock_client = StorageMock(get_file_md5_return=source_file_md5, fast_transfer_file_return=10001)
            patch(
                "apps.node_man.periodic_tasks.update_proxy_file.get_storage", mock.MagicMock(storage_mock_client)
            ).start()

            # 本地文件不存在差异
            for job_result in POLL_RESULT["task_result"]["success"]:
                md5_log = json.dumps(local_files_md5_map)
                job_result["log_content"] = f"test error lines\n{md5_log}\ntest error lines\n"
            patch("apps.node_man.periodic_tasks.update_proxy_file.JobDemand", self.JOB_DEMAND_MOCK_CLIENT).start()
            self.assertIsNone(call_command("update_proxy_file"))

            # 存在差异 同步文件
            for file in self.download_files:
                local_files_md5_map.update({file: compare_file_md5})
            storage_mock_client = StorageMock(get_file_md5_return=compare_file_md5, fast_transfer_file_return=10001)
            patch(
                "apps.node_man.periodic_tasks.update_proxy_file.get_storage", mock.MagicMock(storage_mock_client)
            ).start()
            self.init_ap_db(number=3, nginx_path="/data/bkee/public/bknodeman/download/test")
            self.assertIsNone(call_command("update_proxy_file"))
            shutil.rmtree(settings.DOWNLOAD_PATH)

    @override_settings(GSE_VERSION=GseVersion.V1.value)
    @patch(
        "apps.node_man.periodic_tasks.update_proxy_file.GseApiHelper",
        gse.get_gse_api_helper(GseVersion.V1.value)(GseVersion.V1.value, GseApiMockClient()),
    )
    def test_blueking_artifactory_update(self):
        with self.settings(
            DOWNLOAD_PATH=OVERWRITE_OBJ__KV_MAP["settings"]["DOWNLOAD_PATH"],
            STORAGE_TYPE=core_const.StorageType.BLUEKING_ARTIFACTORY.value,
            BKREPO_PROJECT=OVERWRITE_OBJ__KV_MAP["settings"]["BKREPO_PROJECT"],
            BKREPO_BUCKET=OVERWRITE_OBJ__KV_MAP["settings"]["BKREPO_BUCKET"],
        ):
            self.assertIsNone(call_command("update_proxy_file"))
