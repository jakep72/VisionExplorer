import clip
import torch
from PIL import Image
import pandas as pd
import numpy as np
from sklearn.manifold import TSNE
import seaborn as sns
import matplotlib.pyplot as plt


def tsne_plot(features, labels):
    embedded = TSNE(n_components=2, learning_rate='auto',
                    perplexity=1).fit_transform(features.cpu().numpy())
    
    df = pd.DataFrame()
    df['tsne-2d-one'] = embedded[:,0]
    df['tsne-2d-two'] = embedded[:,1]
    df['y'] = labels

    plt.figure(figsize=(16,10))
    sns.scatterplot(
        x="tsne-2d-one", y="tsne-2d-two",
        hue="y",
        palette=sns.color_palette("bright",len(labels)),
        data=df,
        legend="full"
    )
    plt.show()

def img2txt(model, image, text):
    image_features = model.encode_image(image)
    text_features = model.encode_text(text)

    image_features = image_features / image_features.norm(dim=1, keepdim=True)
    text_features = text_features / text_features.norm(dim=1, keepdim=True)

    stacked_features = torch.cat([image_features, text_features], dim=0)

    logit_scale = model.logit_scale.exp()

    logits = logit_scale * image_features @ text_features.t()

    return logits, stacked_features

def img2img(model, image1, image2):
    image1_features = model.encode_image(image1)
    image2_features = model.encode_imag(image2)

    image1_features = image1_features / image1_features.norm(dim=1, keepdim=True)
    image2_features = image2_features / image2_features.norm(dim=1, keepdim=True)

    logits_scale = model.logit_scale.exp()

    logits = logits_scale * image1_features @ image2_features.t()

    return logits, image1_features, image2_features

def txt2txt(model, text):
    text_features = model.encode_text(text)

    text_features = text_features / text_features.norm(dim=1, keepdim=True)

    logits_scale = model.logit_scale.exp()

    logits = logits_scale * text_features @ text_features.t()

    return logits, text_features

def features(csv_data_path, caption_choices, checkpoint = None):
    device = "cuda:0" if torch.cuda.is_available() else "cpu"

    model, preprocess = clip.load("RN101", device=device, jit=False)
    
    if checkpoint:
        checkpoint = torch.load(checkpoint)
        model.load_state_dict(checkpoint['model_state_dict'])

    df = pd.read_csv(csv_data_path)
    list_image_path = df["image_path"].to_list()
    list_text = df["captions"].to_list()

    image = preprocess(Image.open(list_image_path[0])).unsqueeze().to(device)
    text = clip.tokenize(caption_choices, truncate=True).to(device)

    model.eval()
    with torch.no_grad():
        logits, features = img2txt(model, image, text)
        labels = ["image"] + caption_choices

        tsne_plot(features, labels)


cp = "model_checkpoints/model_xxxx.pt"

data_path = "xxxxx.csv"

captions = ["xxxxxx",
            "xxxxxx",
            "xxxxxx"]

z = features(data_path, captions, checkpoint=cp)