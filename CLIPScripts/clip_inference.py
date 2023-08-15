import torch
import clip
from PIL import Image
from pathlib import Path
from CLIPScripts.clip_saliency_map import saliency_map


def clip_inference(image_path, model_folder, map=True):
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("RN101", device=device)

    if model_folder:
        cp_path = Path(model_folder) / Path("model_best.pt")
        checkpoint = torch.load(cp_path)
        model.load_state_dict(checkpoint['model_state_dict'])

    cap_path = Path(model_folder) / Path("tokens.pt")
    caption_choices = torch.load(cap_path)
    text = clip.tokenize(caption_choices, truncate=True) 

    image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)

    with torch.no_grad():
        image_logits, text_logits = model(image, text)
        probs = image_logits.softmax(dim=-1).cpu().numpy()

        max_idx = probs[0].argmax(axis=0)
        guess = caption_choices[max_idx]

    base = "an image of a defect"
    guess_text = guess.split(" ")
    base_text = base.split(" ")
    pred = list(set(guess_text).difference(base_text))[0]

    if map == True:
        saliency_map(image_path, guess, model, preprocess)
    return pred