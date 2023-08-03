import torch
import clip
from PIL import Image
import pandas as pd
import numpy as np
from sklearn.metrics import confusion_matrix, precision_score, recall_score, classification_report
import seaborn as sns
import matplotlib.pyplot as plt


def clip_metrics(csv_data_path, caption_choices, checkpoint = None, return_frame=False):
    top_pred = []
    res_list = []
    
    device = "cuda:0" if torch.cuda.is_available() else "cpu"

    model, preprocess = clip.load("RN101", device=device)

    if checkpoint:
        checkpoint = torch.load(cp)
        model.load_state_dict(checkpoint['model_state_dict'])

    df = pd.read_csv(csv_data_path)
    list_image_path = df["image_path"]
    list_text = df["captions"]

    model.eval()
    text = clip.tokenize(caption_choices, truncate=True).to(device)
    torch.save(text, "caption_tokens.pt")
    correct_count = 0

    for i in range(len(list_image_path)):
        image = preprocess(Image.open(list_image_path[i])).unsqueeze(0).to(device)

        with torch.no_grad():
            image_logits, text_logits = model(image, text)
            probs = image_logits.softmax(dim=-1).cpu().numpy()

            max_idx = probs[0].argmax(axis=0)
            guess = caption_choices[max_idx]
            top_pred.append(guess)

            if guess == list_text[i]:
                correct_count += 1
            
            res_list.append(probs[0])
            print(round(100*(correct_count/(i+1)),2))

    results = pd.DataFrame(res_list, columns=caption_choices)
    results["correct_caption"] = list_text

    precision = precision_score(list_text, top_pred, average='weighted')
    recall = recall_score(list_text, top_pred, average='weighted')
    conf_mat = confusion_matrix(list_text, top_pred)

    cm_plot = sns.heatmap(conf_mat, annot=True, cmap='Blues', fmt='d', xticklabels=caption_choices, yticklabels=caption_choices)
    cm_plot.set_xlabel('Predicted Values')
    cm_plot.set_ylabel('Actual Values')
    cm_plot.set_title('Confusion Matrix', size=16)
    plt.show()

    if return_frame:
        results.to_csv("xxxxx.csv")

    return precision, recall, conf_mat

cp = "model_checkpoints/model_xxxx.pt"

data_path = "xxxxx.csv"

captions = ["xxxxxx",
            "xxxxxx",
            "xxxxxx"]

precision, recall, confusion_mat = clip_metrics(data_path, captions, checkpoint=cp)