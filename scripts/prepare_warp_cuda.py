"""Split the portable warp graph at GridSample so PyTorch can run 3D sampling on CUDA."""
import json
from pathlib import Path
import onnx
from onnx.utils import extract_model

root = Path(__file__).resolve().parents[1] / "artifacts/main/build_artifacts"
model = onnx.shape_inference.infer_shapes(onnx.load(str(root / "warp_network_windows.onnx")))
inferred = root / "warp_inferred.onnx"
onnx.save(model, str(inferred))
samples = [n for n in model.graph.node if n.op_type == "GridSample"]
inputs = [i.name for i in model.graph.input]
steps = []
for index, node in enumerate(samples):
    output = root / f"warp_cuda_{index}.onnx"
    extract_model(str(inferred), str(output), inputs, list(node.input))
    attrs = {a.name: onnx.helper.get_attribute_value(a) for a in node.attribute}
    attrs = {k: v.decode() if isinstance(v, bytes) else v for k, v in attrs.items()}
    steps.append(dict(model=output.name, inputs=list(node.input), output=node.output[0], attrs=attrs))
    inputs += list(node.output)
output = root / "warp_cuda_final.onnx"
extract_model(str(inferred), str(output), inputs, [o.name for o in model.graph.output])
for path in [root / s["model"] for s in steps] + [output]:
    assert not any(n.op_type == "GridSample" for n in onnx.load(str(path)).graph.node), path
(root / "warp_cuda.json").write_text(json.dumps(steps), encoding="utf-8")
print("CUDA warp stages ready")
