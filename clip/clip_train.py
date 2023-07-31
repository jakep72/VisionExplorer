import torch
from torch import nn, optim
from torch.utils.data import Dataset, DataLoader, BatchSampler
import clip
from PIL import Image
import pandas as pd
from tqdm import tqdm


class image_title_dataset(Dataset):
    def __init__(self, list_image_path, list_text, preprocess):
        self.image_path = list_image_path
        self.title = clip.tokenize(list_text, truncate=True)
        self.preprocess = preprocess

    def __len__(self):
        return(self.title)
    
    def __getitem(self, idx):
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
    dataset = image_title_dataset(list_image_path, list_text, preprocess)
    train_dataloader = DataLoader(dataset, batch_size = batch_size)
    return train_dataloader


def train_clip(base_model, csv_file, batch_size, epochs, save_freq):

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
        for images, texts in enumerate(train_dataloader):
            optimizer.zero_grad()

            images.to_device()
            texts.to_device()

            image_logits, text_logits = model(images, texts)

            ground_truth = torch.arange(len(images), dtype=torch.long, device=device)

            total_loss = (loss_img(image_logits, ground_truth) + loss_txt(text_logits, ground_truth))/2

            total_loss.backward()

            convert_models_to_fp32(model)
            optimizer.step()
            clip.model.convert_weights(model)

        print(total_loss)

        if epochs % save_freq == 0:
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'loss': total_loss,
            }, "model_checkpoints/model_{}.pt".format(epoch))


