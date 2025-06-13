import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image
import numpy as np
from pdf2image import convert_from_path
from sklearn.metrics.pairwise import cosine_similarity
from torchvision.models import resnet50, ResNet50_Weights
import torch.nn as nn


model = torch.hub.load('facebookresearch/swav:main', 'resnet50')
model = nn.Sequential(*list(model.children())[:-1])

# Freeze parameters
for p in model.parameters():
    p.requires_grad = False

model.eval()

transform_pipeline = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])


# Function: Convert PIL image to embedding
def get_embedding(pil_image):
    image = pil_image.convert('RGB')  # Ensure RGB
    img_tensor = transform_pipeline(image).unsqueeze(0)
    with torch.no_grad():
        embedding = model(img_tensor)
        embedding = embedding.view(embedding.size(0), -1).cpu().numpy()
    return embedding  # Shape: (1, 2048)


def load_model():
    model = torch.hub.load('facebookresearch/swav:main', 'resnet50')
    model = nn.Sequential(*list(model.children())[:-1])
    model.eval()
    return model.to(torch.device('cuda' if torch.cuda.is_available() else 'cpu'))

# def load_model():
#     weights = ResNet50_Weights.DEFAULT
#     model = resnet50(weights=weights)
#     model = nn.Sequential(*list(model.children())[:-1])
#     model.eval()
#     return model.to(torch.device('cuda' if torch.cuda.is_available() else 'cpu'))

def compare_passport_pdf_to_reference(pdf_path, ref_path):
    """
    Compare a passport PDF (1 or 2 pages) to a reference image.

    Args:
        pdf_path: Path to the input passport PDF.
        reference_img_path: Path to the reference passport image.
        combine_strategy: 'average', 'front_only', or 'concat'
    """
    # # Load model and device
    model = load_model()
    device = next(model.parameters()).device

    # Get reference embedding
    reference_img_path=ref_path
    ref_embedding = get_embedding(Image.open(reference_img_path))

    combine_strategy="average"

    # Convert PDF pages to PIL images
    pages = convert_from_path(pdf_path, dpi=300, poppler_path=r'C:\poppler-24.08.0\Library\bin')

    if len(pages) == 1 or combine_strategy == "front_only":
        print("Detected 1 page or using front_only strategy.")
        test_embedding = get_embedding(pages[0])

    elif len(pages) >= 2:
        print("Detected 2 pages in PDF.")
        front_embedding = get_embedding(pages[0])
        back_embedding = get_embedding(pages[1])

        if combine_strategy == "average":
            test_embedding = (front_embedding + back_embedding) / 2
        elif combine_strategy == "concat":
            test_embedding = np.concatenate([front_embedding, back_embedding], axis=1)
        else:
            raise ValueError("Invalid combine_strategy. Choose from 'average', 'front_only', 'concat'.")
    else:
        raise ValueError("PDF has no pages.")

    # Compute similarity
    similarity = cosine_similarity(ref_embedding, test_embedding)[0][0]
    print(f"Similarity: {similarity:.4f}")
    return float(similarity)