import time
import numpy as np
import torch
from avtr1_renderer.pipeline import Pipeline
from avtr1_renderer.types import Chunk, RenderOptions

pipeline, registry = Pipeline.from_artifacts(avatar_ids=["maria"])
mg = pipeline._motion_generator
window = (mg.chunk_size + mg.future_size) * mg.frame_len + mg.audio_shift
chunk = Chunk(audio_speech=np.zeros(window, dtype=np.float32),
              audio_listen=np.zeros(window, dtype=np.float32))
state = None
timings = []
for i in range(12):
    torch.cuda.synchronize()
    start = time.perf_counter()
    state, frames = pipeline.process_chunk(registry["maria"], chunk, state,
                                          RenderOptions(bg_id="plain_white", pixel_format="yuv_i420"))
    count = sum(1 for _ in frames)
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - start
    print(f"Chunk {i}: {count} frames in {elapsed*1000:.1f} ms", flush=True)
    if i >= 2:
        timings.append(elapsed)
print(f"MEAN_MS={np.mean(timings)*1000:.1f}; FPS={5/np.mean(timings):.2f}; REALTIME={np.mean(timings)<=0.2}", flush=True)
