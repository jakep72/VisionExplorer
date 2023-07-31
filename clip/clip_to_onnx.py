import clip
import torch
import onnxruntime as ort

#fix aten::scaled_dot_product_attention issue

def convert_to_onnx(onnx_name, checkpoint = None):
    device = "cuda:0" if torch.cuda.is_available() else "cpu"

    model, preprocess = clip.load("RN101", device=device)
    
    if checkpoint:
        checkpoint = torch.load(checkpoint, map_location=torch.device(device))
        model.load_state_dict(checkpoint['model_state_dict'])
    
    npx = model.visual.input_resolution
    dummy_image = torch.randn(10, 3, npx, npx, device=device)
    dummy_text = clip.tokenize(["quick brown fox", "lorem ipsum"]).to(device)

    model.forward(dummy_image, dummy_text)

    torch.onnx.export(model, (dummy_image, dummy_text), onnx_name, export_params=True,
                    input_names=["IMAGE","TEXT"],
                    output_names=["LOGITS_PER_IMAGE","LOGITS_PER_TEXT"],
                    opset_version=14,
                    dynamic_axes={
                        "IMAGE": {
                            0: "image_batch_size",
                        },
                        "TEXT": {
                            0: "text_batch_size",
                            },
                        "LOGITS_PER_IMAGE": {
                            0: "image_batch_size",
                            1: "text_batch_size",
                        },
                        "LOGITS_PER_TEXT": {
                            0: "text_batch_size",
                            1: "image_batch_size"
                        },
                    }

    )

convert_to_onnx("base_clip.onnx")