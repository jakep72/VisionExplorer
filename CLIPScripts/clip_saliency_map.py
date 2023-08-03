import numpy as np
import torch
import clip
from PIL import Image
from matplotlib import cm
from skimage.measure import label, regionprops
from skimage.transform import rescale, resize
from skimage.draw import rectangle_perimeter
from copy import deepcopy
from tqdm import tqdm
import cv2


activations = {}
def get_features(name):
  def hook(model, input, output):
    activations[name] = output.detach()
  return hook

def generate_bbox(image, threshold=0.65, connectivity=1, comp_size=50176/1000):
    bar = np.max(image)*threshold
    filtered = (image > bar).astype(int)
    # pdb.set_trace()
    labeled = label(filtered, connectivity=connectivity)
    props = regionprops(labeled)
    if props is None:
      print('Only detected background.')
      return None
    
    return [p for p in props if p.area > comp_size]

def show_bbox_on_img(img, props):
#   pdb.set_trace()
  bbox_img = deepcopy(img)
  for bbox in props:  
    row, col = rectangle_perimeter(start=(bbox.bbox[0]+1, bbox.bbox[1]+1), end=(bbox.bbox[2]-2, bbox.bbox[3]-2))
    bbox_img[row, col, :] = [255, 0, 0]
  return bbox_img

def scale_cam_image(img, target_size=None):
    img = img - np.min(img)
    img = img / (1e-7 + np.max(img))
    if target_size is not None:
      img = resize(img, target_size)

    return img

def weighted_activation(activations, weights, base_score, 
                        cap=True, 
                        shift=True, 
                        softmax=True):
  '''
  mode:
    cap: does not include activations that have lower weights than base_score
    shift: subtract base_score from weights
    softmax: perform softmax on scores, should be required if shift and not cap
  '''

  if cap:
    if not (weights > base_score).any():
      print('None of the weights is larger than base')
      return
    
    indices = (weights > base_score).nonzero()
    activations = activations[indices]
    weights = weights[indices]

  if shift:
    weights = weights - base_score

  if softmax:
    weights = np.exp(weights)/np.sum(np.exp(weights))
  
  weighted = activations * np.expand_dims(weights, axis=(1,2))

  return np.maximum(weighted.sum(axis=0), 0)

def min_max_norm(array):
    lim = [array.min(), array.max()]
    array = (array - lim[0]).float()
    array /= (1.e-10+ (lim[1] - lim[0]))
    # array = torch.clamp(array, min=0, max=1)
    return array

def torch_to_rgba(img):
    img = min_max_norm(img)
    #rgba_im = img.permute(1, 2, 0).cpu()
    rgba_im = img.cpu()
    # if rgba_im.shape[2] == 3:
    #     rgba_im = torch.cat((rgba_im, torch.ones(*rgba_im.shape[:2], 1)), dim=2)
    # assert rgba_im.shape[2] == 4
    return rgba_im

def heatmap(image:torch.Tensor, heatmap: torch.Tensor, size=None, alpha=.6):
    if not size:
        size = image.shape[1]
    # print(heatmap)
    # print(min_max_norm(heatmap))

    img = torch_to_rgba(image).numpy() # [0...1] rgba numpy "image"
    hm = cm.hot(min_max_norm(heatmap).numpy()) # [0...1] rgba numpy "image"

    # print(hm.shape, hm)
 #
    img = (img*255.).astype(np.uint8)
    hm = (hm*255.).astype(np.uint8)

    # img = np.array(numpy_to_image(img,size))
    # hm = np.array(numpy_to_image(hm, size))
    # hm = upscale_pytorch(hm, size)
    # print (hm) 

    return Image.fromarray((alpha * hm + (1-alpha)*img).astype(np.uint8))

def get_cam_weights(input_tensor_,
                    model,
                    text_embedding,
                    activations,
                    device,
                    BATCH_SIZE=32):
  with torch.no_grad():
    upsample = torch.nn.UpsamplingBilinear2d(
        size=input_tensor_.shape[-2:])
    if isinstance(activations, np.ndarray):
        activation_tensor = torch.from_numpy(activations)
    elif isinstance(activations, torch.Tensor):
        activation_tensor = activations
    else:
        print('Invalid activation datatype')
        exit(1)
    
    if device == 'cuda':
        torch.cuda.empty_cache()

    activation_tensor = activation_tensor.to(device)
    input_tensor = input_tensor_.to(device)
    zeros = torch.zeros_like(input_tensor).to(device)
    zeros_embeddings = model.encode_image(zeros)
    zeros_embeddings /= zeros_embeddings.norm(dim=-1, keepdim=True)
    zeros_embeddings = zeros_embeddings.cpu().numpy()
    
    base_scores = (zeros_embeddings @ text_embedding.T).diagonal()    

    upsampled = upsample(activation_tensor)
    # print(upsampled[0,10,:])
    if torch.isnan(upsampled).any():
      print('nan in upsampled before normal')
      return
    
    maxs = upsampled.view(upsampled.size(0), upsampled.size(1),
                          -1).max(dim=-1)[0]
    mins = upsampled.view(upsampled.size(0), upsampled.size(1),
                          -1).min(dim=-1)[0]

    maxs, mins = maxs[:, :, None, None], mins[:, :, None, None]
    upsampled = (upsampled - mins) / (maxs - mins + 1e-7)
    if torch.isnan(input_tensor).any():
      print('nan in input_tensor')
      return

    if torch.isnan(upsampled).any():
      print('nan in upsampled after normal')
      return
    
    input_tensors = torch.einsum('blhw,bchw->bclhw', input_tensor, upsampled)
    if torch.isnan(input_tensors).any():
      print('nan in input_tensors')
      return 
    scores = []
    for index, tensor in enumerate(input_tensors): 
        score = []
        for i in tqdm(range(0, tensor.size(0), BATCH_SIZE)):
          torch.cuda.empty_cache()
          batch = tensor[i: i + BATCH_SIZE, :]
          if torch.isnan(batch).any():
            print('nan in batch')
            return
          img_embeddings = model.encode_image(batch)
          img_embeddings /= img_embeddings.norm(dim=-1, keepdim=True)
          img_embeddings = img_embeddings.cpu().numpy()
          
          if np.isnan(img_embeddings).any():
            print('nan in embeddings')
            return
          outputs = img_embeddings @ text_embedding[index].T
          # print("outputs", outputs.shape)
          score.append(outputs)
        scores.append(np.concatenate(score[:])) 
    
    scores = np.concatenate(scores, axis=0)
    scores = scores.reshape((activations.shape[0], activations.shape[1]))
    return scores, base_scores
  
def saliency_map(imageFile, caption, model, preprocess):
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    
    image_rgb = cv2.imread(str(imageFile))
    # image_rgb = cv2.cvtColor(gray,cv2.COLOR_GRAY2BGR)

    image_raw = Image.open(imageFile)
    #pdb.set_trace()

    # preprocess image:
    image = preprocess(image_raw).unsqueeze(0).to(device)

    model.visual.layer4[2].relu3.register_forward_hook(get_features('act_map'))

    prompt = clip.tokenize([caption]).to(device)
    with torch.no_grad():
        spatial_text_features = model.encode_text(prompt)
        spatial_text_features /= spatial_text_features.norm(dim=-1, keepdim=True)

        image_features = model.encode_image(image)
        activations_copy = activations["act_map"] 
    
    text_embedding = spatial_text_features.cpu().numpy()
    
    spatial_weights, base_scores = get_cam_weights(image, model, text_embedding, activations_copy.float(), device, BATCH_SIZE=32)
    #pdb.set_trace()
    saliency = weighted_activation(activations_copy[0].cpu().numpy(), spatial_weights[0], base_scores[0],
                            cap=True, softmax=True)
    
    # saliency = np.arange(1,50).reshape((7, 7))
    scaled = scale_cam_image(saliency, target_size=(image_rgb.shape[0], image_rgb.shape[1]))

    # cam_img = heatmap(torch.tensor(image_rgb), torch.tensor(scaled))
    
    props = generate_bbox(scaled, threshold=0.8, comp_size=image_rgb.shape[0]*image_rgb.shape[1]/1000)

    bbox_img = show_bbox_on_img(image_rgb, props)
    bbox_img = Image.fromarray(bbox_img.astype('uint8'),'RGB')

    bbox_img.save('saliency.jpg')
