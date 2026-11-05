from pathlib import Path
import time,torch
from avtr1_renderer.runtime.windows_warp import CudaWarpEngine
from avtr1_renderer.models.warp import WarpInput,WarpOutput,SerialWarpEngine
from avtr1_renderer.runtime import load_engine
root=Path('artifacts/main/build_artifacts')
a=CudaWarpEngine(root)
b=SerialWarpEngine(load_engine(root/'warp_network_windows.onnx',WarpInput,WarpOutput))
x=WarpInput(torch.randn(1,32,16,64,64,device='cuda'),torch.randn(1,21,3,device='cuda')*.1,torch.randn(1,21,3,device='cuda')*.1)
y=a(x).out;z=b(x).out;torch.cuda.synchronize();print('DIFF',float((y-z).abs().max()),'FINITE',torch.isfinite(y).all().item())
for k in range(4):
 t=time.perf_counter();y=a(x).out;torch.cuda.synchronize();print('CUDA frame ms',(time.perf_counter()-t)*1000)
