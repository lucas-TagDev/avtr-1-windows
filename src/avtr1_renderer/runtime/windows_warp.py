"""Native Windows CUDA warp without the Linux-only TensorRT sampling plugin."""
import json
import os
from pathlib import Path
import torch
import numpy as np
import onnxruntime as ort
import tensorrt as trt
from avtr1_renderer.models.warp import WarpInput, WarpOutput


class _Stage:
    def __init__(self, path):
        stream = torch.cuda.current_stream()
        self.session = ort.InferenceSession(str(path), providers=[
            ("CUDAExecutionProvider", {"user_compute_stream": str(stream.cuda_stream)}),
            "CPUExecutionProvider",
        ])
        self.inputs = self.session.get_inputs()
        self.outputs = self.session.get_outputs()

    def __call__(self, values):
        binding = self.session.io_binding()
        for meta in self.inputs:
            tensor = values[meta.name].contiguous()
            values[meta.name] = tensor
            binding.bind_input(meta.name, "cuda", 0, np.float32, tuple(tensor.shape), tensor.data_ptr())
        result = {}
        for meta in self.outputs:
            if not all(isinstance(d, int) and d > 0 for d in meta.shape):
                raise ValueError(f"Unresolved CUDA warp shape: {meta.name}: {meta.shape}")
            tensor = torch.empty(meta.shape, dtype=torch.float32, device="cuda")
            binding.bind_output(meta.name, "cuda", 0, np.float32, tuple(tensor.shape), tensor.data_ptr())
            result[meta.name] = tensor
        self.session.run_with_iobinding(binding)
        values.update(result)


class _TrtStage:
    def __init__(self, path):
        logger = trt.Logger(trt.Logger.ERROR)
        runtime = trt.Runtime(logger)
        self.engine = runtime.deserialize_cuda_engine(path.read_bytes())
        if self.engine is None:
            raise RuntimeError(f"Could not load {path}")
        self.context = self.engine.create_execution_context()
        self.names = [self.engine.get_tensor_name(i) for i in range(self.engine.num_io_tensors)]

    def __call__(self, values):
        result = {}
        for name in self.names:
            if self.engine.get_tensor_mode(name) == trt.TensorIOMode.INPUT:
                source = name if name in values else name.removeprefix("__")
                tensor = values[source].contiguous()
                values[name] = tensor
                self.context.set_input_shape(name, tuple(tensor.shape))
            else:
                tensor = torch.empty(tuple(self.context.get_tensor_shape(name)),
                                     dtype=torch.float32, device="cuda")
                result[name] = tensor
            self.context.set_tensor_address(name, tensor.data_ptr())
        if not self.context.execute_async_v3(torch.cuda.current_stream().cuda_stream):
            raise RuntimeError("CUDA warp execution failed")
        values.update(result)


def _stage(path):
    engine = path.with_suffix(".engine")
    return _TrtStage(engine) if engine.is_file() else _Stage(path)


class CudaWarpEngine:
    def __init__(self, root: Path):
        batched = all((root / (name + ".engine")).is_file() for name in ("warp_b5_0", "warp_b5_1", "warp_b5_final"))
        prefix = "warp_b5" if batched else "warp_cuda"
        self.batch_size = 5 if batched else 1
        self.steps = json.loads((root / (prefix + ".json")).read_text())
        self.stages = [_stage(root / step["model"]) for step in self.steps]
        self.final = _stage(root / (prefix + "_final.onnx"))

    def __call__(self, inputs: WarpInput, out: WarpOutput | None = None):
        frames = []
        for i in range(0, inputs.feature_3d.shape[0], self.batch_size):
            count = min(self.batch_size, inputs.feature_3d.shape[0] - i)
            values = {}
            for name in ("feature_3d", "kp_source", "kp_driving"):
                tensor = getattr(inputs, name)[i:i+count]
                if count < self.batch_size:
                    tensor = torch.cat([tensor, tensor[-1:].expand(self.batch_size-count, *tensor.shape[1:])])
                values[name] = tensor.contiguous()
            for stage, step in zip(self.stages, self.steps):
                stage(values)
                attrs = step["attrs"]
                feature, grid = (values[name] for name in step["inputs"])
                half = os.environ.get("AVTR1_WARP_SAMPLE_FP16", "0") == "1"
                values[step["output"]] = torch.nn.functional.grid_sample(
                    feature.half() if half else feature, grid.half() if half else grid,
                    mode="bilinear", padding_mode=attrs.get("padding_mode", "zeros"),
                    align_corners=bool(attrs.get("align_corners", 0)),
                ).float()
            self.final(values)
            frames.append(values["out"][:count])
        result = torch.cat(frames)
        if out is not None:
            out.out.copy_(result)
            return out
        return WarpOutput(out=result)
