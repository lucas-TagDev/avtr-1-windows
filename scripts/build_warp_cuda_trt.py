"""Build native Windows TensorRT stages, with CUDA PyTorch for 3D GridSample."""
from pathlib import Path
import torch
import tensorrt as trt

root = Path(__file__).resolve().parents[1] / "artifacts/main/build_artifacts"
logger = trt.Logger(trt.Logger.WARNING)
for filename in ("warp_cuda_0", "warp_cuda_1", "warp_cuda_final"):
    print("Building", filename, flush=True)
    builder = trt.Builder(logger)
    network = builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH))
    parser = trt.OnnxParser(network, logger)
    if not parser.parse((root / (filename + ".onnx")).read_bytes()):
        raise RuntimeError("\n".join(str(parser.get_error(i)) for i in range(parser.num_errors)))
    config = builder.create_builder_config()
    config.set_flag(trt.BuilderFlag.FP16)
    plan = builder.build_serialized_network(network, config)
    if plan is None:
        raise RuntimeError(filename)
    (root / (filename + ".engine")).write_bytes(bytes(plan))
    print("Built", filename, flush=True)
