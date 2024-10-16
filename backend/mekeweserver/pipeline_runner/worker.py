from typing import List
from multiprocessing import Process, Event

# from metaKEGG import Pipeline
# from mekeweserver.model import PipelineInputParams
import time


class PipelineWorker(Process):
    # constructor
    def __init__(self):
        # call the parent constructor
        Process.__init__(self)
        # create and store an event
        self.stop_event = Event()

    def run(self):

        while not self.stop_event.is_set():
            print("I AM ALIVE!")
            time.sleep(1)


worker = PipelineWorker()
worker.start()
print("Parent waiting 3 seconds")
time.sleep(3)
print("Parent stopping worker")
worker.stop_event.set()
worker.join()
print("Parent: we are done here")


# async def run_pipeline(files: str | List[str], params: PipelineInputParams):
#    pipeline = Pipeline(input_file_path=files, **params)
