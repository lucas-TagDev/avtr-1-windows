"""Build native Windows TensorRT stages, with CUDA PyTorch for 3D GridSample."""
from pathlib import Path
import torch
import tensorrt as trt

root = Path(__file__).resolve().parents[1] / "artifacts/main/build_artifacts"
logger = trt.Logger(trt.Logger.WARNING)
for filename in ("warp_b5_0", "warp_b5_1", "warp_b5_final"):
    if (root / (filename + ".engine")).is_file():
        continue
    print("Building", filename, flush=True)
    builder = trt.Builder(logger)
    network = builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH))
    parser = trt.OnnxParser(network, logger)
    if not parser.parse((root / (filename + ".onnx")).read_bytes()):
        raise RuntimeError("\n".join(str(parser.get_error(i)) for i in range(parser.num_errors)))
    config = builder.create_builder_config()
    config.set_flag(trt.BuilderFlag.FP16)
    profile = builder.create_optimization_profile()
    for i in range(network.num_inputs):
        inp = network.get_input(i)
        shape = tuple(inp.shape)
        if inp.name.endswith('GridSample_output_0') and inp.name.startswith('/dense'):
            shape = (110,4,16,64,64)
        elif inp.name == '/dense_motion_network/Sigmoid_output_0':
            shape = (5,1,64,64)
        elif inp.name == '/GridSample_output_0':
            shape = (5,32,16,64,64)
        elif inp.name.endswith('feature_3d'):
            shape = (5,32,16,64,64)
        elif inp.name in ('kp_source','kp_driving'):
            shape = (5,21,3)
        assert all(x>0 for x in shape),(inp.name,shape)
        profile.set_shape(inp.name,shape,shape,shape)
    config.add_optimization_profile(profile)
    plan = builder.build_serialized_network(network, config)
    if plan is None:
        raise RuntimeError(filename)
    (root / (filename + ".engine")).write_bytes(bytes(plan))
    print("Built", filename, flush=True)
