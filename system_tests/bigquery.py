# Copyright 2015 Google Inc. All rights reserved.
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

import operator

import unittest

from google.cloud import bigquery
from google.cloud.exceptions import Forbidden

from retry import RetryErrors
from retry import RetryInstanceState
from retry import RetryResult
from system_test_utils import unique_resource_id


def _make_dataset_name(prefix):
    return '%s%s' % (prefix, unique_resource_id())


def _rate_limit_exceeded(forbidden):
    """Predicate: pass only exceptions with 'rateLimitExceeded' as reason."""
    return any(error['reason'] == 'rateLimitExceeded'
               for error in forbidden._errors)


# We need to wait to stay within the rate limits.
# The alternative outcome is a 403 Forbidden response from upstream, which
# they return instead of the more appropriate 429.
# See: https://cloud.google.com/bigquery/quota-policy
retry_403 = RetryErrors(Forbidden, error_predicate=_rate_limit_exceeded)


class Config(object):
    """Run-time configuration to be modified at set-up.

    This is a mutable stand-in to allow test set-up to modify
    global state.
    """
    CLIENT = None


def setUpModule():
    Config.CLIENT = bigquery.Client()


class TestBigQuery(unittest.TestCase):

    def setUp(self):
        self.to_delete = []

    def tearDown(self):
        from google.cloud.bigquery.dataset import Dataset
        from google.cloud.storage import Bucket
        from google.cloud.exceptions import BadRequest
        from google.cloud.exceptions import Conflict

        def _still_in_use(bad_request):
            return any(error['reason'] == 'resourceInUse'
                       for error in bad_request._errors)

        retry_in_use = RetryErrors(BadRequest, error_predicate=_still_in_use)
        retry_409 = RetryErrors(Conflict)
        for doomed in self.to_delete:
            if isinstance(doomed, Bucket):
                retry_409(doomed.delete)(force=True)
            elif isinstance(doomed, Dataset):
                retry_in_use(doomed.delete)()
            else:
                doomed.delete()

    def test_create_dataset(self):
        DATASET_NAME = _make_dataset_name('create_dataset')
        dataset = Config.CLIENT.dataset(DATASET_NAME)
        self.assertFalse(dataset.exists())

        retry_403(dataset.create)()
        self.to_delete.append(dataset)

        self.assertTrue(dataset.exists())
        self.assertEqual(dataset.name, DATASET_NAME)

    def test_reload_dataset(self):
        DATASET_NAME = _make_dataset_name('reload_dataset')
        dataset = Config.CLIENT.dataset(DATASET_NAME)
        dataset.friendly_name = 'Friendly'
        dataset.description = 'Description'

        retry_403(dataset.create)()
        self.to_delete.append(dataset)

        other = Config.CLIENT.dataset(DATASET_NAME)
        other.reload()
        self.assertEqual(other.friendly_name, 'Friendly')
        self.assertEqual(other.description, 'Description')

    def test_patch_dataset(self):
        dataset = Config.CLIENT.dataset(_make_dataset_name('patch_dataset'))
        self.assertFalse(dataset.exists())

        retry_403(dataset.create)()
        self.to_delete.append(dataset)

        self.assertTrue(dataset.exists())
        self.assertIsNone(dataset.friendly_name)
        self.assertIsNone(dataset.description)
        dataset.patch(friendly_name='Friendly', description='Description')
        self.assertEqual(dataset.friendly_name, 'Friendly')
        self.assertEqual(dataset.description, 'Description')

    def test_update_dataset(self):
        dataset = Config.CLIENT.dataset(_make_dataset_name('update_dataset'))
        self.assertFalse(dataset.exists())

        retry_403(dataset.create)()
        self.to_delete.append(dataset)

        self.assertTrue(dataset.exists())
        after = [grant for grant in dataset.access_grants
                 if grant.entity_id != 'projectWriters']
        dataset.access_grants = after

        retry_403(dataset.update)()

        self.assertEqual(len(dataset.access_grants), len(after))
        for found, expected in zip(dataset.access_grants, after):
            self.assertEqual(found.role, expected.role)
            self.assertEqual(found.entity_type, expected.entity_type)
            self.assertEqual(found.entity_id, expected.entity_id)

    def test_list_datasets(self):
        datasets_to_create = [
            'new' + unique_resource_id(),
            'newer' + unique_resource_id(),
            'newest' + unique_resource_id(),
        ]
        for dataset_name in datasets_to_create:
            dataset = Config.CLIENT.dataset(dataset_name)
            retry_403(dataset.create)()
            self.to_delete.append(dataset)

        # Retrieve the datasets.
        all_datasets, token = Config.CLIENT.list_datasets()
        self.assertIsNone(token)
        created = [dataset for dataset in all_datasets
                   if dataset.name in datasets_to_create and
                   dataset.project == Config.CLIENT.project]
        self.assertEqual(len(created), len(datasets_to_create))

    def test_create_table(self):
        dataset = Config.CLIENT.dataset(_make_dataset_name('create_table'))
        self.assertFalse(dataset.exists())

        retry_403(dataset.create)()
        self.to_delete.append(dataset)

        TABLE_NAME = 'test_table'
        full_name = bigquery.SchemaField('full_name', 'STRING',
                                         mode='REQUIRED')
        age = bigquery.SchemaField('age', 'INTEGER', mode='REQUIRED')
        table = dataset.table(TABLE_NAME, schema=[full_name, age])
        self.assertFalse(table.exists())
        table.create()
        self.to_delete.insert(0, table)
        self.assertTrue(table.exists())
        self.assertEqual(table.name, TABLE_NAME)

    def test_list_tables(self):
        DATASET_NAME = _make_dataset_name('list_tables')
        dataset = Config.CLIENT.dataset(DATASET_NAME)
        self.assertFalse(dataset.exists())

        retry_403(dataset.create)()
        self.to_delete.append(dataset)

        # Retrieve tables before any are created for the dataset.
        all_tables, token = dataset.list_tables()
        self.assertEqual(all_tables, [])
        self.assertIsNone(token)

        # Insert some tables to be listed.
        tables_to_create = [
            'new' + unique_resource_id(),
            'newer' + unique_resource_id(),
            'newest' + unique_resource_id(),
        ]
        full_name = bigquery.SchemaField('full_name', 'STRING',
                                         mode='REQUIRED')
        age = bigquery.SchemaField('age', 'INTEGER', mode='REQUIRED')
        for table_name in tables_to_create:
            table = dataset.table(table_name, schema=[full_name, age])
            table.create()
            self.to_delete.insert(0, table)

        # Retrieve the tables.
        all_tables, token = dataset.list_tables()
        self.assertIsNone(token)
        created = [table for table in all_tables
                   if (table.name in tables_to_create and
                       table.dataset_name == DATASET_NAME)]
        self.assertEqual(len(created), len(tables_to_create))

    def test_patch_table(self):
        dataset = Config.CLIENT.dataset(_make_dataset_name('patch_table'))
        self.assertFalse(dataset.exists())

        retry_403(dataset.create)()
        self.to_delete.append(dataset)

        TABLE_NAME = 'test_table'
        full_name = bigquery.SchemaField('full_name', 'STRING',
                                         mode='REQUIRED')
        age = bigquery.SchemaField('age', 'INTEGER', mode='REQUIRED')
        table = dataset.table(TABLE_NAME, schema=[full_name, age])
        self.assertFalse(table.exists())
        table.create()
        self.to_delete.insert(0, table)
        self.assertTrue(table.exists())
        self.assertIsNone(table.friendly_name)
        self.assertIsNone(table.description)
        table.patch(friendly_name='Friendly', description='Description')
        self.assertEqual(table.friendly_name, 'Friendly')
        self.assertEqual(table.description, 'Description')

    def test_update_table(self):
        dataset = Config.CLIENT.dataset(_make_dataset_name('update_table'))
        self.assertFalse(dataset.exists())

        retry_403(dataset.create)()
        self.to_delete.append(dataset)

        TABLE_NAME = 'test_table'
        full_name = bigquery.SchemaField('full_name', 'STRING',
                                         mode='REQUIRED')
        age = bigquery.SchemaField('age', 'INTEGER', mode='REQUIRED')
        table = dataset.table(TABLE_NAME, schema=[full_name, age])
        self.assertFalse(table.exists())
        table.create()
        self.to_delete.insert(0, table)
        self.assertTrue(table.exists())
        voter = bigquery.SchemaField('voter', 'BOOLEAN', mode='NULLABLE')
        schema = table.schema
        schema.append(voter)
        table.schema = schema
        table.update()
        self.assertEqual(len(table.schema), len(schema))
        for found, expected in zip(table.schema, schema):
            self.assertEqual(found.name, expected.name)
            self.assertEqual(found.field_type, expected.field_type)
            self.assertEqual(found.mode, expected.mode)

    def test_insert_data_then_dump_table(self):
        import datetime
        from google.cloud._helpers import UTC

        NOW_SECONDS = 1448911495.484366
        NOW = datetime.datetime.utcfromtimestamp(
            NOW_SECONDS).replace(tzinfo=UTC)
        ROWS = [
            ('Phred Phlyntstone', 32, NOW),
            ('Bharney Rhubble', 33, NOW + datetime.timedelta(seconds=10)),
            ('Wylma Phlyntstone', 29, NOW + datetime.timedelta(seconds=20)),
            ('Bhettye Rhubble', 27, None),
        ]
        ROW_IDS = range(len(ROWS))
        dataset = Config.CLIENT.dataset(
            _make_dataset_name('insert_data_then_dump'))
        self.assertFalse(dataset.exists())

        retry_403(dataset.create)()
        self.to_delete.append(dataset)

        TABLE_NAME = 'test_table'
        full_name = bigquery.SchemaField('full_name', 'STRING',
                                         mode='REQUIRED')
        age = bigquery.SchemaField('age', 'INTEGER', mode='REQUIRED')
        now = bigquery.SchemaField('now', 'TIMESTAMP')
        table = dataset.table(TABLE_NAME, schema=[full_name, age, now])
        self.assertFalse(table.exists())
        table.create()
        self.to_delete.insert(0, table)
        self.assertTrue(table.exists())

        errors = table.insert_data(ROWS, ROW_IDS)
        self.assertEqual(len(errors), 0)

        rows = ()

        def _has_rows(result):
            return len(result[0]) > 0

        # Allow for 90 seconds of "warm up" before rows visible.  See:
        # https://cloud.google.com/bigquery/streaming-data-into-bigquery#dataavailability
        # 8 tries -> 1 + 2 + 4 + 8 + 16 + 32 + 64 = 127 seconds
        retry = RetryResult(_has_rows, max_tries=8)
        rows, _, _ = retry(table.fetch_data)()

        by_age = operator.itemgetter(1)
        self.assertEqual(sorted(rows, key=by_age),
                         sorted(ROWS, key=by_age))

    def test_load_table_from_local_file_then_dump_table(self):
        import csv
        import tempfile
        ROWS = [
            ('Phred Phlyntstone', 32),
            ('Bharney Rhubble', 33),
            ('Wylma Phlyntstone', 29),
            ('Bhettye Rhubble', 27),
        ]
        TABLE_NAME = 'test_table'

        dataset = Config.CLIENT.dataset(
            _make_dataset_name('load_local_then_dump'))

        retry_403(dataset.create)()
        self.to_delete.append(dataset)

        full_name = bigquery.SchemaField('full_name', 'STRING',
                                         mode='REQUIRED')
        age = bigquery.SchemaField('age', 'INTEGER', mode='REQUIRED')
        table = dataset.table(TABLE_NAME, schema=[full_name, age])
        table.create()
        self.to_delete.insert(0, table)

        with tempfile.NamedTemporaryFile(mode='w+') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(('Full Name', 'Age'))
            writer.writerows(ROWS)
            csv_file.flush()

            with open(csv_file.name, 'rb') as csv_read:
                job = table.upload_from_file(
                    csv_read,
                    source_format='CSV',
                    skip_leading_rows=1,
                    create_disposition='CREATE_NEVER',
                    write_disposition='WRITE_EMPTY',
                )

        def _job_done(instance):
            return instance.state.lower() == 'done'

        # Retry until done.
        retry = RetryInstanceState(_job_done, max_tries=8)
        retry(job.reload)()

        self.assertEqual(job.output_rows, len(ROWS))

        rows, _, _ = table.fetch_data()
        by_age = operator.itemgetter(1)
        self.assertEqual(sorted(rows, key=by_age),
                         sorted(ROWS, key=by_age))

    def test_load_table_from_storage_then_dump_table(self):
        import csv
        import tempfile
        from google.cloud.storage import Client as StorageClient
        local_id = unique_resource_id()
        BUCKET_NAME = 'bq_load_test' + local_id
        BLOB_NAME = 'person_ages.csv'
        GS_URL = 'gs://%s/%s' % (BUCKET_NAME, BLOB_NAME)
        ROWS = [
            ('Phred Phlyntstone', 32),
            ('Bharney Rhubble', 33),
            ('Wylma Phlyntstone', 29),
            ('Bhettye Rhubble', 27),
        ]
        TABLE_NAME = 'test_table'

        s_client = StorageClient()

        # In the **very** rare case the bucket name is reserved, this
        # fails with a ConnectionError.
        bucket = s_client.create_bucket(BUCKET_NAME)
        self.to_delete.append(bucket)

        blob = bucket.blob(BLOB_NAME)

        with tempfile.TemporaryFile(mode='w+') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(('Full Name', 'Age'))
            writer.writerows(ROWS)
            blob.upload_from_file(
                csv_file, rewind=True, content_type='text/csv')

        self.to_delete.insert(0, blob)

        dataset = Config.CLIENT.dataset(
            _make_dataset_name('load_gcs_then_dump'))

        retry_403(dataset.create)()
        self.to_delete.append(dataset)

        full_name = bigquery.SchemaField('full_name', 'STRING',
                                         mode='REQUIRED')
        age = bigquery.SchemaField('age', 'INTEGER', mode='REQUIRED')
        table = dataset.table(TABLE_NAME, schema=[full_name, age])
        table.create()
        self.to_delete.insert(0, table)

        job = Config.CLIENT.load_table_from_storage(
            'bq_load_storage_test_' + local_id, table, GS_URL)
        job.create_disposition = 'CREATE_NEVER'
        job.skip_leading_rows = 1
        job.source_format = 'CSV'
        job.write_disposition = 'WRITE_EMPTY'

        job.begin()

        def _job_done(instance):
            return instance.state in ('DONE', 'done')

        # Allow for 90 seconds of "warm up" before rows visible.  See:
        # https://cloud.google.com/bigquery/streaming-data-into-bigquery#dataavailability
        # 8 tries -> 1 + 2 + 4 + 8 + 16 + 32 + 64 = 127 seconds
        retry = RetryInstanceState(_job_done, max_tries=8)
        retry(job.reload)()

        rows, _, _ = table.fetch_data()
        by_age = operator.itemgetter(1)
        self.assertEqual(sorted(rows, key=by_age),
                         sorted(ROWS, key=by_age))

    def test_job_cancel(self):
        DATASET_NAME = _make_dataset_name('job_cancel')
        JOB_NAME = 'fetch_' + DATASET_NAME
        TABLE_NAME = 'test_table'
        QUERY = 'SELECT * FROM %s.%s' % (DATASET_NAME, TABLE_NAME)

        dataset = Config.CLIENT.dataset(DATASET_NAME)

        retry_403(dataset.create)()
        self.to_delete.append(dataset)

        full_name = bigquery.SchemaField('full_name', 'STRING',
                                         mode='REQUIRED')
        age = bigquery.SchemaField('age', 'INTEGER', mode='REQUIRED')
        table = dataset.table(TABLE_NAME, schema=[full_name, age])
        table.create()
        self.to_delete.insert(0, table)

        job = Config.CLIENT.run_async_query(JOB_NAME, QUERY)
        job.begin()
        job.cancel()

        def _job_done(instance):
            return instance.state in ('DONE', 'done')

        retry = RetryInstanceState(_job_done, max_tries=8)
        retry(job.reload)()

        # The `cancel` API doesn't leave any reliable traces on
        # the status of the job resource, so we can't really assert for
        # them here.  The best we can do is not that the API call didn't
        # raise an error, and that the job completed (in the `retry()`
        # above).
