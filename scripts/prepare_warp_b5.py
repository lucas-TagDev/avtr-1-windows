from pathlib import Path
import sys,onnx,onnx_graphsurgeon as gs,json
from onnx.utils import extract_model
from build_renderer_engines import _surge_warp
root=Path(__file__).resolve().parents[1]/'artifacts/main/build_artifacts'
g=gs.import_onnx(onnx.load(str(root/'warp_network_windows.onnx')))
_surge_warp(g)
for t in list(g.inputs)+list(g.outputs):
 t.shape[0]=5
g.cleanup().toposort()
m=gs.export_onnx(g);m.ir_version=8
m.graph.ClearField('value_info')
m=onnx.shape_inference.infer_shapes(m)
p=root/'warp_b5_inferred.onnx';onnx.save(m,str(p))
samples=[n for n in m.graph.node if n.op_type=='GridSample']
inputs=[t.name for t in m.graph.input]
nodes=list(m.graph.node);cut=nodes.index(samples[1]);before={x for n in nodes[:cut] for x in n.output};after={x for n in nodes[cut+1:] for x in n.input}
types={t.name:t.type.tensor_type.elem_type for t in list(m.graph.value_info)+list(m.graph.input)+list(m.graph.output)}
frontier=sorted(x for x in before&after if types.get(x)==onnx.TensorProto.FLOAT)
steps=[]
for i,node in enumerate(samples):
 outputs=list(node.input)
 if i==1: outputs=list(dict.fromkeys(outputs+frontier))
 out=root/f'warp_b5_{i}.onnx';extract_model(str(p),str(out),inputs,outputs)
 attrs={a.name:onnx.helper.get_attribute_value(a) for a in node.attribute};attrs={k:v.decode() if isinstance(v,bytes) else v for k,v in attrs.items()}
 steps.append(dict(model=out.name,inputs=list(node.input),output=node.output[0],attrs=attrs))
 inputs=list(dict.fromkeys(inputs+list(node.output)+(frontier if i==1 else [])))
extract_model(str(p),str(root/'warp_b5_final.onnx'),inputs,[o.name for o in m.graph.output])
(root/'warp_b5.json').write_text(json.dumps(steps))
print('B5 partition ready',frontier)
