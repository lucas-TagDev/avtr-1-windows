from pathlib import Path
import onnx
from avtr1_renderer.avtr1_artifact_manager import get_artifact_manager, get_storage_root
source = get_artifact_manager().get_artifact_path("warp_network_ori_onnx")
target = get_storage_root() / "build_artifacts" / "warp_network_windows.onnx"
if not target.is_file():
    model = onnx.version_converter.convert_version(onnx.load(str(source)), 20)
    onnx.save(model, str(target))
print(target)
