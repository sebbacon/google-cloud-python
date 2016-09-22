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


try:
    # pylint: disable=unused-import
    import google.cloud.pubsub._gax
    # pylint: enable=unused-import
except ImportError:  # pragma: NO COVER
    _HAVE_GAX = False
else:
    _HAVE_GAX = True

from unit_tests._testing import _GAXBaseAPI


class _Base(object):
    PROJECT = 'PROJECT'
    PROJECT_PATH = 'projects/%s' % (PROJECT,)
    LIST_TOPICS_PATH = '%s/topics' % (PROJECT_PATH,)
    TOPIC_NAME = 'topic_name'
    TOPIC_PATH = 'projects/%s/topics/%s' % (PROJECT, TOPIC_NAME)
    LIST_TOPIC_SUBSCRIPTIONS_PATH = '%s/subscriptions' % (TOPIC_PATH,)
    SUB_NAME = 'sub_name'
    SUB_PATH = '%s/subscriptions/%s' % (TOPIC_PATH, SUB_NAME)

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)


@unittest.skipUnless(_HAVE_GAX, 'No gax-python')
class Test_PublisherAPI(_Base, unittest.TestCase):

    def _getTargetClass(self):
        from google.cloud.pubsub._gax import _PublisherAPI
        return _PublisherAPI

    def test_ctor(self):
        gax_api = _GAXPublisherAPI()
        api = self._makeOne(gax_api)
        self.assertIs(api._gax_api, gax_api)

    def test_list_topics_no_paging(self):
        from google.gax import INITIAL_PAGE
        from unit_tests._testing import _GAXPageIterator
        TOKEN = 'TOKEN'
        response = _GAXPageIterator([_TopicPB(self.TOPIC_PATH)], TOKEN)
        gax_api = _GAXPublisherAPI(_list_topics_response=response)
        api = self._makeOne(gax_api)

        topics, next_token = api.list_topics(self.PROJECT)

        self.assertEqual(len(topics), 1)
        topic = topics[0]
        self.assertIsInstance(topic, dict)
        self.assertEqual(topic['name'], self.TOPIC_PATH)
        self.assertEqual(next_token, TOKEN)

        name, page_size, options = gax_api._list_topics_called_with
        self.assertEqual(name, self.PROJECT_PATH)
        self.assertEqual(page_size, 0)
        self.assertIs(options.page_token, INITIAL_PAGE)

    def test_list_topics_with_paging(self):
        from unit_tests._testing import _GAXPageIterator
        SIZE = 23
        TOKEN = 'TOKEN'
        NEW_TOKEN = 'NEW_TOKEN'
        response = _GAXPageIterator(
            [_TopicPB(self.TOPIC_PATH)], NEW_TOKEN)
        gax_api = _GAXPublisherAPI(_list_topics_response=response)
        api = self._makeOne(gax_api)

        topics, next_token = api.list_topics(
            self.PROJECT, page_size=SIZE, page_token=TOKEN)

        self.assertEqual(len(topics), 1)
        topic = topics[0]
        self.assertIsInstance(topic, dict)
        self.assertEqual(topic['name'], self.TOPIC_PATH)
        self.assertEqual(next_token, NEW_TOKEN)

        name, page_size, options = gax_api._list_topics_called_with
        self.assertEqual(name, self.PROJECT_PATH)
        self.assertEqual(page_size, SIZE)
        self.assertEqual(options.page_token, TOKEN)

    def test_topic_create(self):
        topic_pb = _TopicPB(self.TOPIC_PATH)
        gax_api = _GAXPublisherAPI(_create_topic_response=topic_pb)
        api = self._makeOne(gax_api)

        resource = api.topic_create(self.TOPIC_PATH)

        self.assertEqual(resource, {'name': self.TOPIC_PATH})
        topic_path, options = gax_api._create_topic_called_with
        self.assertEqual(topic_path, self.TOPIC_PATH)
        self.assertIsNone(options)

    def test_topic_create_already_exists(self):
        from google.cloud.exceptions import Conflict
        gax_api = _GAXPublisherAPI(_create_topic_conflict=True)
        api = self._makeOne(gax_api)

        with self.assertRaises(Conflict):
            api.topic_create(self.TOPIC_PATH)

        topic_path, options = gax_api._create_topic_called_with
        self.assertEqual(topic_path, self.TOPIC_PATH)
        self.assertIsNone(options)

    def test_topic_create_error(self):
        from google.cloud.exceptions import GrpcRendezvous

        gax_api = _GAXPublisherAPI(_random_gax_error=True)
        api = self._makeOne(gax_api)

        with self.assertRaises(GrpcRendezvous):
            api.topic_create(self.TOPIC_PATH)

        topic_path, options = gax_api._create_topic_called_with
        self.assertEqual(topic_path, self.TOPIC_PATH)
        self.assertIsNone(options)

    def test_topic_get_hit(self):
        topic_pb = _TopicPB(self.TOPIC_PATH)
        gax_api = _GAXPublisherAPI(_get_topic_response=topic_pb)
        api = self._makeOne(gax_api)

        resource = api.topic_get(self.TOPIC_PATH)

        self.assertEqual(resource, {'name': self.TOPIC_PATH})
        topic_path, options = gax_api._get_topic_called_with
        self.assertEqual(topic_path, self.TOPIC_PATH)
        self.assertIsNone(options)

    def test_topic_get_miss(self):
        from google.cloud.exceptions import NotFound
        gax_api = _GAXPublisherAPI()
        api = self._makeOne(gax_api)

        with self.assertRaises(NotFound):
            api.topic_get(self.TOPIC_PATH)

        topic_path, options = gax_api._get_topic_called_with
        self.assertEqual(topic_path, self.TOPIC_PATH)
        self.assertIsNone(options)

    def test_topic_get_error(self):
        from google.cloud.exceptions import GrpcRendezvous

        gax_api = _GAXPublisherAPI(_random_gax_error=True)
        api = self._makeOne(gax_api)

        with self.assertRaises(GrpcRendezvous):
            api.topic_get(self.TOPIC_PATH)

        topic_path, options = gax_api._get_topic_called_with
        self.assertEqual(topic_path, self.TOPIC_PATH)
        self.assertIsNone(options)

    def test_topic_delete_hit(self):
        gax_api = _GAXPublisherAPI(_delete_topic_ok=True)
        api = self._makeOne(gax_api)

        api.topic_delete(self.TOPIC_PATH)

        topic_path, options = gax_api._delete_topic_called_with
        self.assertEqual(topic_path, self.TOPIC_PATH)
        self.assertIsNone(options)

    def test_topic_delete_miss(self):
        from google.cloud.exceptions import NotFound
        gax_api = _GAXPublisherAPI(_delete_topic_ok=False)
        api = self._makeOne(gax_api)

        with self.assertRaises(NotFound):
            api.topic_delete(self.TOPIC_PATH)

        topic_path, options = gax_api._delete_topic_called_with
        self.assertEqual(topic_path, self.TOPIC_PATH)
        self.assertIsNone(options)

    def test_topic_delete_error(self):
        from google.cloud.exceptions import GrpcRendezvous

        gax_api = _GAXPublisherAPI(_random_gax_error=True)
        api = self._makeOne(gax_api)

        with self.assertRaises(GrpcRendezvous):
            api.topic_delete(self.TOPIC_PATH)

        topic_path, options = gax_api._delete_topic_called_with
        self.assertEqual(topic_path, self.TOPIC_PATH)
        self.assertIsNone(options)

    def test_topic_publish_hit(self):
        import base64
        PAYLOAD = b'This is the message text'
        B64 = base64.b64encode(PAYLOAD).decode('ascii')
        MSGID = 'DEADBEEF'
        MESSAGE = {'data': B64, 'attributes': {}}
        response = _PublishResponsePB([MSGID])
        gax_api = _GAXPublisherAPI(_publish_response=response)
        api = self._makeOne(gax_api)

        resource = api.topic_publish(self.TOPIC_PATH, [MESSAGE])

        self.assertEqual(resource, [MSGID])
        topic_path, message_pbs, options = gax_api._publish_called_with
        self.assertEqual(topic_path, self.TOPIC_PATH)
        message_pb, = message_pbs
        self.assertEqual(message_pb.data.decode('ascii'), B64)
        self.assertEqual(message_pb.attributes, {})
        self.assertEqual(options.is_bundling, False)

    def test_topic_publish_miss_w_attrs_w_bytes_payload(self):
        import base64
        from google.cloud.exceptions import NotFound
        PAYLOAD = b'This is the message text'
        B64 = base64.b64encode(PAYLOAD)
        MESSAGE = {'data': B64, 'attributes': {'foo': 'bar'}}
        gax_api = _GAXPublisherAPI()
        api = self._makeOne(gax_api)

        with self.assertRaises(NotFound):
            api.topic_publish(self.TOPIC_PATH, [MESSAGE])

        topic_path, message_pbs, options = gax_api._publish_called_with
        self.assertEqual(topic_path, self.TOPIC_PATH)
        message_pb, = message_pbs
        self.assertEqual(message_pb.data, B64)
        self.assertEqual(message_pb.attributes, {'foo': 'bar'})
        self.assertEqual(options.is_bundling, False)

    def test_topic_publish_error(self):
        import base64
        from google.cloud.exceptions import GrpcRendezvous

        PAYLOAD = b'This is the message text'
        B64 = base64.b64encode(PAYLOAD).decode('ascii')
        MESSAGE = {'data': B64, 'attributes': {}}
        gax_api = _GAXPublisherAPI(_random_gax_error=True)
        api = self._makeOne(gax_api)

        with self.assertRaises(GrpcRendezvous):
            api.topic_publish(self.TOPIC_PATH, [MESSAGE])

        topic_path, message_pbs, options = gax_api._publish_called_with
        self.assertEqual(topic_path, self.TOPIC_PATH)
        message_pb, = message_pbs
        self.assertEqual(message_pb.data.decode('ascii'), B64)
        self.assertEqual(message_pb.attributes, {})
        self.assertEqual(options.is_bundling, False)

    def test_topic_list_subscriptions_no_paging(self):
        from google.gax import INITIAL_PAGE
        from unit_tests._testing import _GAXPageIterator
        response = _GAXPageIterator([
            {'name': self.SUB_PATH, 'topic': self.TOPIC_PATH}], None)
        gax_api = _GAXPublisherAPI(_list_topic_subscriptions_response=response)
        api = self._makeOne(gax_api)

        subscriptions, next_token = api.topic_list_subscriptions(
            self.TOPIC_PATH)

        self.assertEqual(len(subscriptions), 1)
        subscription = subscriptions[0]
        self.assertIsInstance(subscription, dict)
        self.assertEqual(subscription['name'], self.SUB_PATH)
        self.assertEqual(subscription['topic'], self.TOPIC_PATH)
        self.assertIsNone(next_token)

        topic_path, page_size, options = (
            gax_api._list_topic_subscriptions_called_with)
        self.assertEqual(topic_path, self.TOPIC_PATH)
        self.assertEqual(page_size, 0)
        self.assertIs(options.page_token, INITIAL_PAGE)

    def test_topic_list_subscriptions_with_paging(self):
        from unit_tests._testing import _GAXPageIterator
        SIZE = 23
        TOKEN = 'TOKEN'
        NEW_TOKEN = 'NEW_TOKEN'
        response = _GAXPageIterator([
            {'name': self.SUB_PATH, 'topic': self.TOPIC_PATH}], NEW_TOKEN)
        gax_api = _GAXPublisherAPI(_list_topic_subscriptions_response=response)
        api = self._makeOne(gax_api)

        subscriptions, next_token = api.topic_list_subscriptions(
            self.TOPIC_PATH, page_size=SIZE, page_token=TOKEN)

        self.assertEqual(len(subscriptions), 1)
        subscription = subscriptions[0]
        self.assertIsInstance(subscription, dict)
        self.assertEqual(subscription['name'], self.SUB_PATH)
        self.assertEqual(subscription['topic'], self.TOPIC_PATH)
        self.assertEqual(next_token, NEW_TOKEN)

        name, page_size, options = (
            gax_api._list_topic_subscriptions_called_with)
        self.assertEqual(name, self.TOPIC_PATH)
        self.assertEqual(page_size, SIZE)
        self.assertEqual(options.page_token, TOKEN)

    def test_topic_list_subscriptions_miss(self):
        from google.gax import INITIAL_PAGE
        from google.cloud.exceptions import NotFound
        gax_api = _GAXPublisherAPI()
        api = self._makeOne(gax_api)

        with self.assertRaises(NotFound):
            api.topic_list_subscriptions(self.TOPIC_PATH)

        topic_path, page_size, options = (
            gax_api._list_topic_subscriptions_called_with)
        self.assertEqual(topic_path, self.TOPIC_PATH)
        self.assertEqual(page_size, 0)
        self.assertIs(options.page_token, INITIAL_PAGE)

    def test_topic_list_subscriptions_error(self):
        from google.gax import INITIAL_PAGE
        from google.cloud.exceptions import GrpcRendezvous

        gax_api = _GAXPublisherAPI(_random_gax_error=True)
        api = self._makeOne(gax_api)

        with self.assertRaises(GrpcRendezvous):
            api.topic_list_subscriptions(self.TOPIC_PATH)

        topic_path, page_size, options = (
            gax_api._list_topic_subscriptions_called_with)
        self.assertEqual(topic_path, self.TOPIC_PATH)
        self.assertEqual(page_size, 0)
        self.assertIs(options.page_token, INITIAL_PAGE)


@unittest.skipUnless(_HAVE_GAX, 'No gax-python')
class Test_SubscriberAPI(_Base, unittest.TestCase):

    PUSH_ENDPOINT = 'https://api.example.com/push'

    def _getTargetClass(self):
        from google.cloud.pubsub._gax import _SubscriberAPI
        return _SubscriberAPI

    def test_ctor(self):
        gax_api = _GAXSubscriberAPI()
        api = self._makeOne(gax_api)
        self.assertIs(api._gax_api, gax_api)

    def test_list_subscriptions_no_paging(self):
        from google.gax import INITIAL_PAGE
        from unit_tests._testing import _GAXPageIterator
        response = _GAXPageIterator([_SubscriptionPB(
            self.SUB_PATH, self.TOPIC_PATH, self.PUSH_ENDPOINT, 0)], None)
        gax_api = _GAXSubscriberAPI(_list_subscriptions_response=response)
        api = self._makeOne(gax_api)

        subscriptions, next_token = api.list_subscriptions(self.PROJECT)

        self.assertEqual(len(subscriptions), 1)
        subscription = subscriptions[0]
        self.assertIsInstance(subscription, dict)
        self.assertEqual(subscription['name'], self.SUB_PATH)
        self.assertEqual(subscription['topic'], self.TOPIC_PATH)
        self.assertEqual(subscription['pushConfig'],
                         {'pushEndpoint': self.PUSH_ENDPOINT})
        self.assertEqual(subscription['ackDeadlineSeconds'], 0)
        self.assertIsNone(next_token)

        name, page_size, options = gax_api._list_subscriptions_called_with
        self.assertEqual(name, self.PROJECT_PATH)
        self.assertEqual(page_size, 0)
        self.assertIs(options.page_token, INITIAL_PAGE)

    def test_list_subscriptions_with_paging(self):
        from unit_tests._testing import _GAXPageIterator
        SIZE = 23
        TOKEN = 'TOKEN'
        NEW_TOKEN = 'NEW_TOKEN'
        response = _GAXPageIterator([_SubscriptionPB(
            self.SUB_PATH, self.TOPIC_PATH, self.PUSH_ENDPOINT, 0)], NEW_TOKEN)
        gax_api = _GAXSubscriberAPI(_list_subscriptions_response=response)
        api = self._makeOne(gax_api)

        subscriptions, next_token = api.list_subscriptions(
            self.PROJECT, page_size=SIZE, page_token=TOKEN)

        self.assertEqual(len(subscriptions), 1)
        subscription = subscriptions[0]
        self.assertIsInstance(subscription, dict)
        self.assertEqual(subscription['name'], self.SUB_PATH)
        self.assertEqual(subscription['topic'], self.TOPIC_PATH)
        self.assertEqual(subscription['pushConfig'],
                         {'pushEndpoint': self.PUSH_ENDPOINT})
        self.assertEqual(subscription['ackDeadlineSeconds'], 0)
        self.assertEqual(next_token, NEW_TOKEN)

        name, page_size, options = gax_api._list_subscriptions_called_with
        self.assertEqual(name, self.PROJECT_PATH)
        self.assertEqual(page_size, 23)
        self.assertEqual(options.page_token, TOKEN)

    def test_subscription_create(self):
        sub_pb = _SubscriptionPB(self.SUB_PATH, self.TOPIC_PATH, '', 0)
        gax_api = _GAXSubscriberAPI(_create_subscription_response=sub_pb)
        api = self._makeOne(gax_api)

        resource = api.subscription_create(self.SUB_PATH, self.TOPIC_PATH)

        expected = {
            'name': self.SUB_PATH,
            'topic': self.TOPIC_PATH,
            'ackDeadlineSeconds': 0,
        }
        self.assertEqual(resource, expected)
        name, topic, push_config, ack_deadline, options = (
            gax_api._create_subscription_called_with)
        self.assertEqual(name, self.SUB_PATH)
        self.assertEqual(topic, self.TOPIC_PATH)
        self.assertIsNone(push_config)
        self.assertEqual(ack_deadline, 0)
        self.assertIsNone(options)

    def test_subscription_create_already_exists(self):
        from google.cloud.exceptions import Conflict
        DEADLINE = 600
        gax_api = _GAXSubscriberAPI(_create_subscription_conflict=True)
        api = self._makeOne(gax_api)

        with self.assertRaises(Conflict):
            api.subscription_create(
                self.SUB_PATH, self.TOPIC_PATH, DEADLINE, self.PUSH_ENDPOINT)

        name, topic, push_config, ack_deadline, options = (
            gax_api._create_subscription_called_with)
        self.assertEqual(name, self.SUB_PATH)
        self.assertEqual(topic, self.TOPIC_PATH)
        self.assertEqual(push_config.push_endpoint, self.PUSH_ENDPOINT)
        self.assertEqual(ack_deadline, DEADLINE)
        self.assertIsNone(options)

    def test_subscription_create_error(self):
        from google.cloud.exceptions import GrpcRendezvous

        gax_api = _GAXSubscriberAPI(_random_gax_error=True)
        api = self._makeOne(gax_api)

        with self.assertRaises(GrpcRendezvous):
            api.subscription_create(self.SUB_PATH, self.TOPIC_PATH)

        name, topic, push_config, ack_deadline, options = (
            gax_api._create_subscription_called_with)
        self.assertEqual(name, self.SUB_PATH)
        self.assertEqual(topic, self.TOPIC_PATH)
        self.assertIsNone(push_config)
        self.assertEqual(ack_deadline, 0)
        self.assertIsNone(options)

    def test_subscription_get_hit(self):
        sub_pb = _SubscriptionPB(
            self.SUB_PATH, self.TOPIC_PATH, self.PUSH_ENDPOINT, 0)
        gax_api = _GAXSubscriberAPI(_get_subscription_response=sub_pb)
        api = self._makeOne(gax_api)

        resource = api.subscription_get(self.SUB_PATH)

        expected = {
            'name': self.SUB_PATH,
            'topic': self.TOPIC_PATH,
            'ackDeadlineSeconds': 0,
            'pushConfig': {
                'pushEndpoint': self.PUSH_ENDPOINT,
            },
        }
        self.assertEqual(resource, expected)
        sub_path, options = gax_api._get_subscription_called_with
        self.assertEqual(sub_path, self.SUB_PATH)
        self.assertIsNone(options)

    def test_subscription_get_miss(self):
        from google.cloud.exceptions import NotFound
        gax_api = _GAXSubscriberAPI()
        api = self._makeOne(gax_api)

        with self.assertRaises(NotFound):
            api.subscription_get(self.SUB_PATH)

        sub_path, options = gax_api._get_subscription_called_with
        self.assertEqual(sub_path, self.SUB_PATH)
        self.assertIsNone(options)

    def test_subscription_get_error(self):
        from google.cloud.exceptions import GrpcRendezvous

        gax_api = _GAXSubscriberAPI(_random_gax_error=True)
        api = self._makeOne(gax_api)

        with self.assertRaises(GrpcRendezvous):
            api.subscription_get(self.SUB_PATH)

        sub_path, options = gax_api._get_subscription_called_with
        self.assertEqual(sub_path, self.SUB_PATH)
        self.assertIsNone(options)

    def test_subscription_delete_hit(self):
        gax_api = _GAXSubscriberAPI(_delete_subscription_ok=True)
        api = self._makeOne(gax_api)

        api.subscription_delete(self.TOPIC_PATH)

        sub_path, options = gax_api._delete_subscription_called_with
        self.assertEqual(sub_path, self.TOPIC_PATH)
        self.assertIsNone(options)

    def test_subscription_delete_miss(self):
        from google.cloud.exceptions import NotFound
        gax_api = _GAXSubscriberAPI(_delete_subscription_ok=False)
        api = self._makeOne(gax_api)

        with self.assertRaises(NotFound):
            api.subscription_delete(self.TOPIC_PATH)

        sub_path, options = gax_api._delete_subscription_called_with
        self.assertEqual(sub_path, self.TOPIC_PATH)
        self.assertIsNone(options)

    def test_subscription_delete_error(self):
        from google.cloud.exceptions import GrpcRendezvous

        gax_api = _GAXSubscriberAPI(_random_gax_error=True)
        api = self._makeOne(gax_api)

        with self.assertRaises(GrpcRendezvous):
            api.subscription_delete(self.TOPIC_PATH)

        sub_path, options = gax_api._delete_subscription_called_with
        self.assertEqual(sub_path, self.TOPIC_PATH)
        self.assertIsNone(options)

    def test_subscription_modify_push_config_hit(self):
        gax_api = _GAXSubscriberAPI(_modify_push_config_ok=True)
        api = self._makeOne(gax_api)

        api.subscription_modify_push_config(self.SUB_PATH, self.PUSH_ENDPOINT)

        sub_path, config, options = gax_api._modify_push_config_called_with
        self.assertEqual(sub_path, self.SUB_PATH)
        self.assertEqual(config.push_endpoint, self.PUSH_ENDPOINT)
        self.assertIsNone(options)

    def test_subscription_modify_push_config_miss(self):
        from google.cloud.exceptions import NotFound
        gax_api = _GAXSubscriberAPI()
        api = self._makeOne(gax_api)

        with self.assertRaises(NotFound):
            api.subscription_modify_push_config(
                self.SUB_PATH, self.PUSH_ENDPOINT)

        sub_path, config, options = gax_api._modify_push_config_called_with
        self.assertEqual(sub_path, self.SUB_PATH)
        self.assertEqual(config.push_endpoint, self.PUSH_ENDPOINT)
        self.assertIsNone(options)

    def test_subscription_modify_push_config_error(self):
        from google.cloud.exceptions import GrpcRendezvous

        gax_api = _GAXSubscriberAPI(_random_gax_error=True)
        api = self._makeOne(gax_api)

        with self.assertRaises(GrpcRendezvous):
            api.subscription_modify_push_config(
                self.SUB_PATH, self.PUSH_ENDPOINT)

        sub_path, config, options = gax_api._modify_push_config_called_with
        self.assertEqual(sub_path, self.SUB_PATH)
        self.assertEqual(config.push_endpoint, self.PUSH_ENDPOINT)
        self.assertIsNone(options)

    def test_subscription_pull_explicit(self):
        import base64
        import datetime
        from google.cloud._helpers import UTC
        from google.cloud._helpers import _datetime_to_pb_timestamp
        from google.cloud._helpers import _datetime_to_rfc3339
        NOW = datetime.datetime.utcnow().replace(tzinfo=UTC)
        NOW_PB = _datetime_to_pb_timestamp(NOW)
        NOW_RFC3339 = _datetime_to_rfc3339(NOW)
        PAYLOAD = b'This is the message text'
        B64 = base64.b64encode(PAYLOAD).decode('ascii')
        ACK_ID = 'DEADBEEF'
        MSG_ID = 'BEADCAFE'
        MESSAGE = {
            'messageId': MSG_ID,
            'data': B64,
            'attributes': {'a': 'b'},
            'publishTime': NOW_RFC3339,
        }
        RECEIVED = [{'ackId': ACK_ID, 'message': MESSAGE}]
        message_pb = _PubsubMessagePB(MSG_ID, B64, {'a': 'b'}, NOW_PB)
        response_pb = _PullResponsePB([_ReceivedMessagePB(ACK_ID, message_pb)])
        gax_api = _GAXSubscriberAPI(_pull_response=response_pb)
        api = self._makeOne(gax_api)
        MAX_MESSAGES = 10

        received = api.subscription_pull(
            self.SUB_PATH, return_immediately=True, max_messages=MAX_MESSAGES)

        self.assertEqual(received, RECEIVED)
        sub_path, max_messages, return_immediately, options = (
            gax_api._pull_called_with)
        self.assertEqual(sub_path, self.SUB_PATH)
        self.assertEqual(max_messages, MAX_MESSAGES)
        self.assertTrue(return_immediately)
        self.assertIsNone(options)

    def test_subscription_pull_defaults_miss(self):
        from google.cloud.exceptions import NotFound
        gax_api = _GAXSubscriberAPI()
        api = self._makeOne(gax_api)

        with self.assertRaises(NotFound):
            api.subscription_pull(self.SUB_PATH)

        sub_path, max_messages, return_immediately, options = (
            gax_api._pull_called_with)
        self.assertEqual(sub_path, self.SUB_PATH)
        self.assertEqual(max_messages, 1)
        self.assertFalse(return_immediately)
        self.assertIsNone(options)

    def test_subscription_pull_defaults_error(self):
        from google.cloud.exceptions import GrpcRendezvous

        gax_api = _GAXSubscriberAPI(_random_gax_error=True)
        api = self._makeOne(gax_api)

        with self.assertRaises(GrpcRendezvous):
            api.subscription_pull(self.SUB_PATH)

        sub_path, max_messages, return_immediately, options = (
            gax_api._pull_called_with)
        self.assertEqual(sub_path, self.SUB_PATH)
        self.assertEqual(max_messages, 1)
        self.assertFalse(return_immediately)
        self.assertIsNone(options)

    def test_subscription_acknowledge_hit(self):
        ACK_ID1 = 'DEADBEEF'
        ACK_ID2 = 'BEADCAFE'
        gax_api = _GAXSubscriberAPI(_acknowledge_ok=True)
        api = self._makeOne(gax_api)

        api.subscription_acknowledge(self.SUB_PATH, [ACK_ID1, ACK_ID2])

        sub_path, ack_ids, options = gax_api._acknowledge_called_with
        self.assertEqual(sub_path, self.SUB_PATH)
        self.assertEqual(ack_ids, [ACK_ID1, ACK_ID2])
        self.assertIsNone(options)

    def test_subscription_acknowledge_miss(self):
        from google.cloud.exceptions import NotFound
        ACK_ID1 = 'DEADBEEF'
        ACK_ID2 = 'BEADCAFE'
        gax_api = _GAXSubscriberAPI()
        api = self._makeOne(gax_api)

        with self.assertRaises(NotFound):
            api.subscription_acknowledge(self.SUB_PATH, [ACK_ID1, ACK_ID2])

        sub_path, ack_ids, options = gax_api._acknowledge_called_with
        self.assertEqual(sub_path, self.SUB_PATH)
        self.assertEqual(ack_ids, [ACK_ID1, ACK_ID2])
        self.assertIsNone(options)

    def test_subscription_acknowledge_error(self):
        from google.cloud.exceptions import GrpcRendezvous

        ACK_ID1 = 'DEADBEEF'
        ACK_ID2 = 'BEADCAFE'
        gax_api = _GAXSubscriberAPI(_random_gax_error=True)
        api = self._makeOne(gax_api)

        with self.assertRaises(GrpcRendezvous):
            api.subscription_acknowledge(self.SUB_PATH, [ACK_ID1, ACK_ID2])

        sub_path, ack_ids, options = gax_api._acknowledge_called_with
        self.assertEqual(sub_path, self.SUB_PATH)
        self.assertEqual(ack_ids, [ACK_ID1, ACK_ID2])
        self.assertIsNone(options)

    def test_subscription_modify_ack_deadline_hit(self):
        ACK_ID1 = 'DEADBEEF'
        ACK_ID2 = 'BEADCAFE'
        NEW_DEADLINE = 90
        gax_api = _GAXSubscriberAPI(_modify_ack_deadline_ok=True)
        api = self._makeOne(gax_api)

        api.subscription_modify_ack_deadline(
            self.SUB_PATH, [ACK_ID1, ACK_ID2], NEW_DEADLINE)

        sub_path, ack_ids, deadline, options = (
            gax_api._modify_ack_deadline_called_with)
        self.assertEqual(sub_path, self.SUB_PATH)
        self.assertEqual(ack_ids, [ACK_ID1, ACK_ID2])
        self.assertEqual(deadline, NEW_DEADLINE)
        self.assertIsNone(options)

    def test_subscription_modify_ack_deadline_miss(self):
        from google.cloud.exceptions import NotFound
        ACK_ID1 = 'DEADBEEF'
        ACK_ID2 = 'BEADCAFE'
        NEW_DEADLINE = 90
        gax_api = _GAXSubscriberAPI()
        api = self._makeOne(gax_api)

        with self.assertRaises(NotFound):
            api.subscription_modify_ack_deadline(
                self.SUB_PATH, [ACK_ID1, ACK_ID2], NEW_DEADLINE)

        sub_path, ack_ids, deadline, options = (
            gax_api._modify_ack_deadline_called_with)
        self.assertEqual(sub_path, self.SUB_PATH)
        self.assertEqual(ack_ids, [ACK_ID1, ACK_ID2])
        self.assertEqual(deadline, NEW_DEADLINE)
        self.assertIsNone(options)

    def test_subscription_modify_ack_deadline_error(self):
        from google.cloud.exceptions import GrpcRendezvous

        ACK_ID1 = 'DEADBEEF'
        ACK_ID2 = 'BEADCAFE'
        NEW_DEADLINE = 90
        gax_api = _GAXSubscriberAPI(_random_gax_error=True)
        api = self._makeOne(gax_api)

        with self.assertRaises(GrpcRendezvous):
            api.subscription_modify_ack_deadline(
                self.SUB_PATH, [ACK_ID1, ACK_ID2], NEW_DEADLINE)

        sub_path, ack_ids, deadline, options = (
            gax_api._modify_ack_deadline_called_with)
        self.assertEqual(sub_path, self.SUB_PATH)
        self.assertEqual(ack_ids, [ACK_ID1, ACK_ID2])
        self.assertEqual(deadline, NEW_DEADLINE)
        self.assertIsNone(options)


@unittest.skipUnless(_HAVE_GAX, 'No gax-python')
class Test_make_gax_publisher_api(_Base, unittest.TestCase):

    def _callFUT(self, connection):
        from google.cloud.pubsub._gax import make_gax_publisher_api
        return make_gax_publisher_api(connection)

    def test_live_api(self):
        from unit_tests._testing import _Monkey
        from google.cloud.pubsub import _gax as MUT

        channels = []
        mock_result = object()

        def mock_publisher_api(channel):
            channels.append(channel)
            return mock_result

        connection = _Connection(in_emulator=False)
        with _Monkey(MUT, PublisherApi=mock_publisher_api):
            result = self._callFUT(connection)

        self.assertIs(result, mock_result)
        self.assertEqual(channels, [None])

    def test_emulator(self):
        from unit_tests._testing import _Monkey
        from google.cloud.pubsub import _gax as MUT

        channels = []
        mock_result = object()
        insecure_args = []
        mock_channel = object()

        def mock_publisher_api(channel):
            channels.append(channel)
            return mock_result

        def mock_insecure_channel(host):
            insecure_args.append(host)
            return mock_channel

        host = 'CURR_HOST:1234'
        connection = _Connection(in_emulator=True, host=host)
        with _Monkey(MUT, PublisherApi=mock_publisher_api,
                     insecure_channel=mock_insecure_channel):
            result = self._callFUT(connection)

        self.assertIs(result, mock_result)
        self.assertEqual(channels, [mock_channel])
        self.assertEqual(insecure_args, [host])


@unittest.skipUnless(_HAVE_GAX, 'No gax-python')
class Test_make_gax_subscriber_api(_Base, unittest.TestCase):

    def _callFUT(self, connection):
        from google.cloud.pubsub._gax import make_gax_subscriber_api
        return make_gax_subscriber_api(connection)

    def test_live_api(self):
        from unit_tests._testing import _Monkey
        from google.cloud.pubsub import _gax as MUT

        channels = []
        mock_result = object()

        def mock_subscriber_api(channel):
            channels.append(channel)
            return mock_result

        connection = _Connection(in_emulator=False)
        with _Monkey(MUT, SubscriberApi=mock_subscriber_api):
            result = self._callFUT(connection)

        self.assertIs(result, mock_result)
        self.assertEqual(channels, [None])

    def test_emulator(self):
        from unit_tests._testing import _Monkey
        from google.cloud.pubsub import _gax as MUT

        channels = []
        mock_result = object()
        insecure_args = []
        mock_channel = object()

        def mock_subscriber_api(channel):
            channels.append(channel)
            return mock_result

        def mock_insecure_channel(host):
            insecure_args.append(host)
            return mock_channel

        host = 'CURR_HOST:1234'
        connection = _Connection(in_emulator=True, host=host)
        with _Monkey(MUT, SubscriberApi=mock_subscriber_api,
                     insecure_channel=mock_insecure_channel):
            result = self._callFUT(connection)

        self.assertIs(result, mock_result)
        self.assertEqual(channels, [mock_channel])
        self.assertEqual(insecure_args, [host])


class _GAXPublisherAPI(_GAXBaseAPI):

    _create_topic_conflict = False

    def list_topics(self, name, page_size, options):
        self._list_topics_called_with = name, page_size, options
        return self._list_topics_response

    def create_topic(self, name, options=None):
        self._create_topic_called_with = name, options
        if self._random_gax_error:
            raise self._make_grpc_error()
        if self._create_topic_conflict:
            raise self._make_grpc_failed_precondition()
        return self._create_topic_response

    def get_topic(self, name, options=None):
        self._get_topic_called_with = name, options
        if self._random_gax_error:
            raise self._make_grpc_error()
        try:
            return self._get_topic_response
        except AttributeError:
            raise self._make_grpc_not_found()

    def delete_topic(self, name, options=None):
        self._delete_topic_called_with = name, options
        if self._random_gax_error:
            raise self._make_grpc_error()
        if not self._delete_topic_ok:
            raise self._make_grpc_not_found()

    def publish(self, topic, messages, options=None):
        self._publish_called_with = topic, messages, options
        if self._random_gax_error:
            raise self._make_grpc_error()
        try:
            return self._publish_response
        except AttributeError:
            raise self._make_grpc_not_found()

    def list_topic_subscriptions(self, topic, page_size, options=None):
        self._list_topic_subscriptions_called_with = topic, page_size, options
        if self._random_gax_error:
            raise self._make_grpc_error()
        try:
            return self._list_topic_subscriptions_response
        except AttributeError:
            raise self._make_grpc_not_found()


class _GAXSubscriberAPI(_GAXBaseAPI):

    _create_subscription_conflict = False
    _modify_push_config_ok = False
    _acknowledge_ok = False
    _modify_ack_deadline_ok = False

    def list_subscriptions(self, project, page_size, options=None):
        self._list_subscriptions_called_with = (project, page_size, options)
        return self._list_subscriptions_response

    def create_subscription(self, name, topic,
                            push_config, ack_deadline_seconds,
                            options=None):
        self._create_subscription_called_with = (
            name, topic, push_config, ack_deadline_seconds, options)
        if self._random_gax_error:
            raise self._make_grpc_error()
        if self._create_subscription_conflict:
            raise self._make_grpc_failed_precondition()
        return self._create_subscription_response

    def get_subscription(self, name, options=None):
        self._get_subscription_called_with = name, options
        if self._random_gax_error:
            raise self._make_grpc_error()
        try:
            return self._get_subscription_response
        except AttributeError:
            raise self._make_grpc_not_found()

    def delete_subscription(self, name, options=None):
        self._delete_subscription_called_with = name, options
        if self._random_gax_error:
            raise self._make_grpc_error()
        if not self._delete_subscription_ok:
            raise self._make_grpc_not_found()

    def modify_push_config(self, name, push_config, options=None):
        self._modify_push_config_called_with = name, push_config, options
        if self._random_gax_error:
            raise self._make_grpc_error()
        if not self._modify_push_config_ok:
            raise self._make_grpc_not_found()

    def pull(self, name, max_messages, return_immediately, options=None):
        self._pull_called_with = (
            name, max_messages, return_immediately, options)
        if self._random_gax_error:
            raise self._make_grpc_error()
        try:
            return self._pull_response
        except AttributeError:
            raise self._make_grpc_not_found()

    def acknowledge(self, name, ack_ids, options=None):
        self._acknowledge_called_with = name, ack_ids, options
        if self._random_gax_error:
            raise self._make_grpc_error()
        if not self._acknowledge_ok:
            raise self._make_grpc_not_found()

    def modify_ack_deadline(self, name, ack_ids, deadline, options=None):
        self._modify_ack_deadline_called_with = (
            name, ack_ids, deadline, options)
        if self._random_gax_error:
            raise self._make_grpc_error()
        if not self._modify_ack_deadline_ok:
            raise self._make_grpc_not_found()


class _TopicPB(object):

    def __init__(self, name):
        self.name = name


class _PublishResponsePB(object):

    def __init__(self, message_ids):
        self.message_ids = message_ids


class _PushConfigPB(object):

    def __init__(self, push_endpoint):
        self.push_endpoint = push_endpoint


class _PubsubMessagePB(object):

    def __init__(self, message_id, data, attributes, publish_time):
        self.message_id = message_id
        self.data = data
        self.attributes = attributes
        self.publish_time = publish_time


class _ReceivedMessagePB(object):

    def __init__(self, ack_id, message):
        self.ack_id = ack_id
        self.message = message


class _PullResponsePB(object):

    def __init__(self, received_messages):
        self.received_messages = received_messages


class _SubscriptionPB(object):

    def __init__(self, name, topic, push_endpoint, ack_deadline_seconds):
        self.name = name
        self.topic = topic
        self.push_config = _PushConfigPB(push_endpoint)
        self.ack_deadline_seconds = ack_deadline_seconds


class _Connection(object):

    def __init__(self, in_emulator=False, host=None):
        self.in_emulator = in_emulator
        self.host = host
