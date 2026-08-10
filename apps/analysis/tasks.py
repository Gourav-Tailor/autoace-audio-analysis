from concurrent.futures import ThreadPoolExecutor

PROCESSING_POOL = ThreadPoolExecutor(max_workers=4)


def enqueue_batch_audio_processing(batch_id):
    """Schedule the audio-analysis phase of a batch in a background thread.

    This keeps the upload endpoint responsive while allowing a lightweight local
    queue implementation to stand in for Celery/Redis in development.
    """

    future = PROCESSING_POOL.submit(_process_batch_audio, batch_id)
    return future


def _process_batch_audio(batch_id):
    from .models import Batch
    from .upload_handlers import BatchProcessor

    batch = Batch.objects.get(pk=batch_id)
    processor = BatchProcessor(batch=batch)
    return processor.process_audio()
