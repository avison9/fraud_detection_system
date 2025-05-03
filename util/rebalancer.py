from util.logger_conf import ConsumerLogger
from kafka.consumer.subscription_state import ConsumerRebalanceListener
import threading
import time
from datetime import datetime, timedelta
import os


logger =  ConsumerLogger(os.path.basename(__file__)).get_logger()

class RebalanceListener(ConsumerRebalanceListener):
    def __init__(self, consumer, buffer, flush_callback, timeout_minutes=5):
        self.consumer = consumer
        self.buffer = buffer
        self.flush_callback = flush_callback
        self.timeout = timedelta(minutes=timeout_minutes)
        self.last_used = datetime.utcnow()
        self.lock = threading.Lock()
        self.running = True

        # Start background thread to clear buffer if idle
        self.cleaner_thread = threading.Thread(target=self._buffer_cleaner, daemon=True)
        self.cleaner_thread.start()

    def _buffer_cleaner(self):
        while self.running:
            time.sleep(60)
            with self.lock:
                now = datetime.utcnow()
                if self.buffer and now - self.last_used > self.timeout:
                    try:
                        print("[INFO][Rebalance] Auto-clearing idle buffer...")
                        self.buffer.clear()
                        print("[INFO][Rebalance] Buffer cleared after idle timeout.")
                    except Exception as e:
                        print(f"[INFO][Rebalance] Error during idle flush: {e}")

    def update_last_used(self):
        with self.lock:
            self.last_used = datetime.utcnow()

    def on_partitions_revoked(self, revoked):
        with self.lock:
            if self.buffer:
                print("[INFO][Rebalance] Flushing buffer before partition revocation...")
                try:
                    self.flush_callback(self.buffer)
                    self.buffer.clear()
                except Exception as e:
                    print(f"[INFO][Rebalance] Error during flush: {e}")
        print(f"Partitions revoked: {revoked}")
        self.consumer.commit()

    def on_partitions_assigned(self, assigned):
        print(f"Partitions assigned: {assigned}")

    def stop(self):
        self.running = False
