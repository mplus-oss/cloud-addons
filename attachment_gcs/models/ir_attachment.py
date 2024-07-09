# -*- coding: utf-8 -*-

import google.auth
import google.cloud.storage
import os
import re
import io
from odoo import models, fields, api, _, exceptions

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def _get_stores(self):
        return ["gcs"] + super(IrAttachment, self)._get_stores()

    @api.model
    def _get_gcs_client(self):
        # This will use the GOOGLE_APPLICATION_CREDENTIALS env variable or the workload identity token\
        try:
            credentials, project_id = google.auth.default()
        except google.auth.exceptions.DefaultCredentialsError:
            raise exceptions.UserError(
                "Credential does not set correctly, either use GOOGLE_APPLICATION_CREDENTIALS or use Workload Identity"
            )
        storage_client = google.cloud.storage.Client(project=project_id, credentials=credentials)

        bucket_name = os.environ.get("GCS_BUCKET_NAME")

        if not bucket_name:
            raise exceptions.UserError("GCS_BUCKET_NAME is not set")

        return storage_client


    @api.model
    def _get_bucket_name(self):
        running_env = os.environ.get("RUNNING_ENV", "dev")
        bucket_name = os.environ.get("GCS_BUCKET_NAME", "{env}-{db}")
        bucket_name.format(env=running_env, db=self.env.cr.dbname)
        bucket_name = re.sub(r"[\W_]+", "-", bucket_name)

        return str.lower(bucket_name)[:63]


    @api.model
    def _get_bucket_client(self, bucket_name=None):
        if not bucket_name:
            bucket_name = self._get_bucket_name()

        bucket_client = self._get_gcs_client().bucket(bucket_name)
        return bucket_client


    @api.model
    def _store_file_read(self, fname, bin_size=False):
        if fname.startswith("gcs://"):
            key = fname.replace("gcs://", "", 1).lower()
            if "/" in key:
                bucket_name, key = key.split("/", 1)
            else:
                bucket_name = None
            bucket_client = self._get_bucket_client(bucket_name)
            if not bucket_client:
                return ""
            try:
                blob = bucket_client.get_blob(key)
                read = blob.download_as_bytes()
            except Exception:
                read = ""
                _logger.info("Attachment '%s' missing on object storage", fname)
            return read
        else:
            return super(IrAttachment, self)._store_file_read(fname, bin_size)

    def _store_file_write(self, key, bin_data):
        location = self.env.context.get("storage_location") or self._storage()
        if location == "gcs":
            bucket_client = self._get_bucket_client()
            filename = "gcs://%s/%s" % (bucket_client.name, key)
            with io.BytesIO() as file:
                blob = bucket_client.blob(key)
                file.write(bin_data)
                file.seek(0)
                blob.upload_from_file(file)
        else:
            _super = super(IrAttachment, self)
            filename = _super._store_file_write(key, bin_data)

        return filename


    def _store_file_delete(self, fname):
        if fname.startswith("gcs://"):
            key = fname.replace("gcs://", "", 1).lower()
            if "/" in key:
                bucket_name, key = key.split("/", 1)
            else:
                bucket_name = None
            bucket_client = self._get_bucket_client(bucket_name)
            if not bucket:
                return
            try:
                blob = bucket_client.get_blob(key)
                blob.delete()
            except Exception:
                _logger.info("Attachment '%s' missing on object storage", fname)
        else:
            super(IrAttachment, self)._store_file_delete(fname)