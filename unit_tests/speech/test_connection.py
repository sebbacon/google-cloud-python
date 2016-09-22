# Copyright 2016 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest


class TestConnection(unittest.TestCase):

    def _getTargetClass(self):
        from google.cloud.speech.connection import Connection
        return Connection

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_build_api_url(self):
        conn = self._makeOne()
        uri = '/'.join([
            conn.API_BASE_URL,
            conn.API_VERSION,
            'speech',
        ])
        method = 'syncrecognize'
        uri += ':' + method
        self.assertEqual(conn.build_api_url(method), uri)
