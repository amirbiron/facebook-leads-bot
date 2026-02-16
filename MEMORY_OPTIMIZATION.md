# Memory Optimization for 512MB Render Plan

## Problem
The application was exceeding Render's 512MB memory limit, causing frequent crashes and restarts. The main culprit was Selenium + Chrome consuming 300-500MB+ per instance.

## Solutions Implemented

### 1. Chrome Browser Optimizations (Most Critical)
Added 40+ aggressive memory-saving flags to Chrome:
- `--disable-gpu`, `--disable-extensions`, `--disable-plugins`
- `--disable-webgl`, `--disable-3d-apis`
- Disabled images loading (`prefs.images: 2`) - saves significant memory
- `--js-flags=--max-old-space-size=256` - limits JavaScript heap to 256MB
- Memory-efficient rendering flags
- Single-process optimizations

### 2. Disabled Debug Mode in Production
- Changed `DEBUG_MODE` default from `true` to `false`
- No more screenshots or HTML dumps (saves ~50-100MB)
- Added explicit `DEBUG_MODE=false` to render.yaml

### 3. Reduced Processing Load
- **Posts per group**: 10 → 5
- **Groups per cycle**: 5 → 2
- **Max scrolls**: 8 → 4
- This reduces the amount of data processed and held in memory

### 4. Explicit Memory Cleanup
- Added `gc.collect()` calls after each group scan
- Added `gc.collect()` after each complete scan cycle
- Proper browser cleanup: close all windows before quit
- Clear `_seen_post_hashes` set on cleanup

### 5. Dockerfile Optimizations
- Clean up apt cache and temp files
- Added Python memory environment variables:
  - `PYTHONMALLOC=malloc`
  - `MALLOC_TRIM_THRESHOLD_=100000`
  - `MALLOC_MMAP_THRESHOLD_=100000`

### 6. Configuration Updates
- `render.yaml`: Reduced default values for posts and groups
- `config.py`: Updated defaults to memory-efficient values

## Expected Memory Usage

With these optimizations:
- **Chrome**: ~150-250MB (down from 300-500MB)
- **Python + dependencies**: ~100-150MB
- **MongoDB client**: ~20-40MB
- **Telegram bot**: ~20-30MB
- **Buffer**: ~50-100MB

**Total**: ~340-470MB (comfortably under 512MB limit)

## Monitoring

If you still experience memory issues, you can:

1. **Further reduce limits in render.yaml**:
   ```yaml
   - key: POSTS_PER_GROUP
     value: 3  # even lower
   - key: GROUPS_PER_CYCLE
     value: 1  # scan one group at a time
   ```

2. **Increase scan interval** to reduce frequency:
   ```yaml
   - key: CHECK_INTERVAL_MINUTES
     value: 240  # scan every 4 hours instead of 3
   ```

3. **Monitor memory usage** in Render dashboard

## Trade-offs

- **Less data per cycle**: You'll scan fewer posts per run
- **No debug screenshots**: Harder to troubleshoot scraping issues
- **No images loaded**: Faster but might affect some selectors
- **More frequent cycles**: Consider increasing CHECK_INTERVAL_MINUTES if needed

## If Still Having Issues

If memory still exceeds 512MB, consider:
1. Upgrading to Render's next tier (2GB RAM)
2. Using a lighter browser (requests + BeautifulSoup, but won't work for logged-in FB)
3. Splitting into multiple workers (one per group)
