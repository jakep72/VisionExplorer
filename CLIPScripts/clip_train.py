import torch
from torch import nn, optim
from torch.utils.data import Dataset, DataLoader, BatchSampler
import clip
from PIL import Image
import pandas as pd
from pathlib import Path


class image_title_dataset(Dataset):
    def __init__(self, list_image_path, list_text, preprocess):
        self.image_path = list_image_path
        self.title = clip.tokenize(list_text, truncate=True)
        self.preprocess = preprocess

    def __len__(self):
        return len(self.title)
    
    def __getitem__(self, idx):
        image = self.preprocess(Image.open(self.image_path[idx]))
        title = self.title[idx]
        return image, title  

def convert_models_to_fp32(model):
    for p in model.parameters():
        p.data = p.data.float()
        p.grad.data = p.grad.data.float()

def load_data(csv_file, batch_size, preprocess):
    df = pd.read_csv(csv_file)
    list_image_path = df["image_path"].to_list()
    list_text = df["captions"].to_list()

    tokens = list(set(list_text))
    Path("model_checkpoints").mkdir(exist_ok=True)
    torch.save(tokens,"model_checkpoints/tokens.pt")

    dataset = image_title_dataset(list_image_path, list_text, preprocess)
    train_dataloader = DataLoader(dataset, batch_size = batch_size)
    return train_dataloader


def train_clip(csv_file, base_model="RN101", batch_size=16, epochs=10):
    loss_list = []
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load(base_model, device=device, jit=False)
    train_dataloader = load_data(csv_file, batch_size, preprocess)

    if device == "cpu":
        model.float()
    else:
        clip.model.convert_weights(model)

    loss_img = nn.CrossEntropyLoss()
    loss_txt = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-6, betas=(0.9, 0.98), eps=1e-6, weight_decay=0.0001)

    for epoch in range(epochs):
        for batch in train_dataloader:
            optimizer.zero_grad()

            images, texts = batch

            images = images.to(device)
            texts = texts.to(device)

            image_logits, text_logits = model(images, texts)

            ground_truth = torch.arange(len(images), dtype=torch.long, device=device)

            total_loss = (loss_img(image_logits, ground_truth) + loss_txt(text_logits, ground_truth))/2

            total_loss.backward()

            if device == "cpu":
                optimizer.step()
            else : 
                convert_models_to_fp32(model)
                optimizer.step()
                clip.model.convert_weights(model)
        
        loss_list.append(total_loss)
        prev_loss = loss_list[epoch-1]
        current_loss = total_loss
        if len(loss_list) == 1 or current_loss < prev_loss:
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'loss': total_loss,
            }, "model_checkpoints/model_best.pt")

        else:
            print("early stopping.... current loss greater than previous loss.")
            break
        
