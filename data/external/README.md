# data/external

Sources that cannot be fetched automatically from the build environment —
the host refuses the request, the provider requires a credential, or there is
no stable endpoint.

**Everything in here is gitignored.** Files are re-obtainable by following
`docs/data/ACQUISITION_GUIDE.md`; the repository stays small and carries no
third-party data.

One folder per registry key. Keep the publisher's original filename, and do
not unzip — the pipeline reads archives directly and the checksum of the
original file goes into the provenance manifest.

Validate whatever you have placed:

```bash
python -m siting_atlas.ingest.external --check
```
