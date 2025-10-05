# Memory-Safe Streaming Upload Implementation

## Overview

This document describes the memory-safe streaming upload implementation for handling large files (>1GB) without memory exhaustion.

## Problem Statement

The original upload implementation had a critical memory safety issue:

```python
# OLD IMPLEMENTATION (UNSAFE)
file_content = await file.read()  # Loads entire file into memory!
file_size = len(file_content)
sha256_hash = hashlib.sha256(file_content).hexdigest()
```

For a 2GB file, this would:
- Allocate 2GB for `file_content`
- Allocate another 2GB for the BytesIO wrapper
- Risk out-of-memory errors on the API server
- Block other requests during upload

## Solution Architecture

### Streaming Hash Wrapper

We introduced `StreamingHashWrapper` that:
1. Wraps the upload file stream
2. Computes SHA256 hash incrementally as data passes through
3. Tracks total bytes read
4. Never buffers the entire file in memory

```python
class StreamingHashWrapper(io.BufferedIOBase):
    def read(self, size=-1):
        chunk = self.source.read(size)  # Read one chunk
        if chunk:
            self.hasher.update(chunk)   # Update hash incrementally
            self.bytes_read += len(chunk)
        return chunk                     # Pass chunk to storage
```

### Upload Flow

```
┌─────────────────┐
│  Client Upload  │
│   (Any Size)    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│         FastAPI UploadFile Stream                    │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │     StreamingHashWrapper                     │  │
│  │                                              │  │
│  │  • Reads 8KB chunks                         │  │
│  │  • Updates SHA256 incrementally             │  │
│  │  • Counts bytes                             │  │
│  │  • Passes chunks through                    │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
└────────┬────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│         Storage Backend                              │
│                                                      │
│  Local: shutil.copyfileobj(stream, file)           │
│         • Reads chunks from wrapper                 │
│         • Writes chunks to disk                     │
│         • 8KB buffer, constant memory               │
│                                                      │
│  S3: s3_client.upload_fileobj(stream, bucket, key) │
│      • Streams chunks to S3                         │
│      • No full file buffering                       │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### Memory Usage Analysis

**Per Upload:**
- StreamingHashWrapper: ~16KB (2x 8KB chunk buffer)
- SHA256 hasher state: ~200 bytes
- Byte counter: ~8 bytes
- Total overhead: **~16.2 KB** (constant, regardless of file size)

**Example: 10GB Upload**
- Old implementation: 10GB+ memory usage (full buffering)
- New implementation: ~16KB memory usage (streaming)
- **Memory reduction: 99.9998%**

## Implementation Details

### Chunk Size Selection

We use **8KB (8192 bytes)** chunks because:
- Optimal for disk I/O (matches common filesystem block size)
- Small enough to keep memory usage minimal
- Large enough to avoid excessive overhead
- Standard buffer size used by `shutil.copyfileobj()`

### Hash Computation

SHA256 hash is computed incrementally using the hashlib streaming API:

```python
hasher = hashlib.sha256()
while reading:
    chunk = read_chunk()
    hasher.update(chunk)  # Update hash with chunk
hash_result = hasher.hexdigest()
```

This is mathematically equivalent to:
```python
hasher = hashlib.sha256()
hasher.update(entire_file)  # All at once
hash_result = hasher.hexdigest()
```

But uses constant memory instead of O(file_size) memory.

### Storage Backend Integration

Both storage backends already supported streaming:

**Local Filesystem:**
```python
def store_blob(self, file: BinaryIO, key: str) -> str:
    with open(target_path, "wb") as f:
        shutil.copyfileobj(file, f)  # Streams in chunks
```

**S3 (MinIO):**
```python
def store_blob(self, file: BinaryIO, key: str) -> str:
    self.s3_client.upload_fileobj(file, bucket, key)  # Streams in chunks
```

No changes needed to storage backends!

## Testing Strategy

### Unit Tests
- `test_streaming_hash_small_file`: Verify basic hash computation
- `test_streaming_hash_chunked_read`: Verify chunked reading works
- `test_streaming_hash_empty_file`: Edge case handling
- `test_streaming_hash_large_simulated`: 100MB simulated file
- `test_hash_consistency`: Verify hash matches standard computation

### Integration Tests
- `test_upload_with_streaming_hash`: End-to-end upload flow
- `test_upload_large_file_streaming`: 100MB real upload
- `test_upload_very_large_file_memory_safe`: 500MB upload
- `test_upload_multiple_large_sequential`: Multiple large uploads
- `test_upload_hash_consistency`: Various file sizes (0 bytes to 10MB)

### Stress Tests
Files tested:
- 0 bytes (empty file)
- 1 byte
- 100 bytes
- 8192 bytes (exactly one chunk)
- 8193 bytes (just over one chunk)
- 1 MB
- 10 MB
- 100 MB
- 500 MB

## Performance Characteristics

### Throughput
- Limited by disk I/O or network bandwidth, not CPU
- SHA256 hashing: ~500 MB/s on modern CPUs
- Disk writes: 100-500 MB/s (SSD)
- S3 uploads: 10-100 MB/s (network dependent)

### Latency
- First byte latency: Same as before (immediate streaming)
- Total time: Dominated by I/O, not processing
- Memory allocation: Constant time (no scaling with file size)

### Scalability
- Can handle thousands of concurrent uploads (memory per upload is constant)
- No memory pressure as file sizes increase
- Tested up to 500MB in automated tests
- Designed for >1GB files

## Backwards Compatibility

The change is **fully backwards compatible**:
- Same API endpoint signature
- Same request/response format
- Same database schema
- Same file storage format
- Existing clients work without changes

Only the internal implementation changed to use streaming.

## Monitoring and Observability

Logs remain the same:
```
INFO | File processed | run_id=42 size_bytes=1073741824 sha256=abc123...
INFO | Stored file in storage backend | run_id=42 storage_key=runs/42/file.tar.gz
```

No log changes needed - streaming is transparent to observability.

## Future Enhancements

Potential improvements:
1. **Configurable chunk size**: Allow tuning via environment variable
2. **Progress callbacks**: Report upload progress for large files
3. **Resume support**: Allow resuming interrupted uploads
4. **Compression**: Compress files during upload to save storage
5. **Deduplication**: Check hash before storage to avoid duplicates

## References

- [Python hashlib documentation](https://docs.python.org/3/library/hashlib.html)
- [shutil.copyfileobj documentation](https://docs.python.org/3/library/shutil.html#shutil.copyfileobj)
- [boto3 upload_fileobj documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.upload_fileobj)
- Milestone 1 Gap Analysis: Streamed Upload & Memory Safety requirement

## Validation Results

✅ All unit tests passing
✅ All integration tests passing  
✅ Hash computation verified (matches standard SHA256)
✅ Large file handling tested (up to 500MB)
✅ Memory efficiency verified (constant memory usage)
✅ Storage backends work without modification
✅ Backwards compatibility maintained
