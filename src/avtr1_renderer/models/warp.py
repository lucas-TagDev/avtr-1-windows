# SPDX-FileCopyrightText: 2026 Goodsize Inc.
# SPDX-License-Identifier: LicenseRef-AVTR-1-Community

"""LivePortrait warp network I/O contract.

The legacy build is fixed-batch ``B=1``; the batched build under
``renderer_engines_b5/warp_network_b5_fp16.engine`` takes ``B`` in
``[1, 5]``. The dataclass accepts both.

Engine I/O:
    input  ``feature_3d``  FLOAT (B, 32, 16, 64, 64)
    input  ``kp_source``   FLOAT (B, 21, 3)
    input  ``kp_driving``  FLOAT (B, 21, 3)
    output ``out``         FLOAT (B, 256, 64, 64)
"""

from __future__ import annotations

from dataclasses import dataclass

import torch

from avtr1_renderer.runtime import InferenceEngine


@dataclass(slots=True)
class WarpInput:
    feature_3d: torch.Tensor  # (B, 32, 16, 64, 64)
    kp_source: torch.Tensor  # (B, 21, 3)
    kp_driving: torch.Tensor  # (B, 21, 3)

    def __post_init__(self) -> None:
        b = self.feature_3d.shape[0]
        assert self.feature_3d.shape == (b, 32, 16, 64, 64), (
            f"feature_3d must be (B, 32, 16, 64, 64), got {tuple(self.feature_3d.shape)}"
        )
        assert self.kp_source.shape == self.kp_driving.shape == (b, 21, 3), (
            f"kp shapes must be ({b}, 21, 3), got "
            f"source={tuple(self.kp_source.shape)}, "
            f"driving={tuple(self.kp_driving.shape)}"
        )


@dataclass(slots=True)
class WarpOutput:
    out: torch.Tensor  # (B, 256, 64, 64)


WarpEngine = InferenceEngine[WarpInput, WarpOutput]


class SerialWarpEngine:
    """Run the portable batch-one ONNX warp for each frame on Windows."""

    def __init__(self, engine: WarpEngine):
        self.engine = engine

    def allocate_outputs(self, shapes=None):
        return self.engine.allocate_outputs(shapes)

    def __call__(self, inputs: WarpInput, out: WarpOutput | None = None) -> WarpOutput:
        frames = []
        for i in range(inputs.feature_3d.shape[0]):
            result = self.engine(WarpInput(
                feature_3d=inputs.feature_3d[i:i+1].contiguous(),
                kp_source=inputs.kp_source[i:i+1].contiguous(),
                kp_driving=inputs.kp_driving[i:i+1].contiguous(),
            ))
            frames.append(result.out)
        combined = torch.cat(frames, dim=0)
        if out is not None:
            out.out.copy_(combined)
            return out
        return WarpOutput(out=combined)
