# Attachments on Google Cloud Storage

This addon allows to store the attachments (documents and assets) on [Google Cloud Storage](https://cloud.google.com/storage).

## Configuration

Activate GCS:

* Create or set the system parameter with the key `ir_attachment.location` and the value in the form `gcs`.

Configure accesses with environment variables:

* `GOOGLE_APPLICATION_CREDENTIALS` is the path to service account JSON file, or empty if you're using Workload Identity
* `GCS_BUCKET_NAME` is the bucket name, the strings `{db}` and `{env}` can be used inside that variable and the values will be replaced respectively by the database name and environment name.

This addon must be added in the server wide addons with (`--load` option):

```--load=web,attachment_gcs```

## Limitations

* You need to call `env['ir.attachment'].force_storage()` after having changed the `ir_attachment.location` configuration in order to migrate the existing attachments to Google Cloud Storage.

# Camptocamp Dependencies

This module depends on [Camptocamp's `base_attachment_object_storage`](https://github.com/camptocamp/odoo-cloud-platform/tree/16.0/base_attachment_object_storage), which is included in this repository.